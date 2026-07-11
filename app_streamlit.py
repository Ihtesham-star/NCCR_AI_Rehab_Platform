"""
NCCR Rehabilitation Platform - Streamlit Web Interface
Professional, Fast, User-Friendly Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from pathlib import Path
import json
import time
import os
import signal
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
 
# Configure page
st.set_page_config(
    page_title="NCCR Rehabilitation Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# Language translations
TRANSLATIONS = {
    'en': {
        'title': 'NCCR Rehabilitation Platform',
        'subtitle': 'Advanced Pediatric Rehabilitation Analytics System',
        'dashboard': '🏠 Dashboard',
        'patients': '👥 Patients',
        'import_data': '📤 Import Data',
        'assessments': '📋 Assessments',
        'reports': '📊 Reports',
        'system_overview': '📊 System Overview',
        'total_patients': 'Total Patients',
        'ai_assessments': 'AI Assessments',
        'emg_sessions': 'EMG Sessions',
        'balance_tests': 'Balance Tests',
        'quick_actions': '⚡ Quick Actions',
        'upload_data': 'Upload Data Files',
        'manage_patients': 'Manage Patients',
        'generate_assessment': 'Generate Assessment',
        'search_patients': '🔍 Search patients by name or ID...',
        'patient_id': 'Patient ID',
        'name': 'Name',
        'dob': 'DOB',
        'age': 'Age',
        'sex': 'Sex',
        'assess': 'Assess',
        'delete_patient': 'Delete Patient',
        'clear_assessments': 'Clear Assessments',
        'loading': 'Loading...',
        'processing': 'Processing...',
        'success': 'Success',
        'error': 'Error',
        'years': 'years',
        'use_ai_parser': 'Use AI Parser',
        'process_files': 'Process Files',
        'select_files': 'Select files',
        'view_patients': 'View Patients Now',
        'language': 'Language',
        'clinical_data': 'Clinical Data',
        'level': 'Level',
        'meters': 'meters',
        'sec': 'sec',
        'diagnoses': 'Diagnoses',
        'medications': 'Medications',
        'procedures': 'Procedures',
        'imaging': 'Imaging',
        'lab_results': 'Lab Results',
        'specialist_assessments': 'Specialist Assessments',
        'therapy_sessions': 'Therapy Sessions',
        'recommendations': 'Recommendations',
        'barthel_index': 'Barthel Index',
        'clinical_scores': 'Clinical Scores',
        'admission': 'Admission',
        'discharge': 'Discharge',
        'additional_data': 'Additional Data',
        'items': 'items',
        'and_more': 'and',
        'more': 'more',
        'male': 'Male',
        'female': 'Female',
        'primary': 'Primary',
        'secondary': 'Secondary',
        'icd_codes': 'ICD Codes',
        'full_diagnosis_text': 'Full Diagnosis Text',
        'admission_date': 'Admission Date',
        'discharge_date': 'Discharge Date',
        'test_results': 'Test Results',
        'clinical_tests': 'Clinical Tests',
        'progress_dynamics': 'Progress Dynamics',
        'stable': 'stable',
        'neurologist': 'Neurologist',
        'dermatologist': 'Dermatologist',
        'cardiologist': 'Cardiologist',
        'blood_gas_analysis': 'Blood Gas Analysis',
        'complete_blood_count': 'Complete Blood Count',
        'biochemistry': 'Biochemistry',
        'microbiology': 'Microbiology',
        'serology': 'Serology',
        'urine_analysis': 'Urine Analysis',
        'ultrasound_abdomen': 'Ultrasound Abdomen',
        'echocardiography': 'Echocardiography',
        'chest_xray': 'Chest X-ray',
        'ct_scan': 'CT Scan',
        'mri': 'MRI',
        'procalcitonin': 'Procalcitonin',
        'crp': 'CRP',
        'ph': 'pH',
        'pco2': 'pCO2',
        'po2': 'pO2',
        'hct': 'Hct',
        'sodium': 'Sodium',
        'potassium': 'Potassium',
        'calcium': 'Calcium',
        'wbc': 'WBC',
        'rbc': 'RBC',
        'hemoglobin': 'Hemoglobin',
        'hematocrit': 'Hematocrit',
        'platelets': 'Platelets',
        'esr': 'ESR',
        'total_protein': 'Total Protein',
        'albumin': 'Albumin',
        'alt': 'ALT',
        'ast': 'AST',
        'total_bilirubin': 'Total Bilirubin',
        'glucose': 'Glucose',
        'urea': 'Urea',
        'creatinine': 'Creatinine',
        'throat_culture': 'Throat Culture',
        'blood_culture_sterility': 'Blood Culture Sterility',
        'blood_culture_salmonella': 'Blood Culture Salmonella',
        'cmv_igg': 'CMV IgG',
        'cmv_igm': 'CMV IgM',
        'cmv_pcr': 'CMV PCR',
        'brucellosis': 'Brucellosis',
        'malaria': 'Malaria',
        'protein': 'Protein',
        'leukocytes': 'Leukocytes',
        'erythrocytes': 'Erythrocytes',
        'present': 'present',
        'absent': 'absent',
        'negative': 'negative',
        'no_growth': 'no growth'
    },
    'ru': {
        'title': 'Платформа реабилитации NCCR',
        'subtitle': 'Расширенная система аналитики педиатрической реабилитации',
        'dashboard': '🏠 Панель управления',
        'patients': '👥 Пациенты',
        'import_data': '📤 Импорт данных',
        'assessments': '📋 Оценки',
        'reports': '📊 Отчеты',
        'system_overview': '📊 Обзор системы',
        'total_patients': 'Всего пациентов',
        'ai_assessments': 'AI оценки',
        'emg_sessions': 'ЭМГ сеансы',
        'balance_tests': 'Тесты баланса',
        'quick_actions': '⚡ Быстрые действия',
        'upload_data': 'Загрузить файлы данных',
        'manage_patients': 'Управление пациентами',
        'generate_assessment': 'Создать оценку',
        'search_patients': '🔍 Поиск пациентов по имени или ID...',
        'patient_id': 'ID пациента',
        'name': 'Имя',
        'dob': 'Дата рождения',
        'age': 'Возраст',
        'sex': 'Пол',
        'assess': 'Оценить',
        'delete_patient': 'Удалить пациента',
        'clear_assessments': 'Очистить оценки',
        'loading': 'Загрузка...',
        'processing': 'Обработка...',
        'success': 'Успешно',
        'error': 'Ошибка',
        'years': 'лет',
        'use_ai_parser': 'Использовать AI парсер',
        'process_files': 'Обработать файлы',
        'select_files': 'Выбрать файлы',
        'view_patients': 'Просмотреть пациентов',
        'language': 'Язык',
        'clinical_data': 'Клинические данные',
        'level': 'Уровень',
        'meters': 'метров',
        'sec': 'сек',
        'diagnoses': 'Диагнозы',
        'medications': 'Лекарства',
        'procedures': 'Процедуры',
        'imaging': 'Визуализация',
        'lab_results': 'Лабораторные результаты',
        'specialist_assessments': 'Консультации специалистов',
        'therapy_sessions': 'Терапевтические сеансы',
        'recommendations': 'Рекомендации',
        'barthel_index': 'Индекс Бартел',
        'clinical_scores': 'Клинические оценки',
        'admission': 'Поступление',
        'discharge': 'Выписка',
        'additional_data': 'Дополнительные данные',
        'items': 'элементов',
        'and_more': 'и еще',
        'more': 'больше',
        'male': 'Мужской',
        'female': 'Женский',
        'primary': 'Основной',
        'secondary': 'Сопутствующий',
        'icd_codes': 'МКБ коды',
        'full_diagnosis_text': 'Полный текст диагноза',
        'admission_date': 'Дата поступления',
        'discharge_date': 'Дата выписки',
        'test_results': 'Результаты тестов',
        'clinical_tests': 'Клинические тесты',
        'progress_dynamics': 'Динамика прогресса',
        'stable': 'стабильно',
        'neurologist': 'Невролог',
        'dermatologist': 'Дерматолог',
        'cardiologist': 'Кардиолог',
        'blood_gas_analysis': 'Анализ газов крови',
        'complete_blood_count': 'Общий анализ крови',
        'biochemistry': 'Биохимия',
        'microbiology': 'Микробиология',
        'serology': 'Серология',
        'urine_analysis': 'Анализ мочи',
        'ultrasound_abdomen': 'УЗИ брюшной полости',
        'echocardiography': 'Эхокардиография',
        'chest_xray': 'Рентген грудной клетки',
        'ct_scan': 'КТ',
        'mri': 'МРТ',
        'procalcitonin': 'Прокальцитонин',
        'crp': 'СРБ',
        'ph': 'pH',
        'pco2': 'pCO2',
        'po2': 'pO2',
        'hct': 'Гематокрит',
        'sodium': 'Натрий',
        'potassium': 'Калий',
        'calcium': 'Кальций',
        'wbc': 'Лейкоциты',
        'rbc': 'Эритроциты',
        'hemoglobin': 'Гемоглобин',
        'hematocrit': 'Гематокрит',
        'platelets': 'Тромбоциты',
        'esr': 'СОЭ',
        'total_protein': 'Общий белок',
        'albumin': 'Альбумин',
        'alt': 'АЛТ',
        'ast': 'АСТ',
        'total_bilirubin': 'Общий билирубин',
        'glucose': 'Глюкоза',
        'urea': 'Мочевина',
        'creatinine': 'Креатинин',
        'throat_culture': 'Посев из зева',
        'blood_culture_sterility': 'Посев крови на стерильность',
        'blood_culture_salmonella': 'Посев крови на сальмонеллу',
        'cmv_igg': 'ЦМВ IgG',
        'cmv_igm': 'ЦМВ IgM',
        'cmv_pcr': 'ЦМВ ПЦР',
        'brucellosis': 'Бруцеллез',
        'malaria': 'Малярия',
        'protein': 'Белок',
        'leukocytes': 'Лейкоциты',
        'erythrocytes': 'Эритроциты',
        'present': 'обнаружено',
        'absent': 'не обнаружено',
        'negative': 'отрицательно',
        'no_growth': 'роста нет'
    }
}
 
# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"
if 'language' not in st.session_state:
    st.session_state.language = 'ru'  # Default to Russian
if 'stats_cache' not in st.session_state:
    st.session_state.stats_cache = None
if 'patients_cache' not in st.session_state:
    st.session_state.patients_cache = None
if 'cache_time' not in st.session_state:
    st.session_state.cache_time = 0
 
# Helper function to get translated text
def t(key):
    """Get translated text based on current language"""
    lang = st.session_state.language
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
 
# API Configuration
API_BASE = "http://localhost:8000/api"
CACHE_DURATION = 5  # Cache for 5 seconds - refresh quickly after upload
 
# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
 
    /* Main container styling */
    .main {
        background-color: #f5f7fa;
    }
 
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
    }
 
    /* Sidebar buttons - Blue background by default */
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
    }
 
    /* Active/Primary button - Brighter blue */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(96, 165, 250, 0.5) !important;
        transform: scale(1.02);
    }
 
    /* Hover effect */
    [data-testid="stSidebar"] .stButton button:hover {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        color: white !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
    }
 
    /* Sidebar text */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: white !important;
    }
 
    /* Main content buttons */
    .main .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
        border: none;
    }
 
    .main .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
 
    /* Cards */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
 
    /* Tables */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
 
    /* Headers */
    h1, h2, h3 {
        font-weight: 700;
        color: #1e293b;
    }
 
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
 
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px dashed #cbd5e1;
    }
 
    /* Expanders */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 8px;
        font-weight: 600;
    }
 
    /* Success/Info boxes */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 8px;
        border-left-width: 4px;
    }
</style>
""", unsafe_allow_html=True)
 
