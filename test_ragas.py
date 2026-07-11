"""
RAGAS Evaluation for NCCR RAG System
"""
import numpy as np
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision
from ragas.llms import LangchainLLMWrapper
from langchain_anthropic import ChatAnthropic
from datasets import Dataset

from database.connection import SessionLocal
from database.models import Patient
from utils.rag_engine import search_chunks
from utils.claude_ai import claude_ai
from config.settings import settings

# --- Setup RAGAS evaluator LLM with Anthropic via LangChain wrapper ---
# NOTE 1: only `temperature` is set here. Do NOT also pass top_p — Claude
#   Sonnet 4.5+ rejects requests that specify both.
# NOTE 2: max_tokens is raised to 4096. At 1024, some Faithfulness statement
#   generations got cut off mid-JSON, causing LLMDidNotFinishException.
ragas_llm = LangchainLLMWrapper(
    ChatAnthropic(
        model="claude-sonnet-4-5",
        anthropic_api_key=settings.CLAUDE_API_KEY,
        temperature=0.0,
        max_tokens=4096,
    )
)

# Universal questions
test_questions = [
    "What is the main diagnosis of this patient?",
    "What medications were prescribed?",
    "What specialist assessments were completed?",
    "What are the rehabilitation recommendations?",
    "What was the discharge outcome?"
]

patient_db_ids = [2, 3, 4, 5, 6, 7]

questions = []
answers = []
contexts = []
ground_truths = []

db = SessionLocal()
print("Running RAG evaluation across all patients...")

for patient_id in patient_db_ids:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        continue

    print(f"Evaluating patient {patient.patient_id}...")

    for question in test_questions:
        chunks = search_chunks(db, query=question, patient_id=patient_id, top_k=3)

        if not chunks:
            continue

        context = [c['chunk_text'] for c in chunks]
        context_text = "\n\n".join(context)

        prompt = f"""Answer this question using ONLY the provided context. Be concise.

Context:
{context_text}

Question: {question}
Answer:"""

        try:
            response = claude_ai.client.messages.create(
                model=claude_ai.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.content[0].text.strip()
        except Exception as e:
            print(f"Error: {e}")
            continue

        questions.append(question)
        answers.append(answer)
        contexts.append(context)
        ground_truths.append("Information extracted from patient medical document")

        print(f"  Q: {question[:50]}...")
        print(f"  A: {answer[:80]}...")
        print()

db.close()

print(f"\nCollected {len(questions)} QA pairs")
print("Calculating RAGAS scores...\n")

dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths
})

# Use sentence-transformers for embeddings — no OpenAI needed
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper

hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
ragas_embeddings = LangchainEmbeddingsWrapper(hf_embeddings)

results = evaluate(
    dataset=dataset,
    metrics=[
        Faithfulness(llm=ragas_llm),
        AnswerRelevancy(llm=ragas_llm),
        ContextPrecision(llm=ragas_llm)
    ],
    embeddings=ragas_embeddings
)


def safe_mean(value):
    """
    Handle both scalar and per-row list results. Some ragas versions return
    a single float per metric; others return a list of per-row scores
    (with NaN for rows where the LLM call failed, e.g. LLMDidNotFinishException).
    This normalizes both cases into a single float.
    """
    if isinstance(value, (list, tuple)):
        arr = np.array(value, dtype=float)
        return float(np.nanmean(arr))
    return float(value)


faithfulness = safe_mean(results['faithfulness'])
answer_relevancy = safe_mean(results['answer_relevancy'])
context_precision = safe_mean(results['context_precision'])

print("\n" + "="*40)
print("RAGAS EVALUATION RESULTS")
print("="*40)
print(f"Faithfulness:      {faithfulness:.3f}")
print(f"Answer Relevancy:  {answer_relevancy:.3f}")
print(f"Context Precision: {context_precision:.3f}")

overall = (faithfulness + answer_relevancy + context_precision) / 3
print(f"\nOverall RAG Quality: {overall:.3f}")
print("="*40)