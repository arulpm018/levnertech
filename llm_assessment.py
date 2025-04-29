# llm_assessment.py

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI
from utils import score_to_verdict

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com", 
)

def safe_load_json(content: str, context: str) -> Any:
    """
    Strip markdown fences, ensure non-empty, then parse JSON.
    Raises a clear ValueError if parsing fails.
    """
    s = content.strip()
    if s.startswith("```"):
        s = s.lstrip("```").lstrip("json").rstrip("```").strip()
    if not s:
        raise ValueError(f"[safe_load_json] Empty response for context:\n{context!r}")
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError(f"[safe_load_json] JSONDecodeError for context {context!r}: {e}\nContent was:\n{s!r}")

CLAUSE_DESCRIPTIONS = {
    "4.1": "Understanding the organization and its context requires identifying external and internal issues relevant to the organization's purpose that affect its ability to achieve intended ISMS outcomes.",
    "4.2": "Understanding the needs and expectations of interested parties requires determining relevant stakeholders and their requirements.",
    "4.3": "Determining the scope of the ISMS requires defining its boundaries and applicability.",
    "4.4": "The ISMS must be established, implemented, maintained and continually improved in accordance with ISO 27001."
}


def analyze_uploaded_evidence(
    clause_id: str,
    document_text: str
) -> Dict[str, Any]:
    clause_desc = CLAUSE_DESCRIPTIONS.get(clause_id, f"ISO 27001 Clause {clause_id}")
    # truncate if too long
    if len(document_text) > 6000:
        document_text = document_text[:6000] + "..."

    system_prompt = """
You are an ISO 27001 compliance auditor specializing in document review.
Your task is to evaluate the provided document content based on the given ISO clause.

**IMPORTANT:** Respond ONLY with a JSON object following this format, without any additional explanation:
{
  "compliance_level": "<High|Medium|Low>",
  "matched_requirements": [<list of addressed requirements>],
  "missing_requirements": [<list of missing requirements>],
  "suggestions": [<list of improvement suggestions>],
  "overall_assessment": "<concise summary>"
}
Make sure your JSON is syntactically valid.
"""


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Clause {clause_id}: {clause_desc}"},
        {"role": "user", "content": f"Document content:\n\n{document_text}"}
    ]

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0,
            max_tokens=800,
            stream=False
        )
        raw = resp.choices[0].message.content or ""
        print(f"[DEBUG] analyze_uploaded_evidence raw response for {clause_id!r}:\n{raw!r}")
        return safe_load_json(raw, f"analyze_uploaded_evidence({clause_id})")
    except Exception as e:
        # Let the exception bubble so you see it in Streamlit logs
        raise RuntimeError(f"[analyze_uploaded_evidence] {e}")


def evaluate_open_text_compliance(
    clause_id: str,
    user_response: str,
    document_context: Optional[str] = None
) -> Tuple[str, Dict[str, float], str]:
    clause_desc = CLAUSE_DESCRIPTIONS.get(clause_id, f"ISO 27001 Clause {clause_id}")

    if not user_response or not user_response.strip():
        return "Major NC", {"relevance": 0.0, "completeness": 0.0}, "No response provided"

    if len(user_response) > 4000:
        user_response = user_response[:4000] + "..."

    system_prompt = """
You are an ISO 27001 auditor assessing a user's open-ended answer.

Evaluate the response for relevance and completeness regarding the given clause.

**IMPORTANT:** Output ONLY a valid JSON object using this exact schema:
{
  "scores": {
    "relevance": <0.0-1.0>,
    "completeness": <0.0-1.0>
  },
  "verdict": "Complied|Minor NC|Opportunity for Improvement|Major NC",
  "feedback": "<detailed constructive feedback>"
}

Do not add any explanation or notes. Ensure the JSON is valid and fully populated.
"""


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Clause {clause_id}: {clause_desc}"},
        {"role": "user", "content": f"User response:\n\n{user_response}"}
    ]
    if document_context:
        messages.append({"role": "user", "content": f"Supporting docs:\n\n{document_context}"})

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0,
            max_tokens=800,
            stream=False
        )
        raw = resp.choices[0].message.content or ""
        print(f"[DEBUG] evaluate_open_text_compliance raw for {clause_id!r}:\n{raw!r}")
        result = safe_load_json(raw, f"evaluate_open_text_compliance({clause_id})")
        scores = result.get("scores", {})
        verdict = result.get("verdict") or score_to_verdict(
            scores.get("relevance",0), scores.get("completeness",0)
        )
        feedback = result.get("feedback", "")
        return verdict, scores, feedback
    except Exception as e:
        # Fail loudly so you see the real error
        raise RuntimeError(f"[evaluate_open_text_compliance] {e}")


def generate_detailed_recommendations(
    assessment_results: List[Dict[str, Any]],
    organization_context: Optional[str] = None
) -> Dict[str, Any]:
    formatted = json.dumps(assessment_results, indent=2)
    context_prompt = f"Organization context:\n{organization_context}\n\n" if organization_context else ""
    system_prompt = """
You are an ISO 27001 consultant reviewing an organization's overall gap assessment results.

Based on the provided data, generate improvement strategies and actionable recommendations.

**IMPORTANT:** Respond ONLY with a valid JSON object using this schema:
{
  "priority_actions": [...],
  "recommendations_by_clause": {...},
  "implementation_strategy": "...",
  "areas_of_strength": [...]
}

No explanations outside the JSON output. Make sure the JSON is properly formatted and complete.
"""


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context_prompt + "Assessment results:\n" + formatted}
    ]

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0,
            max_tokens=800,
            stream=False
        )
        raw = resp.choices[0].message.content or ""
        print(f"[DEBUG] generate_detailed_recommendations raw:\n{raw!r}")
        return safe_load_json(raw, "generate_detailed_recommendations")
    except Exception as e:
        raise RuntimeError(f"[generate_detailed_recommendations] {e}")


def ai_assistant_response(
    user_query: str,
    clause_context: Optional[str] = None
) -> str:
    context = f"Regarding clause: {clause_context}\n\n" if clause_context else ""
    system_prompt = """
You are an ISO 27001 virtual assistant.

Provide practical, concise advice in natural language to answer user questions.
Whenever relevant, cite ISO clause numbers (e.g., "Refer to Clause 4.1.").

**IMPORTANT:** Respond in plain text only (no JSON), and avoid unnecessary verbosity.
Focus on clarity, relevance, and actionable guidance.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context + "User question: " + user_query}
    ]

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0,
            max_tokens=500,
            stream=False
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"I'm sorry, I can't process that right now: {e}"
