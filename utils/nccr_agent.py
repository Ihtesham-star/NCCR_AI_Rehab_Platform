"""
NCCR LangGraph Agent - Multi-step intelligent document processing
"""
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from typing import TypedDict, Optional
import json
from config.settings import settings

# Initialize Claude through LangChain
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    api_key=settings.CLAUDE_API_KEY,
    max_tokens=2048
)

# State - this is the data that passes between all nodes
class PatientState(TypedDict):
    pdf_text: str                    # raw text from PDF
    patient_info: dict               # extracted basic info
    clinical_data: dict              # extracted clinical scores
    validation_errors: list          # any validation problems found
    assessment: dict                 # final assessment
    retry_count: int                 # how many times we retried
    status: str                      # current status

# ============ NODES ============

def extract_basic_info(state: PatientState) -> PatientState:
    """Node 1: Extract patient name, DOB, sex from PDF"""
    print("🔍 Node 1: Extracting basic patient info...")
    
    prompt = f"""Extract ONLY basic patient information from this medical document.

TEXT:
{state['pdf_text'][:3000]}

Return ONLY this JSON:
{{
    "name": "patient full name",
    "date_of_birth": "YYYY-MM-DD",
    "sex": "Male or Female",
    "patient_id": "any ID found or null"
}}

If a field is not found return null. Return ONLY valid JSON."""

    response = llm.invoke(prompt)
    
    try:
        text = response.content
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        patient_info = json.loads(text.strip())
        print(f"   Found: {patient_info.get('name', 'Unknown')}")
        return {**state, "patient_info": patient_info, "status": "basic_extracted"}
    except:
        return {**state, "patient_info": {}, "status": "basic_failed"}


def validate_basic_info(state: PatientState) -> str:
    """Conditional: Did we get minimum required info?"""
    info = state.get('patient_info', {})
    retry_count = state.get('retry_count', 0)
    
    # Need at least a name
    if info.get('name') and info['name'] != 'null':
        print("   ✅ Basic info validated")
        return "success"
    elif retry_count < 2:
        print(f"   ⚠️ Missing name - retry {retry_count + 1}")
        return "retry"
    else:
        print("   ❌ Could not extract name after retries")
        return "skip"


def retry_extraction(state: PatientState) -> PatientState:
    """Node: Retry with different prompt approach"""
    print("🔄 Retrying extraction with broader search...")
    retry_count = state.get('retry_count', 0)
    
    prompt = f"""This is a medical document. Find ANY person's name mentioned.

TEXT:
{state['pdf_text'][:2000]}

Return JSON:
{{"name": "any name you find", "date_of_birth": null, "sex": null, "patient_id": null}}"""

    response = llm.invoke(prompt)
    
    try:
        text = response.content
        if "```" in text:
            text = text.split("```")[1].split("```")[0]
            if text.startswith("json"):
                text = text[4:]
        patient_info = json.loads(text.strip())
        return {**state, "patient_info": patient_info, "retry_count": retry_count + 1}
    except:
        return {**state, "retry_count": retry_count + 1}


def extract_clinical_data(state: PatientState) -> PatientState:
    """Node 2: Extract clinical scores and therapy data"""
    print("🏥 Node 2: Extracting clinical data...")
    
    prompt = f"""Extract clinical rehabilitation data from this medical document.

TEXT:
{state['pdf_text'][:5000]}

Return ONLY this JSON:
{{
    "barthel_admission": number or null,
    "barthel_discharge": number or null,
    "gmfcs_level": number or null,
    "diagnosis": "main diagnosis in Russian or null",
    "therapy_sessions": {{"total": number or null}},
    "discharge_status": "improvement/stable/decline or null"
}}

Return ONLY valid JSON."""

    response = llm.invoke(prompt)
    
    try:
        text = response.content
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        clinical_data = json.loads(text.strip())
        print(f"   Barthel: {clinical_data.get('barthel_admission')} → {clinical_data.get('barthel_discharge')}")
        return {**state, "clinical_data": clinical_data, "status": "clinical_extracted"}
    except:
        return {**state, "clinical_data": {}, "status": "clinical_failed"}


