"""
Clinical Documents API - Display extracted data from PDFs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Patient, ClinicalDocument

router = APIRouter()

@router.get("/{patient_id}/documents")
async def get_patient_documents(patient_id: str, db: Session = Depends(get_db)):
    """Get all clinical documents for a patient with full extracted data"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    
    docs = db.query(ClinicalDocument).filter(ClinicalDocument.patient_id == patient.id).all()
    
    result = []
    for doc in docs:
        result.append({
            "id": doc.id,
            "document_type": doc.document_type,
            "filename": doc.filename,
            "admission_date": doc.admission_date,
            "discharge_date": doc.discharge_date,
            "diagnoses": doc.diagnoses,
            "barthel_admission": doc.barthel_admission,
            "barthel_discharge": doc.barthel_discharge,
            "barthel_improvement": doc.barthel_improvement,
            "gmfcs_level": doc.gmfcs_level,
            "macs_level": doc.macs_level,
            "clinical_scores": doc.clinical_scores,
            "therapy_sessions": doc.therapy_sessions,
            "specialist_assessments": doc.specialist_assessments,
            "test_results": doc.test_results,
            "medications": doc.medications,
            "procedures": doc.procedures,
            "progress_dynamics": doc.progress_dynamics,
            "functional_improvement": doc.functional_improvement,
            "recommendations": doc.recommendations,
            "followup_plan": doc.followup_plan
        })
    
    return {
        "patient_id": patient_id,
        "patient_name": patient.name,
        "document_count": len(result),
        "documents": result
    }