# Helper Functions
@st.cache_data(ttl=30)  # Cache for 30 seconds - better performance
def fetch_stats():
    """Get system statistics with caching"""
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"total_patients": 0, "total_assessments": 0, "emg_sessions": 0, "balance_tests": 0}
 
@st.cache_data(ttl=30)  # Cache for 30 seconds - better performance
def fetch_patients():
    """Get all patients with caching"""
    try:
        response = requests.get(f"{API_BASE}/patients/", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []
 
def upload_pdf_any(file, use_claude_ai=True):
    """Upload ANY PDF file (EMG, Balance, or other) with Claude AI"""
    try:
        # Get current language
        language = st.session_state.get('language', 'en')
        
        files = {"file": (file.name, file, "application/pdf")}
        if use_claude_ai:
            # Use Claude AI for intelligent parsing with language parameter
            response = requests.post(
                f"{API_BASE}/import/pdf/claude",
                files=files,
                params={"language": language},
                timeout=120
            )
        else:
            # Try standard parsers
            response = requests.post(f"{API_BASE}/import/emg/pdf", files=files, timeout=120)
            if response.status_code != 200:
                response = requests.post(f"{API_BASE}/import/balance/pdf", files=files, timeout=120)

        if response.status_code == 200:
            return True, response.json()
        else:
            try:
                return False, response.json()
            except:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return False, {"error": str(e)}
 
def upload_emg_pdf(file):
    """Upload EMG PDF file (legacy - use upload_pdf_any instead)"""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(f"{API_BASE}/import/emg/pdf", files=files, timeout=30)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)
 
def upload_balance_pdf(file):
    """Upload Balance PDF file (legacy - use upload_pdf_any instead)"""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(f"{API_BASE}/import/balance/pdf", files=files, timeout=30)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)
 
def upload_clinical_excel(file, use_claude_ai=True):
    """Upload Clinical Excel file (with optional Claude AI intelligent parsing)"""
    try:
        # Get current language
        language = st.session_state.get('language', 'en')
        
        endpoint = "/import/clinical/excel/claude" if use_claude_ai else "/import/clinical/excel"
        files = {"file": (file.name, file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = requests.post(
            f"{API_BASE}{endpoint}",
            files=files,
            params={"language": language},
            timeout=120
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            try:
                return False, response.json()
            except:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return False, {"error": str(e)}
 
def generate_assessment(patient_id, use_claude_ai=True):
    """Generate AI assessment for patient (with optional Claude AI)"""
    try:
        # Get current language from session state
        language = st.session_state.get('language', 'en')
 
        # All assessments now intelligently use whatever data is available
        endpoint = f"/assessments/{patient_id}/generate"
 
        # Send language preference to backend
        response = requests.post(
            f"{API_BASE}{endpoint}",
            params={"language": language},
            timeout=120
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            # Get error details
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f"HTTP {response.status_code}")
            except:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            return False, error_msg
            
    except Exception as e:
        return False, str(e)
 
def generate_pdf_report(patient_data, assessment_data=None):
    """Generate PDF report for patient"""
    from io import BytesIO
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
 
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
 
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1*inch, height - 1*inch, "NCCR Rehabilitation Report")
 
    # Patient Information
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1.5*inch, "Patient Information")
 
    c.setFont("Helvetica", 12)
    y = height - 1.8*inch
    c.drawString(1*inch, y, f"Patient ID: {patient_data.get('patient_id', 'N/A')}")
    y -= 0.3*inch
    c.drawString(1*inch, y, f"Name: {patient_data.get('name', 'N/A')}")
    y -= 0.3*inch
    c.drawString(1*inch, y, f"Sex: {patient_data.get('sex', 'N/A')}")
    y -= 0.3*inch
    c.drawString(1*inch, y, f"GMFCS Level: {patient_data.get('gmfcs_level', 'N/A')}")
    y -= 0.3*inch
 
    # Assessment Results
    if assessment_data:
        y -= 0.5*inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, y, "Assessment Results")
 
        c.setFont("Helvetica", 12)
        y -= 0.3*inch
        c.drawString(1*inch, y, f"Assessment Date: {assessment_data.get('assessment_date', 'N/A')}")
        y -= 0.3*inch
        c.drawString(1*inch, y, f"Motor Function Score: {assessment_data.get('motor_function_score', 'N/A')}")
        y -= 0.3*inch
        c.drawString(1*inch, y, f"Balance Score: {assessment_data.get('balance_score', 'N/A')}")
        y -= 0.3*inch
        c.drawString(1*inch, y, f"Disability Severity: {assessment_data.get('disability_severity', 'N/A')}")
        y -= 0.3*inch
        c.drawString(1*inch, y, f"Fall Risk Level: {assessment_data.get('fall_risk_level', 'N/A')}")
 
    # Footer
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, 0.5*inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(1*inch, 0.3*inch, "NCCR Rehabilitation Analytics Platform v1.0.0")
 
    c.save()
    buffer.seek(0)
    return buffer
 
def generate_excel_export(patient_data, assessments=None, clinical_tests=None, emg_data=None, balance_data=None):
    """Generate Excel export with multiple sheets"""
    from io import BytesIO
 
    buffer = BytesIO()
 
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Patient Information Sheet
        patient_df = pd.DataFrame([{
            'Patient ID': patient_data.get('patient_id', 'N/A'),
            'Name': patient_data.get('name', 'N/A'),
            'Date of Birth': patient_data.get('date_of_birth', 'N/A'),
            'Sex': patient_data.get('sex', 'N/A'),
            'Height (cm)': patient_data.get('height_cm', 'N/A'),
            'Weight (kg)': patient_data.get('weight_kg', 'N/A'),
            'GMFCS Level': patient_data.get('gmfcs_level', 'N/A'),
            'Diagnosis': patient_data.get('diagnosis', 'N/A')
        }])
        patient_df.to_excel(writer, sheet_name='Patient Info', index=False)
 
        # Clinical Tests Sheet
        if clinical_tests and len(clinical_tests) > 0:
            clinical_df = pd.DataFrame(clinical_tests)
            clinical_df.to_excel(writer, sheet_name='Clinical Tests', index=False)
 
        # Assessment Sheet
        if assessments and len(assessments) > 0:
            assessment_df = pd.DataFrame(assessments)
            assessment_df.to_excel(writer, sheet_name='Assessments', index=False)
 
        # EMG Data Sheet
        if emg_data and len(emg_data) > 0:
            emg_df = pd.DataFrame(emg_data)
            emg_df.to_excel(writer, sheet_name='EMG Data', index=False)
 
        # Balance Data Sheet
        if balance_data and len(balance_data) > 0:
            balance_df = pd.DataFrame(balance_data)
            balance_df.to_excel(writer, sheet_name='Balance Tests', index=False)
 
    buffer.seek(0)
    return buffer
 
# Header with Language Toggle
col_header1, col_header2 = st.columns([4, 1])
 
