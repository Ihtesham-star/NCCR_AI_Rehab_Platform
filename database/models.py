"""
SQLAlchemy Database Models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Patient(Base):
    """Patient/Child information"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    sex = Column(String(10))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    gmfcs_level = Column(Integer)  # GMFCS classification (1-5)
    diagnosis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    clinical_tests = relationship("ClinicalTest", back_populates="patient", cascade="all, delete-orphan")
    emg_sessions = relationship("EMGSession", back_populates="patient", cascade="all, delete-orphan")
    balance_tests = relationship("BalanceTest", back_populates="patient", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="patient", cascade="all, delete-orphan")
    recommendations = relationship("RehabRecommendation", back_populates="patient", cascade="all, delete-orphan")


class ClinicalTest(Base):
    """Clinical examination results (6MWT, 10MWT, TUG, etc.)"""
    __tablename__ = "clinical_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    test_date = Column(DateTime, nullable=False)
    test_type = Column(String(50), nullable=False)  # '6MWT', '10MWT', 'TUG', 'BALANCE'
    
    # 6MWT fields
    distance_6mwt_meters = Column(Float)
    time_6mwt_seconds = Column(Float)
    
    # 10MWT fields
    distance_10mwt_meters = Column(Float)
    time_10mwt_seconds = Column(Float)
    
    # TUG test
    tug_time_seconds = Column(Float)
    
    # Additional metrics
    gmfm_score = Column(Float)  # Gross Motor Function Measure
    who_qol_score = Column(Float)  # WHO Quality of Life
    omni_exertion_scale = Column(Integer)
    modified_ashworth_scale = Column(Integer)  # Spasticity assessment (0-4)
    
    # Other measurements
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_tests")


class EMGSession(Base):
    """EMG recording session"""
    __tablename__ = "emg_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    session_date = Column(DateTime, nullable=False)
    stage = Column(String(50))  # 'Stage1_upper', 'Stage1_lower', etc.
    frequency_hz = Column(Integer, default=2000)
    equipment = Column(String(100), default="Noraxon")
    
    # Session metadata
    duration_seconds = Column(Float)
    quality_score = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="emg_sessions")
    emg_data = relationship("EMGData", back_populates="session", cascade="all, delete-orphan")


class EMGData(Base):
    """Individual EMG measurements per muscle"""
    __tablename__ = "emg_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("emg_sessions.id"), nullable=False)
    
    # Muscle identification
    muscle_name = Column(String(100), nullable=False)  # 'BICEPS_FEM_LT', 'GLUT_MED_RT', etc.
    side = Column(String(10))  # 'LT' (left) or 'RT' (right)
    
    # EMG metrics
    min_value = Column(Float)
    max_value = Column(Float)
    mean_value = Column(Float)
    rms_value = Column(Float)  # Root Mean Square
    
    # Force measurements
    force_lt_n = Column(Float)  # Force Left in Newtons
    force_rt_n = Column(Float)  # Force Right in Newtons
    
    # Activity level
    activity_number = Column(Integer)
    activity_name = Column(String(100))
    
    # Raw data (optional, for detailed analysis)
    raw_data = Column(JSON)  # Store time-series if needed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("EMGSession", back_populates="emg_data")


class BalanceTest(Base):
    """Balance and stability test results"""
    __tablename__ = "balance_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    test_date = Column(DateTime, nullable=False)
    test_type = Column(String(50))  # 'single_foot_balance', 'both_feet', 'proprioceptive'
    foot = Column(String(10))  # 'left', 'right', 'both'
    
    # Balance metrics
    total_stability_index = Column(Float)
    trunk_tot_st_dev = Column(Float)
    sector_percentage = Column(Float)
    area_percentage = Column(Float)
    time_seconds = Column(Float)
    score = Column(Float)
    
    # Trunk sway measurements
    trunk_sway_a1 = Column(Float)
    trunk_sway_a2 = Column(Float)
    trunk_sway_a3 = Column(Float)
    trunk_sway_a5 = Column(Float)
    
    # Equipment
    equipment = Column(String(100), default="TecnoBody")
    
    # Additional data
    test_condition = Column(String(50))  # 'dynamic', 'static', 'clockwise', 'anti-clockwise'
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="balance_tests")


