"""
Claude AI Integration - FINAL FIXED VERSION
Correctly extracts Noraxon EMG data
"""
import anthropic
from typing import Dict, List, Optional, Any
import json
import base64
from pathlib import Path
import pandas as pd
import pdfplumber
import os


class ClaudeAI:
    """Claude AI integration for intelligent analysis"""
    
    def __init__(self, api_key: str = None, model: str = None, max_tokens: int = None):
        """Initialize Claude AI client"""
        if api_key is None:
            from config.settings import settings
            api_key = settings.CLAUDE_API_KEY
            model = settings.CLAUDE_MODEL if model is None else model
            max_tokens = settings.CLAUDE_MAX_TOKENS if max_tokens is None else max_tokens
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or "claude-sonnet-4-5"
        self.max_tokens = max_tokens or 8096
    
    def parse_noraxon_emg_pdf(self, pdf_path: str) -> Dict:
        """
        Specialized parser for Noraxon EMG reports
        """
        try:
            # Extract text from PDF
            pdf_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    pdf_text += page.extract_text() + "\n\n"
            
            if not pdf_text.strip():
                return {"error": "Could not extract text from PDF"}
            
            # IMPROVED prompt - handles single name correctly
            prompt = f"""Extract data from this Noraxon EMG report.

PDF TEXT:
{pdf_text}

CRITICAL EXTRACTION RULES:

1. **Patient Name:**
   - Look for "First Name" field
   - If "Last Name" is empty or missing, use ONLY the first name
   - Example: If First Name="Amir" and Last Name="", then name="Amir" (NOT "Amir Amir")
   - Keep the original name exactly as written in the document

2. **Date of Birth:**
   - Look for "Date of Birth" field
   - Convert to YYYY-MM-DD format
   - Example: "1/27/2006" → "2006-01-27"

3. **Sex:**
   - Look for "Sex" field
   - Keep as "Male" or "Female"

4. **Test Date:**
   - Look for "Date Measured" field
   - Convert to YYYY-MM-DD
   - Example: "2/25/2024 12:53" → "2024-02-25"

5. **EMG Muscles** (from "Average Period" table):
   Extract Mean and Peak values for each muscle

Return ONLY this JSON (no markdown, no explanations):
{{
  "document_type": "emg",
  "patient_name": "FirstName" (NOT "FirstName FirstName"),
  "data": {{
    "name": "FirstName",
    "date_of_birth": "YYYY-MM-DD",
    "sex": "Male" or "Female",
    "test_date": "YYYY-MM-DD",
    "device": "Noraxon MyoMotion",
    "number_of_periods": number,
    "muscles": [
      {{
        "name": "RECTUS FEM. RT",
        "side": "Right",
        "mean_value": number,
        "peak_value": number
      }}
    ],
    "force_left_mean": number,
    "force_right_mean": number
  }}
}}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            print(f"Parsed Noraxon EMG: {result.get('patient_name', 'Unknown')}")
            return result
            
        except Exception as e:
            print(f"ERROR: Noraxon parsing error: {str(e)}")
            return {"error": f"Parsing failed: {str(e)}"}
    
    def parse_pdf_intelligently(self, pdf_path: str, document_type: str = "auto") -> Dict:
        """
        TRULY INTELLIGENT parser - reads ANY medical/rehabilitation document
        Figures out what it is, extracts ALL relevant data, no hard-coded rules
        ALL MEDICAL TEXT IN RUSSIAN
        """
        try:
            # Extract FULL text from ALL pages
            pdf_text = ""
            page_count = 0
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text + "\n\n"
            
            if not pdf_text.strip():
                return {"error": "Could not extract text from PDF"}
            
            print(f"📄 Reading {page_count}-page document ({len(pdf_text)} chars)")
            
            # INTELLIGENT extraction - Claude figures out everything IN RUSSIAN
            prompt = f"""You are an expert medical data extraction AI. Read this entire document and extract ALL useful rehabilitation/medical data.