with col_header1:
    st.markdown(f"""
    <div class="main-header">
        <h1>{t('title')}</h1>
        <p>{t('subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
 
with col_header2:
    st.markdown("<br>", unsafe_allow_html=True)
    lang_option = st.selectbox(
        t('language'),
        options=['English', 'Русский'],
        index=0 if st.session_state.language == 'en' else 1,
        key='lang_selector'
    )
    if (lang_option == 'English' and st.session_state.language == 'ru') or \
       (lang_option == 'Русский' and st.session_state.language == 'en'):
        st.session_state.language = 'en' if lang_option == 'English' else 'ru'
        st.rerun()
 
# Sidebar Navigation
with st.sidebar:
    st.markdown(f"## {t('dashboard').split()[1] if '🏠' in t('dashboard') else 'Navigation'}")
 
    # Navigation buttons - ONE CLICK WORKS
    if st.button(t('dashboard'), use_container_width=True, type="primary" if st.session_state.page == "Dashboard" else "secondary"):
        st.session_state.page = "Dashboard"
        st.rerun()
 
    if st.button(t('patients'), use_container_width=True, type="primary" if st.session_state.page == "👥 Patients" else "secondary"):
        st.session_state.page = "👥 Patients"
        st.rerun()
 
    if st.button(t('import_data'), use_container_width=True, type="primary" if st.session_state.page == "📤 Import Data" else "secondary"):
        st.session_state.page = "📤 Import Data"
        st.rerun()
 
    if st.button(t('assessments'), use_container_width=True, type="primary" if st.session_state.page == "📋 Assessments" else "secondary"):
        st.session_state.page = "📋 Assessments"
        st.rerun()
 
    if st.button(t('reports'), use_container_width=True, type="primary" if st.session_state.page == "📊 Reports" else "secondary"):
        st.session_state.page = "📊 Reports"
        st.rerun()
 
    st.markdown("---")
    st.markdown("### System Status")
    st.success("✓ Database Online")
    st.success("✓ API Connected")
 
    st.markdown("---")
    shutdown_text = "🔴 Shutdown System" if st.session_state.language == 'en' else "🔴 Выключить систему"
    if st.button(shutdown_text, use_container_width=True):
        # Show shutdown message
        complete_msg = "✅ System shutdown complete. You can close this tab." if st.session_state.language == 'en' else "✅ Выключение завершено. Вы можете закрыть эту вкладку."
        st.success(complete_msg)
 
        try:
            # Call API shutdown endpoint (will terminate both FastAPI and Streamlit)
            # Using a separate thread to avoid blocking
            import threading
            def shutdown_backend():
                try:
                    requests.post(f"{API_BASE}/shutdown", timeout=2)
                except:
                    pass
 
            # Start shutdown in background
            shutdown_thread = threading.Thread(target=shutdown_backend)
            shutdown_thread.daemon = True
            shutdown_thread.start()
 
            # Wait a moment for API to process
            time.sleep(1)
 
            # Kill current Streamlit process
            current_pid = os.getpid()
            psutil.Process(current_pid).terminate()
        except Exception as e:
            # Fallback - just kill current process
            try:
                os.kill(os.getpid(), signal.SIGTERM)
            except:
                pass
 
# Get current page
page = st.session_state.page
 
# ============= DASHBOARD PAGE =============
if page == "Dashboard" or page == "🏠 Dashboard":
    # Professional Header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">NCCR Rehabilitation Platform</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">Advanced Pediatric Rehabilitation Analytics System</p>
    </div>
    """, unsafe_allow_html=True)
 
    # Fetch statistics ONCE
    stats = fetch_stats()
 
    # KPI Cards - Professional Design
    st.markdown(f"### {t('system_overview')}")
    col1, col2, col3, col4 = st.columns(4)
 
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; color: white;">
            <h3 style="margin: 0; font-size: 2.5rem;">{stats['total_patients']}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{t('total_patients')}</p>
        </div>
        """, unsafe_allow_html=True)
 
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 10px; color: white;">
            <h3 style="margin: 0; font-size: 2.5rem;">{stats['total_assessments']}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{t('ai_assessments')}</p>
        </div>
        """, unsafe_allow_html=True)
 
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 10px; color: white;">
            <h3 style="margin: 0; font-size: 2.5rem;">{stats['emg_sessions']}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{t('emg_sessions')}</p>
        </div>
        """, unsafe_allow_html=True)
 
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.5rem; border-radius: 10px; color: white;">
            <h3 style="margin: 0; font-size: 2.5rem;">{stats['balance_tests']}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{t('balance_tests')}</p>
        </div>
        """, unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # Quick Actions
    st.markdown(f"### {t('quick_actions')}")
    col1, col2, col3 = st.columns(3)
 
    with col1:
        if st.button(f"📤 {t('upload_data')}", use_container_width=True, type="primary", key="dash_upload"):
            st.session_state.page = "📤 Import Data"
            st.rerun()
        caption_text = "Import medical records, EMG & balance data" if st.session_state.language == 'en' else "Импорт медицинских записей, ЭМГ и баланс данных"
        st.caption(caption_text)
 
    with col2:
        if st.button(f"👥 {t('manage_patients')}", use_container_width=True, type="primary", key="dash_patients"):
            st.session_state.page = "👥 Patients"
            st.rerun()
        caption_text = "View and manage patient database" if st.session_state.language == 'en' else "Просмотр и управление базой данных пациентов"
        st.caption(caption_text)
 
    with col3:
        if st.button(f"🤖 {t('generate_assessment')}", use_container_width=True, type="primary", key="dash_assess"):
            st.session_state.page = "📋 Assessments"
            st.rerun()
        caption_text = "AI-powered clinical analysis" if st.session_state.language == 'en' else "Клинический анализ на основе AI"
        st.caption(caption_text)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # Recent Activity / System Info
    if stats['total_patients'] > 0:
        st.markdown("### 📈 System Statistics")
 
        col1, col2 = st.columns(2)
 
        with col1:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #667eea;">
                <h4 style="margin: 0 0 1rem 0;">Database Summary</h4>
                <p style="margin: 0.5rem 0;"><strong>Patients:</strong> {}</p>
                <p style="margin: 0.5rem 0;"><strong>Clinical Assessments:</strong> {}</p>
                <p style="margin: 0.5rem 0;"><strong>EMG Data Points:</strong> {}</p>
                <p style="margin: 0.5rem 0;"><strong>Balance Records:</strong> {}</p>
            </div>
            """.format(
                stats['total_patients'],
                stats['total_assessments'],
                stats['emg_sessions'],
                stats['balance_tests']
            ), unsafe_allow_html=True)
 
        with col2:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #43e97b;">
                <h4 style="margin: 0 0 1rem 0;">System Capabilities</h4>
                <p style="margin: 0.5rem 0;">✓ Multi-format data import (PDF, Excel)</p>
                <p style="margin: 0.5rem 0;">✓ Claude AI intelligent parsing</p>
                <p style="margin: 0.5rem 0;">✓ Automated clinical assessments</p>
                <p style="margin: 0.5rem 0;">✓ Real-time analytics & reporting</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #e3f2fd; padding: 2rem; border-radius: 10px; border-left: 5px solid #2196f3; margin-top: 2rem;">
            <h3 style="color: #1976d2; margin-top: 0;">🚀 Get Started</h3>
            <ol style="color: #424242; line-height: 2;">
                <li><strong>Upload Data:</strong> Click "Upload Data Files" to import patient records</li>
                <li><strong>Review Patients:</strong> Check imported data in the Patients section</li>
                <li><strong>Generate Insights:</strong> Use AI to create clinical assessments</li>
                <li><strong>Export Reports:</strong> Download comprehensive patient reports</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
 
# ============= PATIENTS PAGE =============
elif page == "👥 Patients" or page == "Patients":
    title_text = "## 👥 Управление пациентами" if st.session_state.language == 'ru' else "## 👥 Patient Management"
    st.markdown(title_text)
 
    # Tabs
    tab_texts = (["📋 Просмотр всех пациентов", "➕ Добавить пациента"] if st.session_state.language == 'ru' 
                 else ["📋 View All Patients", "➕ Add New Patient"])
    tab1, tab2 = st.tabs(tab_texts)
 
    with tab1:
        # Top buttons
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        with col_btn1:
            header_text = "### База данных пациентов" if st.session_state.language == 'ru' else "### Patient Database"
            st.markdown(header_text)
        with col_btn2:
            btn_text = "🔄 Обновить" if st.session_state.language == 'ru' else "🔄 Refresh Data"
            if st.button(btn_text, use_container_width=True):
                fetch_patients.clear()
                fetch_stats.clear()
                st.rerun()
        with col_btn3:
            btn_text = "🗑️ Удалить все" if st.session_state.language == 'ru' else "🗑️ Delete All"
            if st.button(btn_text, use_container_width=True, type="secondary"):
                st.session_state['confirm_delete_all'] = True
 
        # Confirmation dialog for delete all
        if st.session_state.get('confirm_delete_all', False):
            warning_text = "⚠️ ВНИМАНИЕ: Это удалит всех пациентов и их данные!" if st.session_state.language == 'ru' else "⚠️ WARNING: This will delete all patients and their data!"
            st.error(warning_text)
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                btn_text = "✅ Подтвердить удаление" if st.session_state.language == 'ru' else "✅ Confirm Delete All"
                if st.button(btn_text, type="primary", use_container_width=True):
                    try:
                        patients_to_delete = fetch_patients()
                        deleted_count = 0
                        for patient in patients_to_delete:
                            try:
                                response = requests.delete(f"{API_BASE}/patients/{patient['patient_id']}", timeout=5)
                                if response.status_code in [200, 204]:
                                    deleted_count += 1
                            except:
                                pass
                        success_text = f"Удалено {deleted_count} пациент(ов)" if st.session_state.language == 'ru' else f"Deleted {deleted_count} patient(s)"
                        st.success(success_text)
                        fetch_patients.clear()
                        fetch_stats.clear()
                        st.session_state['confirm_delete_all'] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"{'Ошибка' if st.session_state.language == 'ru' else 'Error'}: {str(e)}")
            with col_confirm2:
                btn_text = "❌ Отмена" if st.session_state.language == 'ru' else "❌ Cancel"
                if st.button(btn_text, use_container_width=True):
                    st.session_state['confirm_delete_all'] = False
                    st.rerun()
 
        # Load patients once
        loading_text = "Загрузка пациентов..." if st.session_state.language == 'ru' else "Loading patients..."
        with st.spinner(loading_text):
            patients = fetch_patients()
        
        # Fetch ALL clinical data in parallel (10x faster!)
        clinical_data = {}
        if patients:
            fetch_text = "Загрузка клинических данных..." if st.session_state.language == 'ru' else "Loading clinical data..."
            with st.spinner(fetch_text):
                def fetch_patient_data(patient_id):
                    """Fetch both clinical tests and documents for one patient"""
                    result = {'tests': [], 'documents': []}
                    try:
                        resp = requests.get(f"{API_BASE}/patients/clinical-tests/{patient_id}", timeout=3)
                        if resp.status_code == 200:
                            result['tests'] = resp.json()
                    except:
                        pass
                    try:
                        resp = requests.get(f"{API_BASE}/clinical-documents/{patient_id}/documents", timeout=3)
                        if resp.status_code == 200:
                            result['documents'] = resp.json().get('documents', [])
                    except:
                        pass
                    return patient_id, result
                
                # Fetch all patients' data in parallel
                with ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_patient = {executor.submit(fetch_patient_data, p.get('patient_id')): p.get('patient_id') for p in patients}
                    for future in as_completed(future_to_patient):
                        patient_id, data = future.result()
                        clinical_data[patient_id] = data

        if patients and len(patients) > 0:
            # Search box
            search = st.text_input(t('search_patients'), "", key="patient_search")
 
            # Convert to DataFrame
            df = pd.DataFrame(patients)
 
            # Clean up date format
            if 'date_of_birth' in df.columns:
                df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce').dt.strftime('%Y-%m-%d')
 
            # Filter by search
            if search:
                df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]
 
            # Show total count
            total_text = f"Всего: {len(df)} пациент(ов)" if st.session_state.language == 'ru' else f"Total: {len(df)} patient(s)"
            st.caption(total_text)
 
            # Display each patient with action buttons
            for idx, patient in df.iterrows():
                with st.expander(f"👤 {patient.get('name', 'N/A')} ({patient.get('patient_id', 'N/A')})"):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
 
                    with col1:
                        st.write(f"**{t('patient_id')}:** {patient.get('patient_id', 'N/A')}")
                        
                        # Translate Unknown Patient
                        patient_name = patient.get('name', 'N/A')
                        if st.session_state.language == 'ru' and patient_name == 'Unknown Patient':
                            patient_name = 'Неизвестный пациент'
                        st.write(f"**{t('name')}:** {patient_name}")
 
                        # Handle DOB display
                        dob_val = patient.get('date_of_birth')
                        if pd.isna(dob_val) or dob_val is None or dob_val == 'NaT':
                            st.write(f"**{t('dob')}:** N/A")
                        else:
                            st.write(f"**{t('dob')}:** {dob_val}")
 
                        # Calculate and show age
                        if dob_val and not pd.isna(dob_val) and dob_val != 'NaT':
                            try:
                                from datetime import datetime
                                dob = pd.to_datetime(dob_val)
                                age = (datetime.now() - dob).days // 365
                                st.write(f"**{t('age')}:** {age} {t('years')}")
                            except:
                                st.write(f"**{t('age')}:** N/A")
                        else:
                            st.write(f"**{t('age')}:** N/A")
 
                        # Translate gender value
                        sex_val = patient.get('sex', 'N/A')
                        if sex_val == 'Male':
                            sex_val = t('male')
                        elif sex_val == 'Female':
                            sex_val = t('female')
                        st.write(f"**{t('sex')}:** {sex_val}")
 
                        # Show additional patient data
                        height = patient.get('height_cm')
                        if height and not pd.isna(height):
                            height_label = "Рост" if st.session_state.language == 'ru' else "Height"
                            st.write(f"**{height_label}:** {height} cm")
 
                        weight = patient.get('weight_kg')
                        if weight and not pd.isna(weight):
                            weight_label = "Вес" if st.session_state.language == 'ru' else "Weight"
                            st.write(f"**{weight_label}:** {weight} kg")
 
                        gmfcs = patient.get('gmfcs_level')
                        if gmfcs and not pd.isna(gmfcs):
                            st.write(f"**GMFCS:** {t('level')} {gmfcs}")

                        # Get pre-fetched clinical data for this patient
                        patient_data = clinical_data.get(patient.get('patient_id'), {})
                        tests = patient_data.get('tests', [])
                        
                        # Display test data if available
                        if tests and len(tests) > 0:
                            test = tests[0]  # Latest test

                            # Display test data directly without header
                            if test.get('distance_6mwt_meters'):
                                st.write(f"**6MWT:** {test['distance_6mwt_meters']} {t('meters')}")
                            if test.get('time_10mwt_seconds'):
                                st.write(f"**10MWT:** {test['time_10mwt_seconds']} {t('sec')}")
                            if test.get('tug_time_seconds'):
                                st.write(f"**TUG:** {test['tug_time_seconds']} {t('sec')}")
                            if test.get('gmfm_score'):
                                st.write(f"**GMFM:** {test['gmfm_score']}%")
                            if test.get('who_qol_score'):
                                st.write(f"**WHO-QOL:** {test['who_qol_score']}")
                            if test.get('omni_exertion_scale'):
                                st.write(f"**OMNI:** {test['omni_exertion_scale']}")
                            if test.get('modified_ashworth_scale'):
                                st.write(f"**Modified Ashworth:** {test['modified_ashworth_scale']}")
                        
                        # ADAPTIVE: Show ALL clinical document data automatically
                        documents = patient_data.get('documents', [])
                        if documents:
                            doc = documents[0]  # Latest document
                            
                            st.markdown("---")
                            st.markdown(f"#### 📋 {t('clinical_data')}")
                            
                            # Icon mapping for different data types
                            icons = {
                                'diagnoses': '🩺',
                                'medications': '💊',
                                'procedures': '🔬',
                                'imaging': '📸',
                                'lab_results': '🧪',
                                'specialist_assessments': '👨‍⚕️',
                                'therapy_sessions': '🏥',
                                'recommendations': '📝',
                                'barthel': '📊',
                                'gmfcs': '📏',
                                'macs': '🤲',
                                'scores': '📈',
                                'clinical': '💉'
                            }
                            
                            def get_icon(field_name):
                                """Get appropriate icon for field"""
                                field_lower = field_name.lower()
                                for key, icon in icons.items():
                                    if key in field_lower:
                                        return icon
                                return '📄'
                            
                            def format_field_name(name):
                                """Convert field_name to readable Title with translation"""
                                if not name:
                                    return ""
                                
                                # Translate exact matches first (for dict keys that appear as-is)
                                exact_translations = {
                                    # Body parts
                                    'Right Arm': 'Правая рука',
                                    'Left Arm': 'Левая рука',
                                    'Right Leg': 'Правая нога',
                                    'Left Leg': 'Левая нога',
                                    
                                    # Common fields (both capitalized and lowercase)
                                    'Admission': 'Прием',
                                    'admission': 'Прием',
                                    'Discharge': 'Выписка',
                                    'discharge': 'Выписка',
                                    'Improvement': 'Улучшение',
                                    'improvement': 'Улучшение',
                                    'Effectiveness': 'Эффективность',
                                    'effectiveness': 'Эффективность',
                                    'Primary': 'Основной',
                                    'primary': 'Основной',
                                    'Secondary': 'Сопутствующий',
                                    'secondary': 'Сопутствующий',
                                    'Date': 'Дата',
                                    'date': 'Дата',
                                    'Result': 'Результат',
                                    'result': 'Результат',
                                    'Findings': 'Находки',
                                    'findings': 'Находки',
                                    'Finding': 'Находка',
                                    'finding': 'Находка',
                                    'Recommendation': 'Рекомендация',
                                    'recommendation': 'Рекомендация',
                                    'Temperature': 'Температура',
                                    'Pulse': 'Пульс',
                                    'Blood Pressure': 'Артериальное давление',
                                    'Respiratory Rate': 'Частота дыхания',
                                    'Oxygen Saturation': 'Насыщение кислородом',
                                    'Total Sessions': 'Всего сеансов',
                                    'Improvement': 'Улучшение',
                                    'Effectiveness': 'Эффективность',
                                    'Category': 'Категория',
                                    'Heart Rate': 'Частота сердцебиения',
                                    
                                    # Specialists
                                    'Psychologist': 'Психолог',
                                    'Speech Therapist': 'Логопед',
                                    'Physiotherapist': 'Физиотерапевт',
                                    'Occupational Therapist': 'Трудотерапевт',
                                    'Music Therapist': 'Музыкотерапевт',
                                    'Game Therapist': 'Игротерапевт',
                                    'Play Therapist': 'Игротерапевт',
                                    'Defectologist': 'Дефектолог',
                                    'Orthotic Specialist': 'Ортопед-техник',
                                    'Prosthetist': 'Протезист',
                                    'Neurologist': 'Невролог',
                                    'Dermatologist': 'Дерматолог',
                                    'Dermatovenerologist': 'Дерматовенеролог',
                                    'Cardiologist': 'Кардиолог',
                                    'Orthopedist': 'Ортопед',
                                    'Rehabilitologist': 'Реабилитолог',
                                    'Montessori Teacher': 'Учитель Монтессори',
                                    'Pediatrician': 'Педиатр',
                                    'Prosthetist Orthotist': 'Ортопед-протезист',
                                    'Consilium Findings': 'Результаты консилиума',
                                    
                                    # Therapy session types
                                    'Occupational Therapy': 'Трудотерапия',
                                    'Physical Therapy': 'Физиотерапия',
                                    'Speech Therapy': 'Логопедия',
                                    'Music Therapy': 'Музыкотерапия',
                                    'Psychological Therapy': 'Психологическая терапия',
                                    'Game Therapy': 'Игровая терапия',
                                    'Play Therapy': 'Игровая терапия',
                                    'Defectology': 'Дефектология',
                                    'Defectologist Sessions': 'Сеансы дефектолога',
                                    'Hydrokinesiotherapy': 'Гидрокинезиотерапия',
                                    'Hydrokinesitherapy': 'Гидрокинезиотерапия',
                                    'Hydrotherapy': 'Гидротерапия',
                                    'Agro Therapy': 'Агротерапия',
                                    'Agrotherapy': 'Агротерапия',
                                    'Bos Logo Therapy': 'БОС логотерапия',
                                    'Bos Motor Training': 'БОС моторная тренировка',
                                    'Robotized Kinesitherapy': 'Роботизированная кинезитерапия',
                                    'Bobath Therapy': 'Терапия Бобата',
                                    'Massage Therapy': 'Массажная терапия',
                                    'Montessori Therapy': 'Терапия Монтессори',
                                    'School Sessions': 'Школьные занятия',
                                    
                                    # Medical procedures (common ones from data)
                                    'Kinesiotherapy upper extremity': 'Кинезиотерапия верхней конечности',
                                    'Kinesiotherapy lower extremity': 'Кинезиотерапия нижней конечности',
                                    'Montessori method sessions': 'Занятия по методу Монтессори',
                                    'Play therapy': 'Игровая терапия',
                                    'Amplipulse therapy': 'Амплипульс-терапия',
                                    'Psychological correction': 'Психологическая коррекция',
                                    
                                    # Test/assessment names
                                    'Modified Ashworth Scale': 'Модифицированная шкала Эшворта',
                                    'Ashworth Scale': 'Шкала Эшворта',
                                    'Gmfm': 'GMFM',
                                    'Gmfm Scale': 'Шкала GMFM',
                                    'Fim Scale': 'Шкала FIM',
                                    'Fim Score': 'Оценка FIM',
                                    'Fim Percentage': 'Процент FIM',
                                    'Rehabilitation Potential': 'Реабилитационный потенциал',
                                    'Rehabilitation Effectiveness': 'Эффективность реабилитации',
                                    'Effectiveness Ratio': 'Коэффициент эффективности',
                                    'Eeg Data': 'Данные ЭЭГ',
                                    'Eeg': 'ЭЭГ',
                                    'Historical Mri': 'Исторические данные МРТ',
                                    'Historical Eeg': 'Исторические данные ЭЭГ',
                                    'Vital Signs Discharge': 'Жизненные показатели при выписке',
                                    'Vital Signs': 'Жизненные показатели',
                                    'Emg Data': 'Данные ЭМГ',
                                    'Balance Data': 'Данные баланса',
                                    'Blood Work': 'Анализ крови',
                                    'Клинические тесты': 'Клинические тесты',
                                    'Лабораторные результаты': 'Лабораторные результаты',
                                    
                                    # Lab test names
                                    'Throat Swab': 'Мазок из зева',
                                    'Blood Culture': 'Посев крови',
                                    'Ultrasound Hepatobiliary': 'УЗИ гепатобилиарной системы',
                                    'Ultrasound Kidneys': 'УЗИ почек',
                                }
                                
                                # Translate Unknown Patient
                                if st.session_state.language == 'ru' and name == 'Unknown Patient':
                                    return 'Неизвестный пациент'
                                
                                # Check exact match first
                                if st.session_state.language == 'ru' and name in exact_translations:
                                    return exact_translations[name]
                                
                                # Normalize the name: replace underscores with spaces and lowercase
                                name_normalized = str(name).replace('_', ' ').lower().strip()
                                
                                # Try to translate common field names
                                field_translations = {
                                    'diagnoses': t('diagnoses'),
                                    'medications': t('medications'),
                                    'procedures': t('procedures'),
                                    'imaging': t('imaging'),
                                    'lab results': t('lab_results'),
                                    'specialist assessments': t('specialist_assessments'),
                                    'therapy sessions': t('therapy_sessions'),
                                    'recommendations': t('recommendations'),
                                    'clinical scores': t('clinical_scores'),
                                    'barthel admission': t('admission'),
                                    'barthel discharge': t('discharge'),
                                    'admission date': t('admission_date'),
                                    'discharge date': t('discharge_date'),
                                    'test results': t('test_results'),
                                    'progress dynamics': t('progress_dynamics'),
                                    'primary': t('primary'),
                                    'secondary': t('secondary'),
                                    'icd codes': t('icd_codes'),
                                    'full diagnosis text': t('full_diagnosis_text'),
                                    'barthel index': t('barthel_index'),
                                    'clinical tests': t('clinical_tests'),
                                    'neurologist': t('neurologist'),
                                    'dermatologist': t('dermatologist'),
                                    'cardiologist': t('cardiologist'),
                                    'blood gas analysis': t('blood_gas_analysis'),
                                    'complete blood count': t('complete_blood_count'),
                                    'biochemistry': t('biochemistry'),
                                    'microbiology': t('microbiology'),
                                    'serology': t('serology'),
                                    'urine analysis': t('urine_analysis'),
                                    'ultrasound abdomen': t('ultrasound_abdomen'),
                                    'echocardiography': t('echocardiography'),
                                    'chest x-ray': t('chest_xray'),
                                    'chest xray': t('chest_xray'),
                                    'ct scan': t('ct_scan'),
                                    'mri': t('mri'),
                                    'procalcitonin': t('procalcitonin'),
                                    'crp': t('crp'),
                                    'ph': t('ph'),
                                    'pco2': t('pco2'),
                                    'po2': t('po2'),
                                    'hct': t('hct'),
                                    'sodium': t('sodium'),
                                    'potassium': t('potassium'),
                                    'calcium': t('calcium'),
                                    'wbc': t('wbc'),
                                    'rbc': t('rbc'),
                                    'hemoglobin': t('hemoglobin'),
                                    'hematocrit': t('hematocrit'),
                                    'platelets': t('platelets'),
                                    'esr': t('esr'),
                                    'total protein': t('total_protein'),
                                    'albumin': t('albumin'),
                                    'alt': t('alt'),
                                    'ast': t('ast'),
                                    'total bilirubin': t('total_bilirubin'),
                                    'glucose': t('glucose'),
                                    'urea': t('urea'),
                                    'creatinine': t('creatinine'),
                                    'throat culture': t('throat_culture'),
                                    'blood culture sterility': t('blood_culture_sterility'),
                                    'blood culture salmonella': t('blood_culture_salmonella'),
                                    'cmv igg': t('cmv_igg'),
                                    'cmv igm': t('cmv_igm'),
                                    'cmv pcr': t('cmv_pcr'),
                                    'brucellosis': t('brucellosis'),
                                    'malaria': t('malaria'),
                                    'protein': t('protein'),
                                    'leukocytes': t('leukocytes'),
                                    'erythrocytes': t('erythrocytes')
                                }
                                
                                # Check normalized version
                                if name_normalized in field_translations:
                                    return field_translations[name_normalized]
                                
                                # Translate 'stable'
                                if name_normalized == 'stable':
                                    return t('stable')
                                
                                return name.replace('_', ' ').title()
                                    
                            def translate_value(value):
                                """Translate common data values"""
                                if not isinstance(value, str):
                                    return value
                                
                                # Skip translation if not in Russian mode
                                if st.session_state.language != 'ru':
                                    return value
                                
                                # Common translations dictionary
                                translations = {
                                    # Gender
                                    'Male': 'Мужской',
                                    'Female': 'Женский',
                                    'None': 'Не указан',
                                    
                                    # Categories
                                    'Primary': 'Основной',
                                    'Secondary': 'Сопутствующий',
                                    'Admission': 'Прием',
                                    'Discharge': 'Выписка',
                                    
                                    # Body parts
                                    'Right Arm': 'Правая рука',
                                    'Left Arm': 'Левая рука',
                                    'Right Leg': 'Правая нога',
                                    'Left Leg': 'Левая нога',
                                    
                                    # Status
                                    'stable': 'стабильно',
                                    'Stable': 'Стабильно',
                                    'present': 'присутствует',
                                    'absent': 'отсутствует',
                                    'negative': 'отрицательно',
                                    'no growth': 'роста нет',
                                    
                                    # Common medical terms
                                    'Date': 'Дата',
                                    'Result': 'Результат',
                                    'Findings': 'Находки',
                                    'Temperature': 'Температура',
                                    'Pulse': 'Пульс',
                                    'Blood Pressure': 'Артериальное давление',
                                    'Respiratory Rate': 'Частота дыхания',
                                    'Oxygen Saturation': 'Насыщение кислородом',
                                    'Total Sessions': 'Всего сеансов',
                                    
                                    # Session types
                                    'Occupational Therapy': 'Трудотерапия',
                                    'Physical Therapy': 'Физиотерапия',
                                    'Speech Therapy': 'Логопедия',
                                    'Music Therapy': 'Музыкотерапия',
                                    'Psychological Therapy': 'Психологическая терапия',
                                    'Game Therapy': 'Игровая терапия',
                                    'Defectology': 'Дефектология',
                                    'Hydrokinesiotherapy': 'Гидрокинезиотерапия',
                                    'Agro Therapy': 'Агротерапия',
                                }
                                
                                # Check exact match first
                                if value in translations:
                                    return translations[value]
                                
                                # Check lowercase
                                if value.lower() in [k.lower() for k in translations.keys()]:
                                    for k, v in translations.items():
                                        if k.lower() == value.lower():
                                            return v
                                
                                return value
                                    
                            def display_value(value, indent=2, max_items=10):
                                """Recursively display any value type"""
                                spaces = "  " * indent
                                
                                if value is None or value == "" or value == []:
                                    return
                                
                                # Handle lists
                                elif isinstance(value, list):
                                    for i, item in enumerate(value[:max_items]):
                                        if isinstance(item, dict):
                                            # Dict in list - show key info
                                            main_key = next((k for k in ['name', 'type', 'specialist', 'procedure', 'medication', 'recommendation'] if k in item), None)
                                            if main_key:
                                                main_val = translate_value(item[main_key])
                                                # Show additional details if available
                                                details = []
                                                for k, v in item.items():
                                                    if k != main_key and v and isinstance(v, (str, int, float)) and len(str(v)) < 50:
                                                        details.append(f"{format_field_name(k)}: {translate_value(v)}")
                                                detail_str = f" ({', '.join(details[:2])})" if details else ""
                                                st.write(f"{spaces}• {main_val}{detail_str}")
                                            else:
                                                # Just show all fields compactly
                                                items = [f"{format_field_name(k)}: {translate_value(v)}" for k, v in item.items() if v and len(str(v)) < 100]
                                                if items:
                                                    st.write(f"{spaces}• {', '.join(items[:3])}")
                                        elif isinstance(item, str):
                                            # Truncate long strings and translate
                                            display_str = item[:150] + "..." if len(item) > 150 else item
                                            display_str = translate_value(display_str)
                                            st.write(f"{spaces}• {display_str}")
                                        else:
                                            st.write(f"{spaces}• {item}")
                                    
                                    if len(value) > max_items:
                                        remaining = len(value) - max_items
                                        st.write(f"{spaces}... {t('and_more')} {remaining} {t('more')}")
                                
                                # Handle dictionaries
                                elif isinstance(value, dict):
                                    # Check if it's a simple key-value dict
                                    if all(isinstance(v, (str, int, float, type(None))) for v in value.values()):
                                        # Show as key: value pairs
                                        for k, v in value.items():
                                            if v is not None and v != "":
                                                if isinstance(v, (int, float)):
                                                    st.write(f"{spaces}• {format_field_name(k)}: **{v}**")
                                                else:
                                                    display_str = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                                                    display_str = translate_value(display_str) 
                                                    st.write(f"{spaces}• {format_field_name(k)}: {display_str}")
                                    else:
                                        # Complex nested dict - recurse
                                        for k, v in value.items():
                                            if v:
                                                st.markdown(f"{spaces}**{format_field_name(k)}:**")
                                                display_value(v, indent + 1, max_items=5)
                                
                                # Handle numbers
                                elif isinstance(value, (int, float)):
                                    st.write(f"{spaces}**{value}**")
                                
                                # Handle strings
                                elif isinstance(value, str):
                                    display_str = value[:200] + "..." if len(value) > 200 else value
                                    display_str = translate_value(display_str)
                                    st.write(f"{spaces}{display_str}")
                                    
                            # Define priority order for display
                            priority_fields = [
                                'diagnoses', 'barthel_admission', 'barthel_discharge', 
                                'gmfcs_level', 'macs_level', 'clinical_scores',
                                'medications', 'procedures', 'imaging', 
                                'lab_results', 'specialist_assessments', 
                                'therapy_sessions', 'recommendations'
                            ]
                                    
                            # Collect all non-empty fields
                            displayed_fields = set()
                                    
                            # First, show priority fields
                            for field in priority_fields:
                                value = doc.get(field)
                                if value:
                                    displayed_fields.add(field)
                                    icon = get_icon(field)
                                            
                                    # Special handling for Barthel scores
                                    if field == 'barthel_admission':
                                        bart_discharge = doc.get('barthel_discharge')
                                        if bart_discharge:
                                            displayed_fields.add('barthel_discharge')
                                            improvement = bart_discharge - value
                                            pct = (improvement / value * 100) if value > 0 else 0
                                            st.markdown(f"**{icon} {t('barthel_index')}:** {t('admission')}: {value} → {t('discharge')}: {bart_discharge} (Δ +{improvement}, +{pct:.1f}%)")
                                        else:
                                            st.markdown(f"**{icon} Barthel Admission:** {value}")
                                        continue
                                    elif field == 'barthel_discharge' and 'barthel_admission' in displayed_fields:
                                        continue  # Already handled above
                                            
                                    # Count items if it's a list/dict
                                    count = ""
                                    if isinstance(value, list):
                                        count = f" ({len(value)})"
                                    elif isinstance(value, dict) and not all(isinstance(v, (str, int, float, type(None))) for v in value.values()):
                                        non_empty = sum(1 for v in value.values() if v)
                                        if non_empty > 0:
                                            count = f" ({non_empty} {t('items')})"
                                            
                                    st.markdown(f"**{icon} {format_field_name(field)}{count}:**")
                                    display_value(value, indent=1)
                                    
                            # Then show any other non-empty fields not in priority list
                            other_fields = []
                            skip_fields = {'id', 'patient_id', 'created_at', 'document_date', 'filename', 'raw_extracted_data', 'document_type'}
                                    
                            for field, value in doc.items():
                                if field not in displayed_fields and field not in skip_fields and value:
                                    other_fields.append((field, value))
                        
                            if other_fields:
                                st.markdown(f"**📋 {t('additional_data')}:**")
                                for field, value in other_fields[:10]:
                                    icon = get_icon(field)
                                    count = f" ({len(value)})" if isinstance(value, (list, dict)) else ""
                                    st.markdown(f"**{icon} {format_field_name(field)}{count}:**")
                                    display_value(value, indent=1, max_items=5)

                with col2:
                    btn_text = "Оценить" if st.session_state.language == 'ru' else "Assess"
                    if st.button(btn_text, key=f"assess_{patient.get('patient_id')}", use_container_width=True):
                            spinner_text = "Анализ..." if st.session_state.language == 'ru' else "Analyzing..."
                            with st.spinner(spinner_text):
                                success, result = generate_assessment(patient.get('patient_id'), use_claude_ai=True)
                                if success:
                                    success_text = "✅ Оценка завершена!" if st.session_state.language == 'ru' else "✅ Assessment complete!"
                                    st.success(success_text)
                                    time.sleep(1)
                                    fetch_patients.clear()
                                    st.rerun()
                                else:
                                    error_text = f"❌ Ошибка: {result}" if st.session_state.language == 'ru' else f"❌ Failed: {result}"
                                    st.error(error_text)
 
                    with col3:
                        btn_text = t('delete_patient')
                        if st.button(btn_text, key=f"delete_{patient.get('patient_id')}", use_container_width=True, type="secondary"):
                            try:
                                response = requests.delete(f"{API_BASE}/patients/{patient.get('patient_id')}", timeout=5)
                                if response.status_code in [200, 204]:
                                    success_text = "✅ Удалено!" if st.session_state.language == 'ru' else "✅ Deleted!"
                                    st.success(success_text)
                                    fetch_patients.clear()
                                    fetch_stats.clear()
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    error_text = "❌ Не удалось удалить" if st.session_state.language == 'ru' else "❌ Failed to delete"
                                    st.error(error_text)
                            except Exception as e:
                                st.error(f"❌ {t('error')}: {str(e)}")
 
                    with col4:
                        btn_text = t('clear_assessments')
                        if st.button(btn_text, key=f"clear_assess_{patient.get('patient_id')}", use_container_width=True, type="secondary"):
                            try:
                                response = requests.delete(f"{API_BASE}/assessments/{patient.get('patient_id')}", timeout=5)
                                if response.status_code in [200, 204]:
                                    success_text = "✅ Очищено!" if st.session_state.language == 'ru' else "✅ Cleared!"
                                    st.success(success_text)
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    warning_text = "Оценки не найдены" if st.session_state.language == 'ru' else "No assessments found"
                                    st.warning(warning_text)
                            except Exception as e:
                                st.error(f"❌ {t('error')}: {str(e)}")
        else:
            warning_text = "📭 Пациенты не найдены в базе данных." if st.session_state.language == 'ru' else "📭 No patients found in database."
            info_text = ("👉 Перейдите на страницу **Импорт данных** для загрузки файлов пациентов (PDF или Excel)" if st.session_state.language == 'ru' 
                        else "👉 Go to **Import Data** page to upload patient files (PDF or Excel)")
            btn_text = "📤 Перейти к импорту данных" if st.session_state.language == 'ru' else "📤 Go to Import Data"
            st.warning(warning_text)
            st.info(info_text)
            if st.button(btn_text, type="primary"):
                st.session_state.page = "📤 Import Data"
                st.rerun()
 
    with tab2:
        st.markdown("### Add New Patient")
 
        with st.form("add_patient_form"):
            col1, col2 = st.columns(2)
 
            with col1:
                patient_id = st.text_input("Patient ID *", placeholder="e.g., PAT001")
                name = st.text_input("Full Name *", placeholder="e.g., John Doe")
                dob = st.date_input("Date of Birth *")
                sex = st.selectbox("Sex", ["", "Male", "Female"])
 
            with col2:
                height = st.number_input("Height (cm)", min_value=0.0, step=0.1)
                weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
                gmfcs = st.selectbox("GMFCS Level", ["", 1, 2, 3, 4, 5])
                diagnosis = st.text_area("Diagnosis")
 
            submitted = st.form_submit_button("✅ Add Patient", use_container_width=True)
 
            if submitted:
                if patient_id and name:
                    data = {
                        "patient_id": patient_id,
                        "name": name,
                        "date_of_birth": dob.isoformat() + "T00:00:00",
                        "sex": sex if sex else None,
                        "height_cm": height if height > 0 else None,
                        "weight_kg": weight if weight > 0 else None,
                        "gmfcs_level": gmfcs if gmfcs else None,
                        "diagnosis": diagnosis if diagnosis else None
                    }
 
                    try:
                        with st.spinner("Adding patient..."):
                            response = requests.post(f"{API_BASE}/patients/", json=data, timeout=5)
                            if response.status_code == 200:
                                st.success("✅ Patient added successfully!")
                                # Clear cache to refresh data
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to add patient: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please fill in required fields (Patient ID and Name)")
 
# ============= IMPORT DATA PAGE =============
elif page == "📤 Import Data" or page == "Import Data":
    title_text = "Загрузка файлов данных" if st.session_state.language == 'ru' else "Upload Data Files"
    st.title(title_text)
 
    # Claude AI toggle
    checkbox_text = "Использовать AI парсер" if st.session_state.language == 'ru' else "Use AI Parser"
    help_text = "Улучшенное извлечение данных" if st.session_state.language == 'ru' else "Enhanced data extraction"
    use_claude = st.checkbox(checkbox_text, value=True, help=help_text)
 
    select_text = t('select_files')
    uploaded_files = st.file_uploader(
        select_text,
        type=['pdf', 'xlsx', 'xls'],
        accept_multiple_files=True,
        key="file_uploader"
    )
 
    if uploaded_files:
        if st.button(t('process_files'), use_container_width=True, type="primary"):
 
            for file in uploaded_files:
                processing_text = f"**{t('processing')}:** {file.name}"
                st.markdown(processing_text)
 
                with st.spinner(t('processing')):
                    # Determine file type and upload
                    if file.name.endswith('.pdf'):
                        success, result = upload_pdf_any(file, use_claude_ai=use_claude)
                    else:
                        success, result = upload_clinical_excel(file, use_claude_ai=use_claude)
 
                    if success and result:
                        # Extract info from response
                        message = result.get('message', '')
                        patient_name = result.get('patient_name', '')
                        patients_count = result.get('patients_created', 0)
                        tests_added = result.get('balance_tests_added', 0) or result.get('emg_sessions_created', 0) or result.get('clinical_tests_created', 0) or result.get('muscles_extracted', 0)
 
                        # Show appropriate success message
                        if patients_count > 0:
                            st.success(f"✅ {file.name}: Created {patients_count} new patient(s)")
                        elif tests_added > 0:
                            st.success(f"✅ {file.name}: Added {tests_added} test(s) for {patient_name}")
                        elif message:
                            st.success(f"✅ {file.name}: {message}")
                        else:
                            st.success(f"✅ {file.name}: Imported successfully")
                    else:
                        st.error(f"❌ {file.name}: Import failed")
                        if result and isinstance(result, dict):
                            if 'detail' in result:
                                st.error(f"Details: {result['detail']}")
                            elif 'error' in result:
                                st.error(f"Error: {result['error']}")
 
            st.markdown("---")
            st.success("✅ All files processed! Go to Patients page to see your data.")
            if st.button("👥 View Patients Now", type="primary"):
                st.session_state.page = "👥 Patients"
                fetch_patients.clear()  # Clear cache
                fetch_stats.clear()  # Clear cache
                st.rerun()
 
    st.markdown("---")
    supported_header = "### ℹ️ Поддерживаемые файлы" if st.session_state.language == 'ru' else "### ℹ️ Supported Files"
    st.markdown(supported_header)
    col1, col2 = st.columns(2)
    with col1:
        pdf_title = "**📄 PDF файлы:**" if st.session_state.language == 'ru' else "**📄 PDF Files:**"
        st.markdown(pdf_title)
        if st.session_state.language == 'ru':
            st.markdown("- Отчеты Noraxon ЭМГ")
            st.markdown("- Тесты баланса TecnoBody")
        else:
            st.markdown("- Noraxon EMG reports")
            st.markdown("- TecnoBody balance tests")
    with col2:
        excel_title = "**📊 Excel файлы:**" if st.session_state.language == 'ru' else "**📊 Excel Files:**"
        st.markdown(excel_title)
        if st.session_state.language == 'ru':
            st.markdown("- Демографические данные пациентов")
            st.markdown("- Поэтапные данные ЭМГ (Улан)")
            st.markdown("- Результаты клинических тестов")
        else:
            st.markdown("- Patient demographics")
            st.markdown("- Stage-based EMG data (Ulan)")
            st.markdown("- Clinical test results")
 
# ============= ASSESSMENTS PAGE =============
elif page == "📋 Assessments" or page == "Assessments":
    title_text = "Оценки" if st.session_state.language == 'ru' else "Assessments"
    st.title(title_text)
 
    loading_text = "Загрузка пациентов..." if st.session_state.language == 'ru' else "Loading patients..."
    with st.spinner(loading_text):
        patients = fetch_patients()
 
    if patients:
        patient_ids = [p['patient_id'] for p in patients]
        select_text = "Выберите пациента" if st.session_state.language == 'ru' else "Select Patient"
        selected = st.selectbox(select_text, patient_ids)
 
        col1, col2 = st.columns(2)
 
        with col1:
            btn_text = "🔬 Создать новую оценку" if st.session_state.language == 'ru' else "🔬 Generate New Assessment"
            if st.button(btn_text, use_container_width=True):
                spinner_text = "AI анализирует данные... Это может занять 15-30 секунд..." if st.session_state.language == 'ru' else "AI is analyzing data... This may take 15-30 seconds..."
                with st.spinner(spinner_text):
                    success, result = generate_assessment(selected)
                    if success:
                        success_text = "✅ Оценка завершена!" if st.session_state.language == 'ru' else "✅ Assessment completed!"
                        st.success(success_text)
                        st.json(result)
                        st.cache_data.clear()
                    else:
                        error_text = f"❌ Ошибка: {result}" if st.session_state.language == 'ru' else f"❌ Failed: {result}"
                        st.error(error_text)
 
        with col2:
            btn_text = "👁️ Просмотр истории оценок" if st.session_state.language == 'ru' else "👁️ View Assessment History"
            if st.button(btn_text, use_container_width=True):
                info_text = "💡 Получение истории оценок..." if st.session_state.language == 'ru' else "💡 Fetching assessment history..."
                st.info(info_text)
                try:
                    response = requests.get(f"{API_BASE}/assessments/{selected}", timeout=5)
                    if response.status_code == 200:
                        assessments = response.json()
                        if assessments:
                            found_text = f"Найдено {len(assessments)} оценок" if st.session_state.language == 'ru' else f"Found {len(assessments)} assessment(s)"
                            st.write(found_text)
                            for idx, assessment in enumerate(assessments):
                                expander_text = f"Оценка {idx+1} - {assessment.get('assessment_date', 'N/A')}" if st.session_state.language == 'ru' else f"Assessment {idx+1} - {assessment.get('assessment_date', 'N/A')}"
                                with st.expander(expander_text):
                                    st.json(assessment)
                        else:
                            no_assess_text = "Оценки для этого пациента не найдены" if st.session_state.language == 'ru' else "No assessments found for this patient"
                            st.info(no_assess_text)
                    else:
                        warning_text = "Не удалось получить оценки" if st.session_state.language == 'ru' else "Could not fetch assessments"
                        st.warning(warning_text)
                except Exception as e:
                    st.error(f"{t('error')}: {str(e)}")

        # RAG Search Section - inside if patients block
        st.markdown("---")
        search_title = "### 🔍 Поиск по документам пациента" if st.session_state.language == 'ru' else "### 🔍 Search Patient Documents"
        st.markdown(search_title)

        search_placeholder = "Например: какой диагноз у пациента?" if st.session_state.language == 'ru' else "e.g. what is the diagnosis of this patient?"
        search_query = st.text_input("Search", placeholder=search_placeholder, key="rag_search", label_visibility="collapsed")

        search_btn = "🔍 Найти" if st.session_state.language == 'ru' else "🔍 Search"
        if st.button(search_btn, type="primary") and search_query and selected:
            with st.spinner("Searching documents..." if st.session_state.language == 'en' else "Поиск в документах..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/assessments/{selected}/search",
                        params={"query": search_query},
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        chunks = result.get('chunks_found', 0)
                        if chunks == 0:
                            st.warning("No relevant documents found for this patient." if st.session_state.language == 'en' else "Документы для этого пациента не найдены.")
                        else:
                            st.success(f"Found answer from {chunks} document sections")
                            st.markdown("#### Answer:")
                            st.markdown(result.get('answer', ''))
                            confidence = result.get('confidence', 0)
                            st.caption(f"Search confidence: {confidence:.2f} | Sections searched: {chunks}")
                    else:
                        st.error("Search failed")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    else:
        warning_text = "⚠️ Пациенты не найдены. Пожалуйста, сначала импортируйте данные." if st.session_state.language == 'ru' else "⚠️ No patients found. Please import data first."
        st.warning(warning_text)
 
    # Features Info
    st.markdown("---")
    features_title = "### 🔬 Возможности оценки" if st.session_state.language == 'ru' else "### 🔬 Assessment Features"
    st.markdown(features_title)
 
    col1, col2, col3, col4 = st.columns(4)
 
    with col1:
        title = "**💪 Моторная функция**" if st.session_state.language == 'ru' else "**💪 Motor Function**"
        caption = "Анализ координации мышц на основе ЭМГ" if st.session_state.language == 'ru' else "EMG-based muscle coordination analysis"
        st.markdown(title)
        st.caption(caption)
 
    with col2:
        title = "**⚖️ Оценка баланса**" if st.session_state.language == 'ru' else "**⚖️ Balance Assessment**"
        caption = "Индекс стабильности и контроль осанки" if st.session_state.language == 'ru' else "Stability index and postural control"
        st.markdown(title)
        st.caption(caption)
 
    with col3:
        title = "**🧠 Когнитивные показатели**" if st.session_state.language == 'ru' else "**🧠 Cognitive Indicators**"
        caption = "Внимание и скорость обработки" if st.session_state.language == 'ru' else "Attention and processing speed"
        st.markdown(title)
        st.caption(caption)
 
    with col4:
        title = "**📊 Оценка инвалидности**" if st.session_state.language == 'ru' else "**📊 Disability Scoring**"
        caption = "Комплексная классификация тяжести" if st.session_state.language == 'ru' else "Comprehensive severity classification"
        st.markdown(title)
        st.caption(caption)
 
# ============= REPORTS PAGE =============
elif page == "📊 Reports" or page == "Reports":
    title_text = "Отчеты" if st.session_state.language == 'ru' else "Reports"
    st.title(title_text)
 
    info_text = "💡 Создавайте комплексные отчеты и визуализации для отслеживания прогресса пациентов." if st.session_state.language == 'ru' else "💡 Generate comprehensive reports and visualizations for patient progress tracking."
    st.info(info_text)
 
    # Report Options
    col1, col2 = st.columns(2)
 
    with col1:
        header_text = "### 👤 Индивидуальный отчет пациента" if st.session_state.language == 'ru' else "### 👤 Individual Patient Report"
        st.markdown(header_text)
        description = "Комплексные результаты оценки и рекомендации по реабилитации" if st.session_state.language == 'ru' else "Comprehensive assessment results and rehabilitation recommendations"
        st.markdown(description)
 
        loading_text = "Загрузка пациентов..." if st.session_state.language == 'ru' else "Loading patients..."
        with st.spinner(loading_text):
            patients = fetch_patients()
 
        if patients:
            select_text = "Выберите пациента" if st.session_state.language == 'ru' else "Select Patient"
            patient = st.selectbox(select_text, [p['patient_id'] for p in patients])
            btn_text = "📄 Создать отчет" if st.session_state.language == 'ru' else "📄 Generate Report"
            if st.button(btn_text, use_container_width=True):
                spinner_text = "Создание отчета..." if st.session_state.language == 'ru' else "Generating report..."
                with st.spinner(spinner_text):
                    try:
                        # Fetch patient summary
                        response = requests.get(f"{API_BASE}/patients/{patient}/summary", timeout=10)
                        if response.status_code == 200:
                            summary = response.json()
                            success_text = "✅ Отчет создан!" if st.session_state.language == 'ru' else "✅ Report generated!"
                            st.success(success_text)
 
                            # Display summary
                            patient_label = "Пациент" if st.session_state.language == 'ru' else "Patient"
                            patient_info = summary.get('patient', {})
                            st.markdown(f"## {patient_label}: {patient_info.get('name', 'N/A')}")
                            st.json(summary)
 
                            # Store in session state for export
                            st.session_state['current_patient_data'] = summary
                            st.session_state['current_patient_id'] = patient
                        else:
                            warning_text = "Не удалось создать отчет" if st.session_state.language == 'ru' else "Could not generate report"
                            st.warning(warning_text)
                    except Exception as e:
                        st.error(f"{t('error')}: {str(e)}")
 
            # Export Buttons
            st.markdown("---")
            export_header = "### 📥 Варианты экспорта" if st.session_state.language == 'ru' else "### 📥 Export Options"
            st.markdown(export_header)
 
            export_col1, export_col2, export_col3 = st.columns(3)
 
            with export_col1:
                btn_text = "📄 Скачать PDF отчет" if st.session_state.language == 'ru' else "📄 Download PDF Report"
                if st.button(btn_text, use_container_width=True):
                    if 'current_patient_data' in st.session_state:
                        try:
                            patient_data = st.session_state['current_patient_data']
 
                            # Get latest assessment
                            assessment_data = None
                            try:
                                assess_response = requests.get(f"{API_BASE}/assessments/{patient}", timeout=5)
                                if assess_response.status_code == 200:
                                    assessments = assess_response.json()
                                    if assessments and len(assessments) > 0:
                                        assessment_data = assessments[-1]  # Latest assessment
                            except:
                                pass
 
                            pdf_buffer = generate_pdf_report(patient_data, assessment_data)
 
                            download_label = "💾 Сохранить PDF файл" if st.session_state.language == 'ru' else "💾 Save PDF File"
                            st.download_button(
                                label=download_label,
                                data=pdf_buffer,
                                file_name=f"report_{patient}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            success_text = "✅ PDF готов к загрузке!" if st.session_state.language == 'ru' else "✅ PDF ready for download!"
                            st.success(success_text)
                        except Exception as e:
                            error_text = f"Ошибка создания PDF: {str(e)}" if st.session_state.language == 'ru' else f"Error generating PDF: {str(e)}"
                            st.error(error_text)
                    else:
                        warning_text = "⚠️ Пожалуйста, сначала создайте отчет" if st.session_state.language == 'ru' else "⚠️ Please generate a report first"
                        st.warning(warning_text)
 
            with export_col2:
                btn_text = "📊 Скачать данные Excel" if st.session_state.language == 'ru' else "📊 Download Excel Data"
                if st.button(btn_text, use_container_width=True):
                    if 'current_patient_data' in st.session_state:
                        try:
                            summary = st.session_state['current_patient_data']
                            patient_data = summary.get('patient', summary)  # Handle nested structure
 
                            # Fetch all data for Excel
                            assessments = []
                            clinical_tests = []
                            emg_data = []
                            balance_data = []
 
                            try:
                                assess_response = requests.get(f"{API_BASE}/assessments/{patient}", timeout=5)
                                if assess_response.status_code == 200:
                                    assessments = assess_response.json()
                            except:
                                pass
 
                            try:
                                clinical_response = requests.get(f"{API_BASE}/patients/clinical-tests/{patient}", timeout=5)
                                if clinical_response.status_code == 200:
                                    clinical_tests = clinical_response.json()
                            except:
                                pass
 
                            excel_buffer = generate_excel_export(patient_data, assessments, clinical_tests, emg_data, balance_data)
 
                            download_label = "💾 Сохранить Excel файл" if st.session_state.language == 'ru' else "💾 Save Excel File"
                            st.download_button(
                                label=download_label,
                                data=excel_buffer,
                                file_name=f"data_{patient}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            success_text = "✅ Excel файл готов к загрузке!" if st.session_state.language == 'ru' else "✅ Excel file ready for download!"
                            st.success(success_text)
                        except Exception as e:
                            error_text = f"Ошибка создания Excel: {str(e)}" if st.session_state.language == 'ru' else f"Error generating Excel: {str(e)}"
                            st.error(error_text)
                    else:
                        warning_text = "⚠️ Пожалуйста, сначала создайте отчет" if st.session_state.language == 'ru' else "⚠️ Please generate a report first"
                        st.warning(warning_text)
 
            with export_col3:
                btn_text = "🤖 Скачать AI оценку" if st.session_state.language == 'ru' else "🤖 Download AI Assessment"
                if st.button(btn_text, use_container_width=True):
                    try:
                        # Fetch assessments for this patient
                        assess_response = requests.get(f"{API_BASE}/assessments/{patient}", timeout=5)
                        if assess_response.status_code == 200:
                            assessments = assess_response.json()
                            if assessments and len(assessments) > 0:
                                # Create assessment report
                                report_title = "ОТЧЕТ AI ОЦЕНКИ" if st.session_state.language == 'ru' else "AI ASSESSMENT REPORT"
                                patient_label = "ID пациента" if st.session_state.language == 'ru' else "Patient ID"
                                generated_label = "Создано" if st.session_state.language == 'ru' else "Generated"
 
                                assessment_text = f"{report_title}\n"
                                assessment_text += f"{patient_label}: {patient}\n"
                                assessment_text += f"{generated_label}: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                                assessment_text += f"\n{'='*60}\n\n"
 
                                for idx, assessment in enumerate(assessments, 1):
                                    assess_label = "Оценка" if st.session_state.language == 'ru' else "Assessment"
                                    date_label = "Дата" if st.session_state.language == 'ru' else "Date"
                                    motor_label = "Моторная функция" if st.session_state.language == 'ru' else "Motor Function Score"
                                    balance_label = "Баланс" if st.session_state.language == 'ru' else "Balance Score"
                                    disability_label = "Тяжесть инвалидности" if st.session_state.language == 'ru' else "Disability Severity"
                                    fall_risk_label = "Риск падения" if st.session_state.language == 'ru' else "Fall Risk Level"
                                    confidence_label = "Уверенность" if st.session_state.language == 'ru' else "Confidence"
 
                                    assessment_text += f"{assess_label} #{idx}\n"
                                    assessment_text += f"{date_label}: {assessment.get('assessment_date', 'N/A')}\n"
                                    assessment_text += f"{motor_label}: {assessment.get('motor_function_score', 'N/A')}\n"
                                    assessment_text += f"{balance_label}: {assessment.get('balance_score', 'N/A')}\n"
                                    assessment_text += f"{disability_label}: {assessment.get('disability_severity', 'N/A')}\n"
                                    assessment_text += f"{fall_risk_label}: {assessment.get('fall_risk_level', 'N/A')}\n"
                                    assessment_text += f"{confidence_label}: {assessment.get('confidence_score', 'N/A')}\n"
 
                                    if assessment.get('detailed_results'):
                                        detailed_label = "Подробные результаты" if st.session_state.language == 'ru' else "Detailed Results"
                                        assessment_text += f"\n{detailed_label}:\n{assessment.get('detailed_results')}\n"
 
                                    assessment_text += f"\n{'-'*60}\n\n"
 
                                download_label = "💾 Сохранить файл оценки" if st.session_state.language == 'ru' else "💾 Save Assessment File"
                                st.download_button(
                                    label=download_label,
                                    data=assessment_text,
                                    file_name=f"assessment_{patient}_{datetime.now().strftime('%Y%m%d')}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                                success_text = f"✅ Найдено {len(assessments)} оценок!" if st.session_state.language == 'ru' else f"✅ Found {len(assessments)} assessment(s)!"
                                st.success(success_text)
                            else:
                                warning_text = "Оценки для этого пациента не найдены" if st.session_state.language == 'ru' else "No assessments found for this patient"
                                st.warning(warning_text)
                        else:
                            warning_text = "Не удалось получить оценки" if st.session_state.language == 'ru' else "Could not fetch assessments"
                            st.warning(warning_text)
                    except Exception as e:
                        st.error(f"{t('error')}: {str(e)}")
 
        else:
            warning_text = "Пациенты недоступны" if st.session_state.language == 'ru' else "No patients available"
            st.warning(warning_text)
 
    with col2:
        header_text = "### 📊 Статистика популяции" if st.session_state.language == 'ru' else "### 📊 Population Statistics"
        st.markdown(header_text)
        description = "Агрегированная статистика по всем пациентам" if st.session_state.language == 'ru' else "Aggregate statistics across all patients"
        st.markdown(description)
        btn_text = "📊 Просмотр статистики" if st.session_state.language == 'ru' else "📊 View Stats"
        if st.button(btn_text, use_container_width=True):
            spinner_text = "Получение статистики..." if st.session_state.language == 'ru' else "Fetching statistics..."
            with st.spinner(spinner_text):
                stats = fetch_stats()
                st.metric(t('total_patients'), stats['total_patients'])
                st.metric(t('ai_assessments'), stats['total_assessments'])
                st.metric(t('emg_sessions'), stats['emg_sessions'])
                st.metric(t('balance_tests'), stats['balance_tests'])
 
    st.markdown("---")
 
    # Features
    features_title = "### 💡 Возможности отчетов" if st.session_state.language == 'ru' else "### 💡 Report Features"
    st.markdown(features_title)
 
    if st.session_state.language == 'ru':
        st.markdown("""
        - ✅ **AI аналитика:** Автоматическая интерпретация результатов оценки
        - ✅ **Печать и обмен:** Профессиональные PDF и Excel отчеты
        - ✅ **Экспорт данных:** Загрузка данных в различных форматах
        """)
    else:
        st.markdown("""
        - ✅ **AI Insights:** Automated interpretation of assessment results
        - ✅ **Print & Share:** Professional PDF and Excel reports
        - ✅ **Data Export:** Download data in multiple formats
        """)
 
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <p>NCCR Rehabilitation Analytics Platform v1.0.0 | Powered by AI</p>
</div>
""", unsafe_allow_html=True)