"""
Rehabilitation Recommendations API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.connection import get_db
from database.models import Patient, RehabRecommendation, Assessment
from recommendations.rehab_engine import RehabRecommendationEngine

router = APIRouter()


class RecommendationResponse(BaseModel):
    id: int
    patient_id: int
    recommendation_date: datetime
    primary_focus: Optional[str]
    therapy_type: Optional[str]
    frequency_per_week: Optional[int]
    session_duration_minutes: Optional[int]
    status: str
    
    class Config:
        from_attributes = True


@router.post("/{patient_id}/generate")
async def generate_recommendation(patient_id: str, db: Session = Depends(get_db)):
    """Generate rehabilitation recommendations for a patient"""
    # Get patient
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Get latest assessment
    if not patient.assessments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient {patient_id} has no assessments. Generate an assessment first."
        )
    
    latest_assessment = max(patient.assessments, key=lambda x: x.assessment_date)
    
    # Initialize recommendation engine
    engine = RehabRecommendationEngine()
    
    # Extract analysis from assessment
    detailed_results = latest_assessment.detailed_results or {}
    motor_analysis = detailed_results.get('motor_analysis', {})
    balance_analysis = detailed_results.get('balance_analysis', {})
    disability_assessment = detailed_results.get('disability_assessment', {})
    
    # Generate recommendations
    recommendations = engine.generate_recommendations(
        disability_assessment,
        motor_analysis,
        balance_analysis,
        patient.gmfcs_level
    )
    
    # Create recommendation record
    rehab_rec = RehabRecommendation(
        patient_id=patient.id,
        assessment_id=latest_assessment.id,
        recommendation_date=datetime.utcnow(),
        primary_focus=', '.join(recommendations['primary_focus']),
        therapy_type=', '.join(recommendations['therapy_types']),
        recommended_exercises=recommendations['recommended_exercises'],
        target_muscles=recommendations['target_muscles'],
        frequency_per_week=recommendations['protocol_details'].get('frequency_per_week'),
        session_duration_minutes=recommendations['protocol_details'].get('session_duration_minutes'),
        program_duration_weeks=recommendations['protocol_details'].get('program_duration_weeks'),
        intensity_level=recommendations['protocol_details'].get('intensity_level'),
        expected_improvements=recommendations['expected_improvements'],
        monitoring_parameters=recommendations['monitoring_parameters'],
        status='active'
    )
    
    db.add(rehab_rec)
    db.commit()
    db.refresh(rehab_rec)
    
    return {
        "recommendation_id": rehab_rec.id,
        "patient_id": patient_id,
        "recommendation_date": rehab_rec.recommendation_date,
        "summary": {
            "primary_focus": recommendations['primary_focus'],
            "therapy_types": recommendations['therapy_types'],
            "protocol": recommendations['protocol_details']
        },
        "details": recommendations
    }


@router.get("/{patient_id}", response_model=List[RecommendationResponse])
async def get_patient_recommendations(patient_id: str, db: Session = Depends(get_db)):
    """Get all recommendations for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    return patient.recommendations


@router.get("/{patient_id}/latest")
async def get_latest_recommendation(patient_id: str, db: Session = Depends(get_db)):
    """Get the latest active recommendation for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    if not patient.recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recommendations found for patient {patient_id}"
        )
    
    latest = max(patient.recommendations, key=lambda x: x.recommendation_date)
    return latest


@router.put("/{recommendation_id}/status")
async def update_recommendation_status(
    recommendation_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update recommendation status"""
    recommendation = db.query(RehabRecommendation).filter(
        RehabRecommendation.id == recommendation_id
    ).first()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found"
        )
    
    if status not in ['active', 'completed', 'modified']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'active', 'completed', or 'modified'"
        )
    
    recommendation.status = status
    recommendation.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Recommendation status updated to {status}"}
