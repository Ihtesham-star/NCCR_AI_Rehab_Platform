"""
Assessment API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

from database.connection import get_db
from database.models import Patient, Assessment, EMGData, BalanceTest, ClinicalTest, ClinicalDocument
from analytics.motor_assessment import MotorFunctionAnalyzer, BalanceAnalyzer, DisabilityQuantifier, CognitiveAssessor
from utils.claude_ai import claude_ai

router = APIRouter()


class AssessmentResponse(BaseModel):
    id: int
    patient_id: int
    assessment_date: datetime
    motor_function_score: Optional[float]
    balance_score: Optional[float]
    cognitive_function_score: Optional[float]
    disability_severity: Optional[str]
    disability_index: Optional[float]
    fall_risk_level: Optional[str]
    model_version: Optional[str] = None
    confidence_score: Optional[float] = None
    detailed_results: Optional[dict] = None
    
    class Config:
        from_attributes = True


@router.post("/{patient_id}/generate")
async def generate_assessment(
    patient_id: str, 
    language: str = "en", 
    db: Session = Depends(get_db),
    clinical_doc_id: int = None
):
    """Generate a new AI-based assessment for a patient"""
    # Get patient
    if isinstance(patient_id, str):
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    else:
        # If called internally with integer ID
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Check if we have clinical document data (from intelligent PDF parsing)
    clinical_doc = None
    if not clinical_doc_id:
        # Try to find the latest clinical document for this patient
        clinical_doc = db.query(ClinicalDocument).filter(
            ClinicalDocument.patient_id == patient.id
        ).order_by(ClinicalDocument.id.desc()).first()
    else:
        clinical_doc = db.query(ClinicalDocument).filter(ClinicalDocument.id == clinical_doc_id).first()
    
    # INTELLIGENT DECISION: Use whatever data is available
    # Priority 1: Barthel-based (rehabilitation discharge)
    # Priority 2: Claude AI analysis of ANY clinical data
    # Priority 3: Traditional EMG/balance metrics
    
    if clinical_doc and clinical_doc.barthel_discharge:
        print(f"📊 Using Barthel-based assessment from clinical document...")
        
        # Calculate disability based on Barthel Index
        barthel_discharge = clinical_doc.barthel_discharge or 0
        barthel_admission = clinical_doc.barthel_admission or barthel_discharge
        
        # Barthel Index interpretation:
        # 100: Independent
        # 91-99: Minimal dependence
        # 61-90: Mild dependence
        # 41-60: Moderate dependence
        # 21-40: Severe dependence
        # 0-20: Total dependence
        
        if barthel_discharge >= 91:
            disability_severity = "minimal"
            disability_index = 95.0
        elif barthel_discharge >= 61:
            disability_severity = "mild"
            disability_index = 75.0
        elif barthel_discharge >= 41:
            disability_severity = "moderate"
            disability_index = 50.0
        elif barthel_discharge >= 21:
            disability_severity = "severe"
            disability_index = 30.0
        else:
            disability_severity = "profound"
            disability_index = 10.0
        
        # Calculate improvement percentage
        barthel_improvement_pct = 0.0
        if barthel_admission > 0:
            barthel_improvement_pct = ((barthel_discharge - barthel_admission) / barthel_admission) * 100
        
        # Get therapy intensity as activity indicator
        therapy_sessions = clinical_doc.therapy_sessions or {}
        total_sessions = sum(therapy_sessions.values()) if isinstance(therapy_sessions, dict) else 0
        
        # Motor function score based on Barthel + therapy
        motor_function_score = barthel_discharge  # Use Barthel as primary motor indicator
        balance_score = barthel_discharge * 0.9  # Barthel correlates with balance
        
        # Cognitive score (if available from clinical scores)
        clinical_scores = clinical_doc.clinical_scores or {}
        cognitive_score = clinical_scores.get('cognitive_score', 70.0)
        
        # Fall risk based on Barthel
        if barthel_discharge >= 80:
            fall_risk = "low"
        elif barthel_discharge >= 50:
            fall_risk = "medium"
        else:
            fall_risk = "high"
        
        # Create assessment
        assessment = Assessment(
            patient_id=patient.id,
            assessment_date=clinical_doc.discharge_date or datetime.utcnow(),
            motor_function_score=motor_function_score,
            muscle_coordination_score=motor_function_score * 0.95,
            gait_quality_score=motor_function_score * 0.9,
            balance_score=balance_score,
            cognitive_function_score=cognitive_score,
            disability_severity=disability_severity,
            disability_index=disability_index,
            fall_risk_level=fall_risk,
            model_version="Barthel-Based 2.0",
            confidence_score=0.90,
            detailed_results={
                'barthel_admission': barthel_admission,
                'barthel_discharge': barthel_discharge,
                'barthel_improvement_pct': round(barthel_improvement_pct, 1),
                'therapy_sessions': therapy_sessions,
                'total_therapy_sessions': total_sessions,
                'diagnoses': clinical_doc.diagnoses,
                'medications_count': len(clinical_doc.medications) if clinical_doc.medications else 0,
                'progress_dynamics': clinical_doc.progress_dynamics,
                'functional_improvement': clinical_doc.functional_improvement
            }
        )
        
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        return {
            "assessment_id": assessment.id,
            "patient_id": patient.patient_id,
            "assessment_date": assessment.assessment_date,
            "method": "barthel_based",
            "summary": {
                "disability_severity": assessment.disability_severity,
                "disability_index": assessment.disability_index,
                "motor_function_score": assessment.motor_function_score,
                "balance_score": assessment.balance_score,
                "cognitive_function_score": assessment.cognitive_function_score,
                "fall_risk_level": assessment.fall_risk_level,
                "barthel_improvement_pct": round(barthel_improvement_pct, 1)
            },
            "detailed_results": assessment.detailed_results
        }
    
    # INTELLIGENT: If we have clinical document but NO Barthel → Use Claude AI to analyze
    elif clinical_doc and clinical_doc.raw_extracted_data:
        print(f"🤖 Using Claude AI to analyze clinical document data...")
        
        # Prepare comprehensive data for Claude
        doc_data = clinical_doc.raw_extracted_data
        
        # Determine language instruction
        language_instruction = "Respond in RUSSIAN language. All text, medical terminology, clinical insights, and recommendations MUST be in Russian." if language == "ru" else ""
        claude_prompt = f"""{language_instruction}
        You are an expert medical AI analyzing clinical data to assess a patient's condition and generate rehabilitation recommendations.


