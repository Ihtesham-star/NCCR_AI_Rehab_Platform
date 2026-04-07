"""
Data Import API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os
import shutil

from database.connection import get_db
from database.models import Patient, EMGSession, EMGData, BalanceTest, ClinicalTest, ClinicalDocument
from data_ingestion.emg_parser import parse_noraxon_pdf
from data_ingestion.balance_parser import parse_balance_pdf
from data_ingestion.excel_parser import parse_clinical_excel
from config.settings import settings
from utils.claude_ai import claude_ai
from api.assessments import generate_assessment  # Import assessment generator

router = APIRouter()


@router.post("/emg/pdf")
async def import_emg_pdf(
    file: UploadFile = File(...),
    patient_id: str = None,
    db: Session = Depends(get_db)
):
    """Import EMG data from Noraxon PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Save uploaded file
    file_path = os.path.join(settings.PDF_STORAGE_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse PDF
        parsed_data = parse_noraxon_pdf(file_path)
        
        # Debug: Check what was parsed
        if not parsed_data.get('emg_measurements'):
            return {
                "message": "No EMG measurements found in PDF",
                "warning": "PDF was uploaded but no data could be extracted. Please check the PDF format.",
                "parsed_patient_info": parsed_data.get('patient_info', {}),
                "filename": file.filename
            }
        
        # Find or create patient
        patient_name = parsed_data['patient_info'].get('name')
        
        # If no patient info, create with filename
        if not patient_name and not patient_id:
            patient_id = file.filename.replace('.pdf', '').replace(' ', '_')
            patient_name = patient_id
        
        if patient_id:
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        elif patient_name:
            patient = db.query(Patient).filter(Patient.name == patient_name).first()
        else:
            patient = None
        
        if not patient:
            # Create new patient
            patient = Patient(
                patient_id=patient_id or patient_name.replace(' ', '_'),
                name=patient_name or "Unknown Patient",
                date_of_birth=parsed_data['patient_info'].get('test_date', datetime.utcnow())
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
        
        # Create EMG session
        emg_session = EMGSession(
            patient_id=patient.id,
            session_date=parsed_data['patient_info'].get('test_date', datetime.utcnow()),
            stage=parsed_data['metadata'].get('stage'),
            frequency_hz=2000,
            equipment="Noraxon"
        )
        db.add(emg_session)
        db.commit()
        db.refresh(emg_session)
        
        # Add EMG measurements
        for measurement in parsed_data['emg_measurements']:
            emg_data = EMGData(
                session_id=emg_session.id,
                muscle_name=measurement['muscle_name'],
                side=measurement.get('side'),
                min_value=measurement.get('min_value'),
                max_value=measurement.get('max_value'),
                mean_value=measurement.get('mean_value')
            )
            db.add(emg_data)
        
        db.commit()
        
        return {
            "message": "EMG data imported successfully",
            "patient_id": patient.patient_id,
            "patient_name": patient.name,
            "session_id": emg_session.id,
            "measurements_count": len(parsed_data['emg_measurements'])
        }
    
    except Exception as e:
        return {
            "message": "Error importing EMG data",
            "error": str(e),
            "filename": file.filename,
            "suggestion": "Please check if the PDF is a valid Noraxon EMG report"
        }


@router.post("/balance/pdf")
async def import_balance_pdf(
    file: UploadFile = File(...),
    patient_id: str = None,
    db: Session = Depends(get_db)
):
    """Import balance test data from TecnoBody PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Save uploaded file
    file_path = os.path.join(settings.PDF_STORAGE_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse PDF
        parsed_data = parse_balance_pdf(file_path)
        
        # Find patient
        patient_name = parsed_data['patient_info'].get('name')
        if patient_id:
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        elif patient_name:
            patient = db.query(Patient).filter(Patient.name == patient_name).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient ID or name not found"
            )
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient not found"
            )
        
        # Create balance test record
        balance_metrics = parsed_data['balance_metrics']
        balance_test = BalanceTest(
            patient_id=patient.id,
            test_date=datetime.strptime(parsed_data['patient_info']['test_date'], '%m/%d/%Y')
                if 'test_date' in parsed_data['patient_info'] else datetime.utcnow(),
            test_type=parsed_data['metadata'].get('test_type'),
            foot=parsed_data['metadata'].get('foot'),
            total_stability_index=balance_metrics.get('total_stability_index'),
            trunk_tot_st_dev=balance_metrics.get('trunk_tot_st_dev'),
            sector_percentage=balance_metrics.get('sector_percentage'),
            area_percentage=balance_metrics.get('area_percentage'),
            time_seconds=balance_metrics.get('time_seconds'),
            score=balance_metrics.get('score'),
            trunk_sway_a1=balance_metrics.get('trunk_sway_a1'),
            trunk_sway_a2=balance_metrics.get('trunk_sway_a2'),
            trunk_sway_a3=balance_metrics.get('trunk_sway_a3'),
            trunk_sway_a5=balance_metrics.get('trunk_sway_a5'),
            test_condition=parsed_data['metadata'].get('condition'),
            equipment="TecnoBody"
        )
        db.add(balance_test)
        db.commit()
        
        return {
            "message": "Balance test data imported successfully",
            "patient_id": patient.patient_id,
            "test_id": balance_test.id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing balance data: {str(e)}"
        )


@router.post("/pdf/claude")
async def import_pdf_with_claude(
    file: UploadFile = File(...),
    patient_id: str = None,
    db: Session = Depends(get_db)
):
    """Import ANY PDF using Claude AI (EMG, Balance, or any medical report)"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Save uploaded file
    file_path = os.path.join(settings.PDF_STORAGE_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        print(f"🤖 Using Claude AI to parse PDF: {file.filename}")
        
        # Use Claude AI to parse PDF intelligently
        parsed_data = claude_ai.parse_pdf_intelligently(file_path)
        
        if 'error' in parsed_data:
            return {
                "message": "Claude AI PDF parsing failed",
                "error": parsed_data['error'],
                "filename": file.filename
            }
        
        # Debug: Print what Claude extracted
        print(f"📊 Claude AI extracted data:")
        print(f"   Document type: {parsed_data.get('document_type')}")
        
        # Claude returns data at root level now, not under 'data' key
        if 'data' in parsed_data and parsed_data['data']:
            data = parsed_data['data']
        else:
            # Data is at root level
            data = parsed_data
        
        print(f"   Data keys: {list(data.keys())}")
        if 'patient_info' in data:
            print(f"   Patient info: {data['patient_info']}")
        
        doc_type = parsed_data.get('document_type', 'unknown')
        
        # Extract patient info - Claude returns it in patient_info object
        patient_info = data.get('patient_info', {})
        print(f"🔍 DEBUG patient_info object: {patient_info}")
        
        # Get patient name from multiple possible locations
        patient_name = (
            patient_info.get('name') or 
            data.get('name') or 
            parsed_data.get('patient_name') or 
            data.get('patient_name')
        )
        print(f"🔍 DEBUG patient_name extracted: '{patient_name}'")
        
        # Get patient ID from multiple possible locations
        pid = (
            patient_id or 
            patient_info.get('patient_id') or 
            data.get('patient_id') or 
            parsed_data.get('patient_id')
        )
        
        if pid:
            patient = db.query(Patient).filter(Patient.patient_id == pid).first()
        elif patient_name:
            patient = db.query(Patient).filter(Patient.name == patient_name).first()
        else:
            patient = None
        
        if not patient:
            # Extract patient demographics from Claude AI response
            dob = datetime.utcnow()  # default
            dob_str = (
                patient_info.get('date_of_birth') or 
                data.get('date_of_birth') or 
                parsed_data.get('date_of_birth')
            )
            if dob_str:
                try:
                    dob = datetime.strptime(str(dob_str), '%Y-%m-%d')
                except:
                    try:
                        dob = datetime.strptime(str(dob_str), '%m/%d/%Y')
                    except:
                        try:
                            # Try DD.MM.YYYY format (common in Russian documents)
                            dob = datetime.strptime(str(dob_str), '%d.%m.%Y')
                        except:
                            print(f"⚠️ Could not parse date: {dob_str}")
            
            sex = (
                patient_info.get('sex') or 
                patient_info.get('gender') or 
                data.get('sex') or 
                data.get('gender') or 
                parsed_data.get('sex')
            )
            
            print(f"✅ Creating patient:")
            print(f"   Name: {patient_name}")
            print(f"   DOB: {dob}")
            print(f"   Sex: {sex}")
            print(f"   Raw patient_info: {patient_info}")
            
            patient = Patient(
                patient_id=pid or file.filename.replace('.pdf', ''),
                name=patient_name or "Unknown Patient",
                date_of_birth=dob,
                sex=sex,
                height_cm=patient_info.get('height_cm') or data.get('height_cm'),
                weight_kg=patient_info.get('weight_kg') or data.get('weight_kg'),
                gmfcs_level=patient_info.get('gmfcs_level') or data.get('gmfcs_level')
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
        
        records_created = 0
        
        # Process based on document type
        if doc_type == 'emg' and 'muscles' in data:
            # Create EMG session
            test_date = data.get('test_date')
            if test_date:
                try:
                    session_date = datetime.strptime(str(test_date), '%Y-%m-%d')
                except:
                    session_date = datetime.utcnow()
            else:
                session_date = datetime.utcnow()
                
            emg_session = EMGSession(
                patient_id=patient.id,
                session_date=session_date,
                equipment=data.get('device', 'Unknown'),
                notes="Imported from PDF via Claude AI"
            )
            db.add(emg_session)
            db.commit()
            db.refresh(emg_session)
            
            # Add muscle data
            for muscle in data.get('muscles', []):
                emg_data = EMGData(
                    session_id=emg_session.id,
                    muscle_name=muscle.get('name'),
                    side=muscle.get('side'),
                    mean_value=muscle.get('mean_value') or muscle.get('rms'),
                    max_value=muscle.get('peak_value') or muscle.get('peak'),
                    rms_value=muscle.get('rms') or muscle.get('mean_value'),
                    peak_amplitude=muscle.get('peak') or muscle.get('peak_value')
                )
                db.add(emg_data)
                records_created += 1
            
            db.commit()
            
            return {
                "message": "✅ EMG data imported successfully using Claude AI",
                "patient_name": patient.name,
                "session_id": emg_session.id,
                "muscles_extracted": records_created,
                "filename": file.filename,
                "powered_by": "Claude AI 🤖"
            }
        
        elif doc_type == 'balance':
            # Create balance test
            balance_test = BalanceTest(
                patient_id=patient.id,
                test_date=datetime.utcnow(),
                total_stability_index=data.get('stability_score'),
                trunk_sway_a1=data.get('sway_ap'),
                trunk_sway_a2=data.get('sway_ml'),
                score=data.get('overall_score'),
                equipment=parsed_data.get('device', 'Unknown')
            )
            db.add(balance_test)
            db.commit()
            
            return {
                "message": "Balance data imported",
                "patient_name": patient.name,
                "patient_id": patient.patient_id,
                "test_id": balance_test.id,
                "patients_created": 0,
                "balance_tests_added": 1,
                "filename": file.filename
            }
        
        else:
            # Generic clinical data - Store comprehensive extracted data
            print(f"📋 Storing comprehensive clinical document data...")
            
            # Extract structured data from Claude's response
            patient_info = data.get('patient_info', {})
            diagnoses = data.get('diagnoses', [])
            clinical_scores = data.get('clinical_scores', {})
            therapy_data = data.get('therapy_data', {})
            test_results = data.get('test_results', [])
            medications = data.get('medications', [])
            procedures = data.get('procedures', [])
            specialist_assessments = data.get('specialist_assessments', [])
            progress_info = data.get('progress_dynamics', {})
            recommendations = data.get('recommendations', [])
            
            # Parse dates
            doc_date = datetime.utcnow()
            admission_date = None
            discharge_date = None
            
            if patient_info.get('admission_date'):
                try:
                    admission_date = datetime.strptime(str(patient_info['admission_date']), '%Y-%m-%d')
                except:
                    pass
            
            if patient_info.get('discharge_date'):
                try:
                    discharge_date = datetime.strptime(str(patient_info['discharge_date']), '%Y-%m-%d')
                except:
                    pass
            
            # Extract Barthel scores
            barthel_admission = clinical_scores.get('barthel_admission') or clinical_scores.get('barthel_index_admission')
            barthel_discharge = clinical_scores.get('barthel_discharge') or clinical_scores.get('barthel_index_discharge')
            barthel_improvement = None
            
            if barthel_admission and barthel_discharge:
                try:
                    barthel_improvement = ((barthel_discharge - barthel_admission) / barthel_admission) * 100
                except:
                    pass
            
            # Create clinical document record
            clinical_doc = ClinicalDocument(
                patient_id=patient.id,
                document_type=doc_type,
                document_date=doc_date,
                admission_date=admission_date,
                discharge_date=discharge_date,
                filename=file.filename,
                diagnoses=diagnoses,
                barthel_admission=barthel_admission,
                barthel_discharge=barthel_discharge,
                barthel_improvement=barthel_improvement,
                gmfcs_level=clinical_scores.get('gmfcs_level'),
                macs_level=clinical_scores.get('macs_level'),
                clinical_scores=clinical_scores,
                therapy_sessions=therapy_data,
                specialist_assessments=specialist_assessments,
                test_results=test_results,
                medications=medications,
                procedures=procedures,
                progress_dynamics=progress_info.get('status', 'stable'),
                functional_improvement=progress_info.get('description'),
                recommendations=recommendations,
                followup_plan=data.get('followup_plan'),
                raw_extracted_data=parsed_data
            )
            db.add(clinical_doc)
            db.commit()
            db.refresh(clinical_doc)
            
            print(f"✅ Clinical document saved (ID: {clinical_doc.id})")
            
            # Auto-generate assessment
            # print(f"🤖 Auto-generating assessment for patient {patient.patient_id}...")
            # try:
            #     assessment_result = await generate_assessment(
            #         patient_id=patient.id,
            #         db=db,
            #         clinical_doc_id=clinical_doc.id  # Pass clinical document ID for context
            #     )
            #     print(f"✅ Assessment generated (ID: {assessment_result.get('assessment_id')})")
            # except Exception as e:
            #     print(f"⚠️ Assessment generation failed: {str(e)}")
            #     assessment_result = {"error": str(e)}
            
            return {
                "message": "✅ PDF processed successfully using Claude AI",
                "patient_name": patient.name,
                "patient_id": patient.patient_id,
                "document_type": doc_type,
                "clinical_document_id": clinical_doc.id,
                "data_summary": {
                    "diagnoses_count": len(diagnoses),
                    "barthel_admission": barthel_admission,
                    "barthel_discharge": barthel_discharge,
                    "barthel_improvement_pct": round(barthel_improvement, 1) if barthel_improvement else None,
                    "therapy_sessions": therapy_data,
                    "medications_count": len(medications),
                    "specialist_assessments_count": len(specialist_assessments)
                },
                "assessment": assessment_result,
                "filename": file.filename,
                "powered_by": "Claude AI 🤖"
            }
    
    except Exception as e:
        return {
            "message": "Error importing PDF with Claude AI",
            "error": str(e),
            "filename": file.filename
        }


@router.post("/clinical/excel")
async def import_clinical_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import clinical data from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    # Save uploaded file
    file_path = os.path.join(settings.EXCEL_STORAGE_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse Excel
        parsed_data = parse_clinical_excel(file_path)
        
        patients_created = 0
        tests_created = 0
        sessions_created = 0
        
        # Import patients from parsed data
        for patient_data in parsed_data.get('patients', []):
            existing = db.query(Patient).filter(
                Patient.patient_id == patient_data['patient_id']
            ).first()
            
            if not existing:
                patient = Patient(**patient_data)
                db.add(patient)
                patients_created += 1
                print(f"Creating patient: {patient_data['name']}")
        
        db.commit()
        
        # Import EMG sessions (for stage-based files)
        for session_data in parsed_data.get('emg_sessions', []):
            patient_name = session_data.get('patient_name', 'Unknown')
            
            # Find or create patient
            patient = db.query(Patient).filter(Patient.name == patient_name).first()
            
            if not patient:
                # Create patient if not exists
                patient = Patient(
                    patient_id=patient_name.replace(' ', '_'),
                    name=patient_name,
                    date_of_birth=session_data.get('test_date', datetime.utcnow())
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
                patients_created += 1
                print(f"Created patient from EMG session: {patient_name}")
            
            # Create EMG session
            emg_session = EMGSession(
                patient_id=patient.id,
                session_date=session_data.get('test_date', datetime.utcnow()),
                stage=session_data.get('stage', 'Unknown'),
                frequency_hz=session_data.get('frequency_hz', 2000),
                equipment="Excel Import"
            )
            db.add(emg_session)
            sessions_created += 1
            print(f"Created EMG session for {patient_name}")
        
        db.commit()
        
        # Import clinical tests
        for test_data in parsed_data.get('clinical_tests', []):
            patient = db.query(Patient).filter(
                Patient.patient_id == test_data['patient_id']
            ).first()
            
            if patient:
                clinical_test = ClinicalTest(
                    patient_id=patient.id,
                    test_date=test_data.get('test_date', datetime.utcnow()),
                    test_type=test_data.get('test_type', 'clinical_assessment'),
                    distance_6mwt_meters=test_data.get('distance_6mwt_meters'),
                    time_10mwt_seconds=test_data.get('time_10mwt_seconds'),
                    tug_time_seconds=test_data.get('tug_time_seconds'),
                    gmfm_score=test_data.get('gmfm_score'),
                    who_qol_score=test_data.get('who_qol_score'),
                    omni_exertion_scale=test_data.get('omni_exertion_scale'),
                    modified_ashworth_scale=test_data.get('modified_ashworth_scale')
                )
                db.add(clinical_test)
                tests_created += 1
        
        db.commit()
        
        return {
            "message": "Clinical data imported successfully",
            "patients_created": patients_created,
            "emg_sessions_created": sessions_created,
            "tests_created": tests_created,
            "total_patients_in_file": len(parsed_data.get('patients', [])),
            "total_emg_sessions": len(parsed_data.get('emg_sessions', [])),
            "filename": file.filename
        }
    
    except Exception as e:
        return {
            "message": "Error importing clinical data",
            "error": str(e),
            "filename": file.filename,
            "suggestion": "Please check if the Excel file has the correct format"
        }


@router.post("/clinical/excel/claude")
async def import_clinical_excel_with_claude(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import clinical data using Claude AI (intelligent parsing)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    # Save uploaded file
    file_path = os.path.join(settings.EXCEL_STORAGE_PATH, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Use Claude AI to parse Excel intelligently
        print("🤖 Using Claude AI for intelligent Excel parsing...")
        parsed_data = claude_ai.parse_excel_intelligently(file_path)
        
        if 'error' in parsed_data:
            return {
                "message": "Claude AI parsing failed",
                "error": parsed_data['error'],
                "filename": file.filename
            }
        
        patients_created = 0
        tests_created = 0
        
        # Import patients from Claude AI results
        for patient_data in parsed_data.get('patients', []):
            try:
                existing = db.query(Patient).filter(
                    Patient.patient_id == patient_data['patient_id']
                ).first()
                
                if not existing:
                    # Calculate date of birth from age if provided
                    dob = datetime.utcnow()
                    if patient_data.get('age'):
                        dob = datetime(datetime.utcnow().year - int(patient_data['age']), 1, 1)
                    
                    patient = Patient(
                        patient_id=patient_data['patient_id'],
                        name=patient_data['name'],
                        date_of_birth=dob,
                        height_cm=patient_data.get('height_cm'),
                        weight_kg=patient_data.get('weight_kg'),
                        gmfcs_level=patient_data.get('gmfcs_level'),
                        sex=patient_data.get('sex')
                    )
                    db.add(patient)
                    db.commit()
                    db.refresh(patient)
                    patients_created += 1
                    print(f"Created patient: {patient_data['name']} ({patient_data['patient_id']})")
                else:
                    patient = existing
                    print(f"Found existing patient: {patient.name} ({patient.patient_id})")
                
                # Add clinical tests if available (for both new and existing patients)
                clinical_tests = patient_data.get('clinical_tests', {})
                if any(clinical_tests.values()):
                    test = ClinicalTest(
                        patient_id=patient.id,
                        test_date=datetime.utcnow(),
                        test_type='clinical_assessment',
                        distance_6mwt_meters=clinical_tests.get('6mwt_distance_meters'),
                        time_10mwt_seconds=clinical_tests.get('10mwt_time_seconds'),
                        tug_time_seconds=clinical_tests.get('tug_time_seconds'),
                        gmfm_score=clinical_tests.get('gmfm_score'),
                        who_qol_score=clinical_tests.get('who_qol_score'),
                        omni_exertion_scale=clinical_tests.get('omni_exertion_scale'),
                        modified_ashworth_scale=clinical_tests.get('modified_ashworth_scale')
                    )
                    db.add(test)
                    tests_created += 1
                    print(f"Added clinical test for patient {patient.patient_id}")
                    
                    # Also create a balance test record if Berg Balance Scale is present
                    berg_score = clinical_tests.get('berg_balance_scale')
                    if berg_score:
                        from database.models import BalanceTest
                        balance_test = BalanceTest(
                            patient_id=patient.id,
                            test_date=datetime.utcnow(),
                            test_type='berg_balance',
                            score=berg_score
                        )
                        db.add(balance_test)
                        print(f"Added balance test for patient {patient.patient_id}")
                
                # Add EMG session if EMG data is present
                emg_data = patient_data.get('emg_data', {})
                if any(emg_data.values()):
                    from database.models import EMGSession
                    emg_session = EMGSession(
                        patient_id=patient.id,
                        session_date=datetime.utcnow(),
                        equipment=emg_data.get('device', 'Unknown'),
                        notes=f"Muscle measurements from import"
                    )
                    db.add(emg_session)
                    print(f"Added EMG session for patient {patient.patient_id}")
            except Exception as e:
                print(f"Error creating patient {patient_data.get('name')}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            "message": "Clinical data imported successfully",
            "patients_created": patients_created,
            "tests_created": tests_created,
            "total_patients_found": len(parsed_data.get('patients', [])),
            "filename": file.filename
        }
    
    except Exception as e:
        return {
            "message": "Error importing with Claude AI",
            "error": str(e),
            "filename": file.filename
        }