def validate_clinical_data(state: PatientState) -> PatientState:
    """Node 3: Validate scores are medically reasonable"""
    print("✅ Node 3: Validating clinical data...")
    
    errors = []
    data = state.get('clinical_data', {})
    
    # Validate Barthel (0-100)
    barthel_adm = data.get('barthel_admission')
    barthel_dis = data.get('barthel_discharge')
    
    if barthel_adm is not None:
        if not (0 <= barthel_adm <= 100):
            errors.append(f"Invalid Barthel admission: {barthel_adm} (must be 0-100)")
    
    if barthel_dis is not None:
        if not (0 <= barthel_dis <= 100):
            errors.append(f"Invalid Barthel discharge: {barthel_dis} (must be 0-100)")
    
    # Validate GMFCS (1-5)
    gmfcs = data.get('gmfcs_level')
    if gmfcs is not None:
        if not (1 <= gmfcs <= 5):
            errors.append(f"Invalid GMFCS level: {gmfcs} (must be 1-5)")
    
    if errors:
        print(f"   ⚠️ Validation errors: {errors}")
    else:
        print("   ✅ All scores valid")
    
    return {**state, "validation_errors": errors, "status": "validated"}


def generate_final_assessment(state: PatientState) -> PatientState:
    """Node 4: Generate assessment from validated data"""
    print("🤖 Node 4: Generating final assessment...")
    
    patient = state.get('patient_info', {})
    clinical = state.get('clinical_data', {})
    errors = state.get('validation_errors', [])
    
    assessment = {
        "patient_name": patient.get('name'),
        "date_of_birth": patient.get('date_of_birth'),
        "diagnosis": clinical.get('diagnosis'),
        "barthel_admission": clinical.get('barthel_admission'),
        "barthel_discharge": clinical.get('barthel_discharge'),
        "gmfcs_level": clinical.get('gmfcs_level'),
        "therapy_total_sessions": clinical.get('therapy_sessions', {}).get('total'),
        "discharge_status": clinical.get('discharge_status'),
        "validation_warnings": errors,
        "processed_by": "LangGraph Agent v1.0"
    }
    
    # Calculate improvement if both Barthel scores exist
    if clinical.get('barthel_admission') and clinical.get('barthel_discharge'):
        improvement = clinical['barthel_discharge'] - clinical['barthel_admission']
        assessment['barthel_improvement'] = improvement
        assessment['improved'] = improvement > 0
    
    print(f"   ✅ Assessment complete for {patient.get('name', 'Unknown')}")
    return {**state, "assessment": assessment, "status": "complete"}


# ============ BUILD THE GRAPH ============

def build_nccr_agent():
    """Build and compile the LangGraph agent"""
    
    graph = StateGraph(PatientState)
    
    # Add nodes
    graph.add_node("extract_basic", extract_basic_info)
    graph.add_node("retry_extraction", retry_extraction)
    graph.add_node("extract_clinical", extract_clinical_data)
    graph.add_node("validate_clinical", validate_clinical_data)
    graph.add_node("generate_assessment", generate_final_assessment)
    
    # Set entry point
    graph.set_entry_point("extract_basic")
    
    # Add conditional edge after basic extraction
    graph.add_conditional_edges(
        "extract_basic",
        validate_basic_info,
        {
            "success": "extract_clinical",
            "retry": "retry_extraction",
            "skip": "extract_clinical"
        }
    )
    
    # After retry - go back to extract_basic
    graph.add_edge("retry_extraction", "extract_basic")
    
    # Linear flow after clinical extraction
    graph.add_edge("extract_clinical", "validate_clinical")
    graph.add_edge("validate_clinical", "generate_assessment")
    graph.add_edge("generate_assessment", END)
    
    return graph.compile()


# Global agent instance
nccr_agent = build_nccr_agent()


def process_document_with_agent(pdf_text: str) -> dict:
    """Main function to process a document through the agent"""
    
    initial_state = PatientState(
        pdf_text=pdf_text,
        patient_info={},
        clinical_data={},
        validation_errors=[],
        assessment={},
        retry_count=0,
        status="starting"
    )
    
    result = nccr_agent.invoke(initial_state)
    return result['assessment']