PATIENT DATA:
- Age: {(datetime.utcnow() - patient.date_of_birth).days // 365 if patient.date_of_birth else 'Unknown'} years
- Sex: {patient.sex or 'Unknown'}
- GMFCS Level: {patient.gmfcs_level or doc_data.get('clinical_scores', {}).get('gmfcs_level') or 'Not specified'}

CLINICAL DOCUMENT:
Document Type: {doc_data.get('document_type')}

Diagnoses: {json.dumps(doc_data.get('diagnoses'), ensure_ascii=False)}

Medications ({len(doc_data.get('medications', []))}): {', '.join(doc_data.get('medications', [])[:10])}

Lab Results: {json.dumps(doc_data.get('test_results', {}).get('lab_results'), ensure_ascii=False)}

Clinical Tests: {json.dumps(doc_data.get('test_results', {}).get('clinical_tests'), ensure_ascii=False)}

Imaging: {json.dumps(doc_data.get('test_results', {}).get('imaging'), ensure_ascii=False)}

Specialist Assessments: {json.dumps(doc_data.get('specialist_assessments'), ensure_ascii=False)}

Progress Dynamics: {json.dumps(doc_data.get('progress_dynamics'), ensure_ascii=False)}

Therapy Sessions: {json.dumps(doc_data.get('therapy_data'), ensure_ascii=False)}

YOUR TASK:
Based on ALL this clinical data, provide a comprehensive assessment:

Return JSON:
{{
  "disability_severity": "minimal/mild/moderate/severe/profound",
  "disability_index": 0-100 (100=independent, 0=total dependence),
  "motor_function_score": 0-100,
  "balance_score": 0-100,
  "cognitive_function_score": 0-100,
  "fall_risk_level": "low/medium/high",
  "confidence_score": 0.0-1.0,
  "clinical_insights": "detailed analysis of patient condition",
  "key_concerns": ["list", "of", "concerns"],
  "rehabilitation_recommendations": ["specific", "recommendations"],
  "expected_outcomes": "realistic prognosis and expectations",
  "follow_up_priority": "high/medium/low"
}}

IMPORTANT: Base your assessment on the ACTUAL clinical data provided. Be realistic and evidence-based.
"""

        try:
            response = claude_ai.client.messages.create(
                model=claude_ai.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": claude_prompt}]
            )
            
            response_text = response.content[0].text
            json_str = claude_ai._extract_json(response_text)
            claude_result = json.loads(json_str)
            
            print(f"✅ Claude AI assessment generated")
            print(f"   Severity: {claude_result.get('disability_severity')}")
            print(f"   Disability Index: {claude_result.get('disability_index')}")
            
            # Create assessment from Claude's analysis
            assessment = Assessment(
                patient_id=patient.id,
                assessment_date=datetime.utcnow(),
                motor_function_score=claude_result.get('motor_function_score'),
                muscle_coordination_score=claude_result.get('motor_function_score', 0) * 0.95,
                gait_quality_score=claude_result.get('motor_function_score', 0) * 0.9,
                balance_score=claude_result.get('balance_score'),
                cognitive_function_score=claude_result.get('cognitive_function_score'),
                disability_severity=claude_result.get('disability_severity'),
                disability_index=claude_result.get('disability_index'),
                fall_risk_level=claude_result.get('fall_risk_level'),
                model_version="Claude AI Clinical Document Analysis",
                confidence_score=claude_result.get('confidence_score', 0.85),
                detailed_results={
                    'method': 'claude_ai_clinical_document',
                    'clinical_insights': claude_result.get('clinical_insights'),
                    'key_concerns': claude_result.get('key_concerns'),
                    'rehabilitation_recommendations': claude_result.get('rehabilitation_recommendations'),
                    'expected_outcomes': claude_result.get('expected_outcomes'),
                    'follow_up_priority': claude_result.get('follow_up_priority'),
                    'data_sources': {
                        'diagnoses_count': len(doc_data.get('diagnoses', {}).get('icd_codes', [])),
                        'medications_count': len(doc_data.get('medications', [])),
                        'lab_results_available': bool(doc_data.get('test_results', {}).get('lab_results')),
                        'imaging_available': bool(doc_data.get('test_results', {}).get('imaging')),
                        'specialist_assessments_count': len(doc_data.get('specialist_assessments', {}))
                    }
                }
            )
            
            db.add(assessment)
            db.commit()
            db.refresh(assessment)
            
            return {
                "assessment_id": assessment.id,
                "patient_id": patient.patient_id,
                "assessment_date": assessment.assessment_date,
                "method": "claude_ai_clinical_analysis",
                "summary": {
                    "disability_severity": assessment.disability_severity,
                    "disability_index": assessment.disability_index,
                    "motor_function_score": assessment.motor_function_score,
                    "balance_score": assessment.balance_score,
                    "cognitive_function_score": assessment.cognitive_function_score,
                    "fall_risk_level": assessment.fall_risk_level
                },
                "clinical_insights": claude_result.get('clinical_insights'),
                "key_concerns": claude_result.get('key_concerns'),
                "recommendations": claude_result.get('rehabilitation_recommendations'),
                "expected_outcomes": claude_result.get('expected_outcomes'),
                "powered_by": "Claude AI 🤖"
            }
            
        except Exception as e:
            print(f"❌ Claude AI assessment failed: {str(e)}")
            # Fall through to traditional assessment
    
    # Traditional EMG/balance assessment (fallback)
    # Gather all patient data
    emg_sessions = patient.emg_sessions
    balance_tests = patient.balance_tests
    clinical_tests = patient.clinical_tests
    
    if not emg_sessions and not balance_tests and not clinical_tests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient has no assessment data (EMG, balance, or clinical tests)"
        )
    
    # Initialize analyzers
    motor_analyzer = MotorFunctionAnalyzer()
    balance_analyzer = BalanceAnalyzer()
    disability_quantifier = DisabilityQuantifier()
    cognitive_assessor = CognitiveAssessor()
    
    # Analyze EMG data
    emg_analysis = {}
    if emg_sessions:
        latest_session = max(emg_sessions, key=lambda x: x.session_date)
        emg_measurements = [
            {
                'muscle_name': data.muscle_name,
                'side': data.side,
                'mean_value': data.mean_value,
                'max_value': data.max_value,
                'min_value': data.min_value
            }
            for data in latest_session.emg_data
        ]
        emg_analysis = motor_analyzer.analyze_emg_data(emg_measurements)
    
    # Analyze balance data
    balance_analysis = {}
    if balance_tests:
        latest_balance = max(balance_tests, key=lambda x: x.test_date)
        balance_metrics = {
            'total_stability_index': latest_balance.total_stability_index,
            'time_seconds': latest_balance.time_seconds,
            'trunk_sway_a1': latest_balance.trunk_sway_a1,
            'trunk_sway_a2': latest_balance.trunk_sway_a2,
            'trunk_sway_a3': latest_balance.trunk_sway_a3,
            'trunk_sway_a5': latest_balance.trunk_sway_a5
        }
        balance_analysis = balance_analyzer.analyze_balance_data(balance_metrics)
    
    # Analyze clinical tests
    clinical_analysis = {}
    if clinical_tests:
        latest_clinical = max(clinical_tests, key=lambda x: x.test_date)
        clinical_data = {
            'distance_6mwt_meters': latest_clinical.distance_6mwt_meters,
            'time_10mwt_seconds': latest_clinical.time_10mwt_seconds,
            'tug_time_seconds': latest_clinical.tug_time_seconds
        }
        clinical_analysis = motor_analyzer.analyze_clinical_tests(clinical_data)
    
    # Calculate disability index
    disability_assessment = disability_quantifier.calculate_disability_index(
        emg_analysis,
        balance_analysis,
        clinical_analysis,
        patient.gmfcs_level
    )
    
    # Assess cognitive indicators
    cognitive_assessment = cognitive_assessor.assess_cognitive_indicators(
        emg_measurements if emg_sessions else [],
        balance_metrics if balance_tests else {},
        clinical_data if clinical_tests else {}
    )
    
    # Create assessment record
    assessment = Assessment(
        patient_id=patient.id,
        assessment_date=datetime.utcnow(),
        motor_function_score=emg_analysis.get('muscle_coordination_score'),
        muscle_coordination_score=emg_analysis.get('muscle_coordination_score'),
        gait_quality_score=clinical_analysis.get('mobility_score'),
        balance_score=balance_analysis.get('balance_score'),
        cognitive_function_score=cognitive_assessment.get('cognitive_function_score'),
        attention_score=cognitive_assessment.get('attention_score'),
        disability_severity=disability_assessment.get('disability_severity'),
        disability_index=disability_assessment.get('disability_index'),
        muscle_imbalance_detected=emg_analysis.get('muscle_imbalance_detected', False),
        asymmetry_percentage=emg_analysis.get('muscle_asymmetry'),
        fall_risk_level=balance_analysis.get('fall_risk_level'),
        model_version="1.0",
        confidence_score=disability_assessment.get('confidence_score'),
        detailed_results={
            'motor_analysis': emg_analysis,
            'balance_analysis': balance_analysis,
            'clinical_analysis': clinical_analysis,
            'disability_assessment': disability_assessment,
            'cognitive_assessment': cognitive_assessment
        }
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "assessment_id": assessment.id,
        "patient_id": patient_id,
        "assessment_date": assessment.assessment_date,
        "summary": {
            "disability_severity": assessment.disability_severity,
            "disability_index": assessment.disability_index,
            "motor_function_score": assessment.motor_function_score,
            "balance_score": assessment.balance_score,
            "cognitive_function_score": assessment.cognitive_function_score,
            "fall_risk_level": assessment.fall_risk_level
        },
        "detailed_results": assessment.detailed_results
    }


@router.post("/{patient_id}/generate/claude")
async def generate_assessment_with_claude(patient_id: str, language: str = "en", db: Session = Depends(get_db)):
    """Generate AI assessment using Claude AI for intelligent medical analysis"""
    # Get patient
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Gather all patient data
    emg_sessions = patient.emg_sessions
    balance_tests = patient.balance_tests
    clinical_tests = patient.clinical_tests
    
    if not emg_sessions and not balance_tests and not clinical_tests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient has no assessment data (EMG, balance, or clinical tests)"
        )
    
    print(f"🤖 Generating Claude AI assessment for patient: {patient.name} (Language: {language})")
    
    # Prepare patient data
    patient_data = {
        'patient_id': patient.patient_id,
        'name': patient.name,
        'age': (datetime.utcnow() - patient.date_of_birth).days // 365 if patient.date_of_birth else None,
        'height_cm': patient.height_cm,
        'weight_kg': patient.weight_kg,
        'gmfcs_level': patient.gmfcs_level
    }
    
    # Prepare EMG data
    emg_data = []
    if emg_sessions:
        latest_session = max(emg_sessions, key=lambda x: x.session_date)
        emg_data = [
            {
                'muscle_name': data.muscle_name,
                'side': data.side,
                'rms_value': data.rms_value,
                'peak_amplitude': data.peak_amplitude
            }
            for data in latest_session.emg_data
        ]
    
    # Prepare balance data
    balance_data = {}
    if balance_tests:
        latest_balance = max(balance_tests, key=lambda x: x.test_date)
        balance_data = {
            'total_stability_index': latest_balance.total_stability_index,
            'trunk_sway_ap': latest_balance.trunk_sway_a1,
            'trunk_sway_ml': latest_balance.trunk_sway_a2,
            'time_seconds': latest_balance.time_seconds,
            'score': latest_balance.score
        }
    
    # Prepare clinical data
    clinical_data = {}
    if clinical_tests:
        latest_clinical = max(clinical_tests, key=lambda x: x.test_date)
        clinical_data = {
            'distance_6mwt_meters': latest_clinical.distance_6mwt_meters,
            'time_10mwt_seconds': latest_clinical.time_10mwt_seconds,
            'tug_time_seconds': latest_clinical.tug_time_seconds,
            'gmfm_score': latest_clinical.gmfm_score,
            'who_qol_score': latest_clinical.who_qol_score
        }
    
    # Generate Claude AI assessment with language support
    claude_assessment = claude_ai.generate_intelligent_assessment(
        patient_data, emg_data, balance_data, clinical_data, language=language
    )
    
    if 'error' in claude_assessment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Claude AI assessment failed: {claude_assessment['error']}"
        )
    
    # Create assessment record with Claude AI results
    assessment = Assessment(
        patient_id=patient.id,
        assessment_date=datetime.utcnow(),
        motor_function_score=claude_assessment.get('motor_function_score'),
        muscle_coordination_score=claude_assessment.get('muscle_coordination_score'),
        gait_quality_score=claude_assessment.get('gait_quality_score'),
        balance_score=claude_assessment.get('balance_score'),
        cognitive_function_score=claude_assessment.get('cognitive_score'),
        disability_severity=claude_assessment.get('disability_severity'),
        disability_index=claude_assessment.get('disability_index'),
        fall_risk_level=claude_assessment.get('fall_risk_level'),
        model_version="Claude AI 1.0",
        confidence_score=claude_assessment.get('confidence_score', 0.95),
        detailed_results={
            'recommendations': claude_assessment.get('recommendations', []),
            'clinical_insights': claude_assessment.get('clinical_insights', ''),
            'expected_outcomes': claude_assessment.get('expected_outcomes', ''),
            'muscle_coordination_score': claude_assessment.get('muscle_coordination_score'),
            'gait_quality_score': claude_assessment.get('gait_quality_score'),
            'cognitive_score': claude_assessment.get('cognitive_score')
        }
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "assessment_id": assessment.id,
        "patient_id": patient_id,
        "assessment_date": assessment.assessment_date,
        "powered_by": "Claude AI",
        "summary": {
            "disability_severity": assessment.disability_severity,
            "disability_index": assessment.disability_index,
            "motor_function_score": assessment.motor_function_score,
            "balance_score": assessment.balance_score,
            "fall_risk_level": assessment.fall_risk_level,
            "muscle_coordination_score": assessment.muscle_coordination_score,
            "gait_quality_score": assessment.gait_quality_score,
            "cognitive_score": assessment.cognitive_function_score,
            "confidence_score": assessment.confidence_score
        },
        "clinical_insights": claude_assessment.get('clinical_insights'),
        "recommendations": claude_assessment.get('recommendations'),
        "expected_outcomes": claude_assessment.get('expected_outcomes')
    }


@router.get("/{patient_id}", response_model=List[AssessmentResponse])
async def get_patient_assessments(patient_id: str, db: Session = Depends(get_db)):
    """Get all assessments for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    return patient.assessments


@router.get("/{patient_id}/latest")
async def get_latest_assessment(patient_id: str, db: Session = Depends(get_db)):
    """Get the latest assessment for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    if not patient.assessments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessments found for patient {patient_id}"
        )
    
    latest = max(patient.assessments, key=lambda x: x.assessment_date)
    return latest


@router.get("/{patient_id}/progress")
async def get_assessment_progress(patient_id: str, db: Session = Depends(get_db)):
    """Get assessment progress over time"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    assessments = sorted(patient.assessments, key=lambda x: x.assessment_date)
    
    progress_data = {
        "patient_id": patient_id,
        "total_assessments": len(assessments),
        "timeline": [
            {
                "date": a.assessment_date,
                "motor_function_score": a.motor_function_score,
                "balance_score": a.balance_score,
                "cognitive_function_score": a.cognitive_function_score,
                "disability_index": a.disability_index,
                "disability_severity": a.disability_severity
            }
            for a in assessments
        ]
    }
    
    # Calculate improvement
    if len(assessments) >= 2:
        first = assessments[0]
        latest = assessments[-1]
        
        progress_data["improvement"] = {
            "motor_function": latest.motor_function_score - first.motor_function_score
                if first.motor_function_score and latest.motor_function_score else None,
            "balance": latest.balance_score - first.balance_score
                if first.balance_score and latest.balance_score else None,
            "disability_index": latest.disability_index - first.disability_index
                if first.disability_index and latest.disability_index else None
        }
    
    return progress_data


@router.delete("/{patient_id}")
async def delete_patient_assessments(patient_id: str, db: Session = Depends(get_db)):
    """Delete all assessments for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Delete all assessments
    deleted_count = db.query(Assessment).filter(Assessment.patient_id == patient.id).delete()
    db.commit()
    
    return {
        "message": f"Deleted {deleted_count} assessment(s) for patient {patient_id}",
        "deleted_count": deleted_count
    }