**CRITICAL LANGUAGE INSTRUCTION:** 
- Document may be in Russian, Kazakh, or mixed Russian/Kazakh
- Extract ALL data regardless of which language it appears in
- Return ALL medical text in RUSSIAN language
- Only keep patient names in their original form
- If field is in Kazakh → translate to Russian
- If field is in Russian → keep as is
- Medical conditions → Russian (e.g., "Down syndrome" → "Синдром Дауна")
- Medications → Russian (e.g., "Sodium chloride" → "Натрия хлорид")
- Procedures → Russian (e.g., "Hydrotherapy" → "Гидротерапия")
- Specialist names → Russian (e.g., "Speech Therapist" → "Логопед", "Psychologist" → "Психолог")
- Recommendations → Russian
- All descriptive text → Russian
- Medical findings → Russian
- Progress descriptions → Russian

DOCUMENT ({page_count} pages):
{pdf_text[:15000]}

YOUR TASK:
1. Read and understand the ENTIRE document
2. Identify what type of document this is (discharge summary, assessment, test results, clinical notes, etc.)
3. Extract ALL relevant patient data, clinical measurements, assessments, therapies, diagnoses, recommendations
4. **Translate all medical/clinical text to RUSSIAN** (keep patient names in original form)
5. Structure it logically based on what you find

Return comprehensive JSON with ALL extracted data (medical text in Russian):
{{
  "document_type": "what kind of document is this?",
  "patient_info": {{
    "patient_id": "any ID found",
    "name": "patient name (keep original)",
    "date_of_birth": "YYYY-MM-DD",
    "sex": "Male/Female",
    "age": number,
    "admission_date": "YYYY-MM-DD if mentioned",
    "discharge_date": "YYYY-MM-DD if mentioned"
  }},
  "diagnoses": {{
    "primary": "главный диагноз (in Russian)",
    "icd_codes": ["all ICD codes found"],
    "secondary": ["другие диагнозы (in Russian)"],
    "full_diagnosis_text": "полный текст диагноза (in Russian)"
  }},
  "clinical_scores": {{
    "barthel_index": {{
      "admission": number (if present),
      "discharge": number (if present),
      "improvement": number
    }},
    "gmfcs_level": number (if mentioned),
    "macs_level": number (if mentioned),
    "any_other_scores": {{}},
    "rehabilitation_potential": number (if mentioned)
  }},
  "therapy_data": {{
    "Трудотерапия": number of sessions,
    "Физиотерапия": number of sessions,
    "Логопедия": number of sessions,
    "Музыкотерапия": number of sessions,
    "Психологическая терапия": number of sessions,
    "Игровая терапия": number of sessions,
    "Дефектология": number of sessions,
    "Гидротерапия": number of sessions,
    "other_therapies": {{}},
    "total_sessions": number
  }},
  "test_results": {{
    "emg_data": {{}},
    "balance_data": {{}},
    "clinical_tests": {{}},
    "lab_results": {{}},
    "imaging": {{}}
  }},
  "medications": ["все лекарства (in Russian)"],
  "procedures": ["все процедуры/лечения (in Russian)"],
  "specialist_assessments": {{
    "Психолог": "заключение психолога (in Russian)",
    "Логопед": "заключение логопеда (in Russian)",
    "Физиотерапевт": "заключение физиотерапевта (in Russian)",
    "Психиатр": "заключение психиатра (in Russian)",
    "Реабилитолог": "заключение реабилитолога (in Russian)",
    "any_other_specialists": {{}}
  }},
  "progress_dynamics": {{
    "motor_improvement": "описание улучшения моторики (in Russian)",
    "cognitive_improvement": "описание когнитивного улучшения (in Russian)",
    "speech_improvement": "описание улучшения речи (in Russian)",
    "overall_change": "улучшение/стабильно/ухудшение (in Russian)",
    "improvement_percentage": number (estimate)
  }},
  "recommendations": ["все рекомендации (in Russian)"],
  "follow_up": ["инструкции по наблюдению (in Russian)"],
  "clinical_summary": "краткое резюме состояния пациента (in Russian)"
}}

