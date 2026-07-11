"""
Patient Management API Endpoints - FIXED VERSION
The issue was the endpoint path order!
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from pydantic import BaseModel, field_validator

from database.connection import get_db
from database.models import Patient, ClinicalTest, EMGSession, BalanceTest

router = APIRouter()


# Pydantic schemas for request/response
class PatientCreate(BaseModel):
    patient_id: str
    name: str
    date_of_birth: datetime
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    gmfcs_level: Optional[int] = None
    diagnosis: Optional[str] = None

    @field_validator('gmfcs_level')
    @classmethod
    def validate_gmfcs_level(cls, v):
        if v is not None and not (v >= 1 and v <= 5):
            raise ValueError('GMFCS level must be between 1 and 5')
        return v


class PatientResponse(BaseModel):
    id: int
    patient_id: str
    name: str
    date_of_birth: datetime
    sex: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    gmfcs_level: Optional[int]
    diagnosis: Optional[str]
    @field_validator('gmfcs_level')
    @classmethod
    def validate_gmfcs_level(cls, v):
        if v is not None and not (v >= 1 and v <= 5):
            raise ValueError('GMFCS level must be between 1 and 5')
        return v

    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    gmfcs_level: Optional[int] = None
    diagnosis: Optional[str] = None


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    # Check if patient already exists
    existing = db.query(Patient).filter(Patient.patient_id == patient.patient_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID {patient.patient_id} already exists"
        )
    
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    gmfcs_level: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get list of patients with optional filtering"""
    query = db.query(Patient)
    
    if gmfcs_level is not None:
        query = query.filter(Patient.gmfcs_level == gmfcs_level)
    
    patients = query.offset(skip).limit(limit).all()
    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient by ID"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    update_data = patient_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Delete a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    db.delete(patient)
    db.commit()
    return None


@router.get("/{patient_id}/summary")
async def get_patient_summary(patient_id: str, db: Session = Depends(get_db)):
    """Get comprehensive patient summary with optimized query"""
    # ⚡ OPTIMIZED: Load all relationships in ONE query
    patient = db.query(Patient).options(
        selectinload(Patient.clinical_tests),
        selectinload(Patient.emg_sessions),
        selectinload(Patient.balance_tests),
        selectinload(Patient.assessments),
        selectinload(Patient.recommendations)
    ).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Get counts (already loaded in memory, no DB hit)
    clinical_tests_count = len(patient.clinical_tests)
    emg_sessions_count = len(patient.emg_sessions)
    balance_tests_count = len(patient.balance_tests)
    assessments_count = len(patient.assessments)
    recommendations_count = len(patient.recommendations)
    
    # Get latest assessment (already in memory)
    latest_assessment = None
    if patient.assessments:
        latest_assessment = max(patient.assessments, key=lambda x: x.assessment_date)
    
    return {
        "patient": PatientResponse.from_orm(patient),
        "data_summary": {
            "clinical_tests": clinical_tests_count,
            "emg_sessions": emg_sessions_count,
            "balance_tests": balance_tests_count,
            "assessments": assessments_count,
            "recommendations": recommendations_count
        },
        "latest_assessment": {
            "date": latest_assessment.assessment_date if latest_assessment else None,
            "disability_severity": latest_assessment.disability_severity if latest_assessment else None,
            "motor_function_score": latest_assessment.motor_function_score if latest_assessment else None,
            "balance_score": latest_assessment.balance_score if latest_assessment else None
        } if latest_assessment else None
    }


# ✅ FIXED: Endpoint path to match frontend call
@router.get("/clinical-tests/{patient_id}")
async def get_patient_clinical_tests(patient_id: str, db: Session = Depends(get_db)):
    """Get clinical tests for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    tests = db.query(ClinicalTest).filter(ClinicalTest.patient_id == patient.id).order_by(ClinicalTest.test_date.desc()).all()
    
    return [
        {
            "test_date": t.test_date,
            "distance_6mwt_meters": t.distance_6mwt_meters,
            "time_10mwt_seconds": t.time_10mwt_seconds,
            "tug_time_seconds": t.tug_time_seconds,
            "gmfm_score": t.gmfm_score,
            "who_qol_score": t.who_qol_score,
            "omni_exertion_scale": t.omni_exertion_scale,
            "modified_ashworth_scale": t.modified_ashworth_scale
        }
        for t in tests
    ]