class Assessment(Base):
    """AI-generated motor and cognitive assessment"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    assessment_date = Column(DateTime, nullable=False)
    
    # Motor function scores (0-100)
    motor_function_score = Column(Float)
    muscle_coordination_score = Column(Float)
    gait_quality_score = Column(Float)
    balance_score = Column(Float)
    
    # Cognitive indicators (0-100)
    cognitive_function_score = Column(Float)
    attention_score = Column(Float)
    
    # Disability level quantification
    disability_severity = Column(String(50))  # 'mild', 'moderate', 'severe', 'profound'
    disability_index = Column(Float)  # 0-100 composite score
    
    # Detailed analysis
    muscle_imbalance_detected = Column(Boolean, default=False)
    asymmetry_percentage = Column(Float)
    fall_risk_level = Column(String(20))  # 'low', 'medium', 'high'
    
    # AI model metadata
    model_version = Column(String(50))
    confidence_score = Column(Float)
    
    # Detailed results as JSON
    detailed_results = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="assessments")


class RehabRecommendation(Base):
    """Rehabilitation recommendations"""
    __tablename__ = "rehab_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    recommendation_date = Column(DateTime, nullable=False)
    
    # Recommendation details
    primary_focus = Column(String(100))  # 'balance', 'strength', 'coordination', 'gait'
    therapy_type = Column(String(100))  # 'physical_therapy', 'occupational_therapy', etc.
    
    # Specific exercises/interventions
    recommended_exercises = Column(JSON)  # List of exercises with parameters
    target_muscles = Column(JSON)  # List of muscles to focus on
    
    # Protocol details
    frequency_per_week = Column(Integer)
    session_duration_minutes = Column(Integer)
    program_duration_weeks = Column(Integer)
    intensity_level = Column(String(20))  # 'low', 'medium', 'high'
    
    # Progress tracking
    expected_improvements = Column(JSON)
    monitoring_parameters = Column(JSON)
    
    # Status
    status = Column(String(20), default='active')  # 'active', 'completed', 'modified'
    clinician_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="recommendations")


class ClinicalDocument(Base):
    """Comprehensive clinical documents data extracted by Claude AI"""
    __tablename__ = "clinical_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Document metadata
    document_type = Column(String(100))  # 'rehabilitation_discharge', 'admission', 'progress_note', etc.
    document_date = Column(DateTime)
    admission_date = Column(DateTime)
    discharge_date = Column(DateTime)
    filename = Column(String(255))
    
    # Diagnoses and conditions
    diagnoses = Column(JSON)  # [{"code": "G80.0", "name": "Spastic cerebral palsy", "type": "main"}]
    
    # Clinical scores and assessments
    barthel_admission = Column(Integer)  # Barthel Index at admission
    barthel_discharge = Column(Integer)  # Barthel Index at discharge
    barthel_improvement = Column(Float)  # Improvement percentage
    gmfcs_level = Column(Integer)  # GMFCS classification
    macs_level = Column(Integer)  # MACS classification
    clinical_scores = Column(JSON)  # Other assessment scores
    
    # Therapy data
    therapy_sessions = Column(JSON)  # {"occupational": 60, "physical": 45, "speech": 30, "music": 10}
    specialist_assessments = Column(JSON)  # [{"specialist": "neurologist", "assessment": "..."}]
    
    # Test results
    test_results = Column(JSON)  # Lab work, imaging, other tests
    
    # Medications and procedures
    medications = Column(JSON)  # [{"name": "...", "dose": "...", "frequency": "..."}]
    procedures = Column(JSON)  # [{"procedure": "...", "date": "..."}]
    
    # Progress and outcomes
    progress_dynamics = Column(String(50))  # 'improvement', 'stable', 'decline'
    functional_improvement = Column(Text)  # Description of improvements
    
    # Recommendations
    recommendations = Column(JSON)  # [{"category": "...", "recommendation": "..."}]
    followup_plan = Column(Text)
    
    # Raw extracted data (full JSON from Claude)
    raw_extracted_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient")


class User(Base):
    """Clinician/Staff user accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(200))
    role = Column(String(50), default='clinician')  # 'admin', 'clinician', 'therapist'
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