CRITICAL RULES:
- If a field doesn't exist in the document, use null (not empty string)
- Extract numbers from any language (55 баллов → 55, "180 meters" → 180)
- Count therapy sessions from any mention of sessions/занятие
- Be thorough - don't miss any clinical data
- ALL MEDICAL TEXT IN RUSSIAN (diagnoses, medications, procedures, findings, recommendations)
- Keep patient names in their original form
- Return ONLY valid JSON, no markdown, no explanations
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            # Log what was found
            doc_type = result.get('document_type', 'Unknown')
            patient_name = result.get('patient_info', {}).get('name', 'Unknown')
            print(f"✅ Extracted {doc_type}")
            print(f"   Patient: {patient_name}")
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {"error": f"Parsing failed: {str(e)}"}
    
    def parse_excel_intelligently(self, excel_path: str, batch_size: int = 20) -> Dict:
        """
        Parse Excel files with Russian medical text.

        FIXED: previously used `nrows=20`, which silently dropped every
        patient past row 20 with no warning. Now reads the ENTIRE sheet
        and processes it in batches of `batch_size` rows, so files with
        more than 20 patients are no longer truncated. Results from all
        batches are merged into a single patients list.
        """
        try:
            excel_file = pd.ExcelFile(excel_path)
            first_sheet = excel_file.sheet_names[0]

            # Read the FULL sheet — no row limit
            df = pd.read_excel(excel_path, sheet_name=first_sheet)
            total_rows = len(df)
            print(f"📊 Excel file has {total_rows} rows — processing in batches of {batch_size}")

            all_patients = []
            errors = []

            # Process in batches so each Claude call stays a reasonable size
            for start in range(0, total_rows, batch_size):
                end = min(start + batch_size, total_rows)
                batch_df = df.iloc[start:end]
                batch_num = (start // batch_size) + 1
                total_batches = (total_rows + batch_size - 1) // batch_size

                print(f"   Batch {batch_num}/{total_batches} (rows {start+1}-{end})...")

                excel_preview = f"Sheet: {first_sheet}\n\n{batch_df.to_string()}"

                prompt = f"""Extract patient rehabilitation data from this Excel file. Extract ALL available clinical test measurements, EMG data, and balance scores.

**LANGUAGE INSTRUCTION:** 
Extract all medical text in RUSSIAN (diagnoses, procedures, notes, etc.). 
Keep patient names in original form. 
Keep numerical values as-is.

{excel_preview}

Return JSON with this EXACT structure:
{{
  "patients": [
    {{
      "patient_id": "string (ID from excel)",
      "name": "string (original patient name)",
      "age": number,
      "height_cm": number,
      "weight_kg": number,
      "gmfcs_level": number (GMFCS level 1-5),
      "clinical_tests": {{
        "6mwt_distance_meters": number (6 minute walk test distance in meters, e.g., "180 meters" -> 180),
        "10mwt_time_seconds": number (10 meter walk test time in seconds, e.g., "10.32 sec" -> 10.32),
        "tug_time_seconds": number (Time Up and Go test in seconds, e.g., "32.30 sec" -> 32.30),
        "gmfm_score": number (GMFM percentage as number 0-100, e.g., "56.37%" -> 56.37),
        "who_qol_score": number (WHO Quality of Life score, e.g., 67),
        "omni_exertion_scale": number (OMNI exertion scale 0-10, e.g., 2),
        "modified_ashworth_scale": number (Modified Ashworth scale 0-4, e.g., 2),
        "berg_balance_scale": number (Berg Balance Scale 0-56, e.g., 44)
      }},
      "emg_data": {{
        "device": "string (EMG device name if present)"
      }}
    }}
  ]
}}

IMPORTANT: 
- Convert percentages to numbers (63.64% -> 63.64)
- Extract numbers from text (e.g., "180 meters" -> 180, "10.32 sec" -> 10.32)
- Keep patient names in original form (don't translate)
- Extract any medical terms/diagnoses in RUSSIAN if present
- Return ONLY the JSON, no explanation."""

                try:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    response_text = response.content[0].text
                    json_str = self._extract_json(response_text)
                    batch_result = json.loads(json_str)

                    batch_patients = batch_result.get('patients', [])
                    all_patients.extend(batch_patients)
                    print(f"   ✅ Batch {batch_num}: extracted {len(batch_patients)} patient(s)")

                except Exception as batch_error:
                    error_msg = f"Batch {batch_num} (rows {start+1}-{end}) failed: {str(batch_error)}"
                    print(f"   ⚠️ {error_msg}")
                    errors.append(error_msg)
                    continue  # keep processing remaining batches even if one fails

            print(f"Extracted {len(all_patients)} patients total from {total_rows} rows ({total_batches} batches)")

            result = {"patients": all_patients}
            if errors:
                result["batch_errors"] = errors
            return result

        except Exception as e:
            print(f"ERROR: Excel parsing error: {str(e)}")
            return {"patients": [], "error": str(e)}
    
    def generate_intelligent_assessment(self, patient_data: Dict, emg_data: Dict, 
                                       balance_data: Dict, clinical_data: Dict, language: str = "en") -> Dict:
        """Generate AI assessment with language support"""
        
        # Language-specific instructions
        language_instructions = {
            "en": "Generate a comprehensive rehabilitation assessment in ENGLISH.",
            "ru": """Создайте комплексную реабилитационную оценку ПОЛНОСТЬЮ на РУССКОМ ЯЗЫКЕ.

ОБЯЗАТЕЛЬНО на русском:
- Все медицинские термины
- Диагнозы и состояния
- Клинические выводы (clinical_insights)
- Рекомендации (recommendations)
- Ожидаемые результаты (expected_outcomes)
- Уровни риска (низкий/средний/высокий/критический)
- Степень тяжести (легкая/умеренная/тяжелая/глубокая)

НЕ ПЕРЕВОДИТЕ на английский. Весь текст должен быть на русском."""
        }
        
        language_prompt = language_instructions.get(language, language_instructions["en"])
        
        prompt = f"""{language_prompt}

PATIENT DATA:
{json.dumps(patient_data, indent=2)}

EMG DATA:
{json.dumps(emg_data, indent=2)}

BALANCE DATA:
{json.dumps(balance_data, indent=2)}

CLINICAL DATA:
{json.dumps(clinical_data, indent=2)}

IMPORTANT: 
- If language is "ru", respond ENTIRELY in Russian
- If language is "en", respond in English
- Current language: {language.upper()}

Generate a detailed assessment including:
1. disability_severity (mild/moderate/severe/profound or легкая/умеренная/тяжелая/глубокая)
2. disability_index (0-100)
3. motor_function_score (0-100)
4. balance_score (0-100)
5. fall_risk_level (low/medium/high/critical or низкий/средний/высокий/критический)
6. muscle_coordination_score (0-100)
7. gait_quality_score (0-100)
8. cognitive_score (0-100)
9. confidence_score (0.0-1.0)
10. clinical_insights (detailed text analysis in specified language)
11. recommendations (array of therapy recommendations in specified language)
12. expected_outcomes (rehabilitation goals and timeline in specified language)

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "disability_severity": "string",
  "disability_index": number,
  "motor_function_score": number,
  "balance_score": number,
  "fall_risk_level": "string",
  "muscle_coordination_score": number,
  "gait_quality_score": number,
  "cognitive_score": number,
  "confidence_score": number,
  "clinical_insights": "detailed text",
  "recommendations": ["recommendation1", "recommendation2"],
  "expected_outcomes": "expected results text"
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            print(f"Assessment generated in {language.upper()}")
            return result
            
        except Exception as e:
            print(f"ERROR: Assessment error: {str(e)}")
            return {"error": str(e)}
    
    def parse_rehabilitation_discharge_summary(self, pdf_path: str) -> Dict:
        """
        Parse comprehensive rehabilitation discharge summary PDFs
        Extracts ALL data from 15-24 page NCCR-style discharge summaries
        ALL MEDICAL TEXT IN RUSSIAN
        """
        try:
            # Extract FULL text from ALL pages
            pdf_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text + "\n\n"
            
            if not pdf_text.strip():
                return {"error": "Could not extract text from PDF"}
            
            print(f"📄 Discharge summary: {len(pdf_text)} characters, {len(pdf_text.split())} words")
            
            # Comprehensive extraction prompt
            prompt = f"""Extract ALL rehabilitation data from this discharge summary (Выписной эпикриз).

**MANDATORY LANGUAGE REQUIREMENT:**
ALL extracted medical text MUST be in RUSSIAN language:
- Diagnoses → Russian (Синдром Дауна, not Down syndrome)
- Medications → Russian (Натрия хлорид, not Sodium chloride)
- Procedures → Russian (Гидротерапия, not Hydrotherapy)
- Specialist assessments → Russian (Логопед, not Speech Therapist)
- Recommendations → Russian
- Progress descriptions → Russian
- Medical findings → Russian

Keep patient names in their ORIGINAL form.

FULL PDF TEXT:
{pdf_text[:15000]}

Extract EVERYTHING into this JSON structure. Be thorough:

{{
  "document_type": "rehabilitation_discharge_summary",
  "patient_info": {{
    "patient_id": "from document number or patient ID",
    "name": "full patient name (keep original)",
    "date_of_birth": "YYYY-MM-DD format",
    "sex": "Male or Female",
    "age_years": number,
    "home_address": "full address if present",
    "admission_date": "YYYY-MM-DD",
    "discharge_date": "YYYY-MM-DD",
    "length_of_stay_days": number
  }},
  "diagnoses": {{
    "primary_diagnosis": "главный диагноз с кодом МКБ (in Russian)",
    "primary_icd_code": "ICD-10 code",
    "secondary_diagnoses": ["список сопутствующих диагнозов (in Russian)"],
    "rehabilitation_diagnosis": "полный текст реабилитационного диагноза (in Russian)"
  }},
  "clinical_scores": {{
    "barthel_index_admission": number (0-100),
    "barthel_index_discharge": number (0-100),
    "barthel_improvement_percent": number,
    "macs_level": number (1-5 if present),
    "rehabilitation_potential_admission": number (0-4 scale),
    "rehabilitation_potential_discharge": number (0-4 scale),
    "rehabilitation_effectiveness": number (ratio),
    "gmfcs_level": number (if mentioned)
  }},
  "therapy_sessions": {{
    "occupational_therapy_sessions": number,
    "physical_therapy_sessions": number,
    "speech_therapy_sessions": number,
    "music_therapy_sessions": number,
    "play_therapy_sessions": number,
    "psychological_sessions": number,
    "defectology_sessions": number,
    "total_therapy_sessions": number
  }},
  "specialist_assessments": {{
    "psychologist_level": "уровень развития (высокий/средний/низкий) (in Russian)",
    "speech_therapist_level": "ОНР уровень (1-4) if present",
    "psychiatrist_diagnosis": "диагноз психиатра (in Russian)",
    "physiotherapist_recommendations": "рекомендации физиотерапевта (in Russian)"
  }},
  "lab_results": {{
    "hemoglobin": number (if present),
    "wbc": number (if present),
    "platelets": number (if present),
    "esr": number (if present)
  }},
  "medications": ["список всех назначенных лекарств (in Russian)"],
  "physiotherapy_procedures": ["список всех процедур (in Russian)"],
  "progress_dynamics": {{
    "motor_improvement": "описание прогресса моторики (in Russian)",
    "cognitive_improvement": "описание когнитивного прогресса (in Russian)",
    "speech_improvement": "описание прогресса речи (in Russian)",
    "behavior_improvement": "описание поведенческого прогресса (in Russian)",
    "overall_improvement_percent": number (estimated 0-100)
  }},
  "discharge_recommendations": ["полный список всех рекомендаций при выписке (in Russian)"],
  "discharge_status": "улучшение/стабильно/ухудшение (in Russian)",
  "follow_up_required": ["список инструкций по наблюдению (in Russian)"]
}}

CRITICAL INSTRUCTIONS:
- Extract numbers from Russian/Kazakh text (55 баллов → 55)
- Calculate improvement: (discharge_score - admission_score)
- Find Бартела/Barthel scores in both admission and discharge sections
- Count ALL therapy sessions mentioned (занятие проведено = 1 session)
- Extract ALL diagnoses with ICD codes (F84.0, G80.1, etc.)
- ALL MEDICAL TEXT IN RUSSIAN (except patient names which stay original)
- Return ONLY valid JSON, no markdown, no explanations"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,  # Increased for comprehensive data
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            patient_name = result.get('patient_info', {}).get('name', 'Unknown')
            print(f"✅ Parsed discharge summary for: {patient_name}")
            print(f"   Barthel: {result.get('clinical_scores', {}).get('barthel_index_admission')} → {result.get('clinical_scores', {}).get('barthel_index_discharge')}")
            print(f"   Therapy sessions: {result.get('therapy_sessions', {}).get('total_therapy_sessions', 0)}")
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR parsing discharge summary: {str(e)}")
            return {"error": f"Parsing failed: {str(e)}"}
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from response"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


# Global instance - CRITICAL!
claude_ai = ClaudeAI()