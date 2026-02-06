from __future__ import annotations
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict
import google.generativeai as genai


class GeminiConfigurationError(RuntimeError):
    """Raised when the Gemini client cannot be configured correctly."""


@lru_cache(maxsize=1)
def _load_job_roles() -> Dict[str, Any]:
    """Load job role definitions from the local JSON file."""
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "job_roles.json"

    if not data_path.exists():
        raise FileNotFoundError(f"job_roles.json not found at {data_path}")

    with data_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_job_roles() -> Dict[str, Any]:
    """Return the full job roles mapping."""
    return _load_job_roles()


def get_job_role_config(role_id: str) -> Dict[str, Any]:
    """Return configuration for a single job role, or a minimal default."""
    roles = _load_job_roles()
    if role_id in roles:
        return roles[role_id]

    # Fallback: treat unknown role id as a free-text label
    return {
        "label": role_id,
        "description": f"Candidate for role: {role_id}",
        "core_skills": [],
    }


@lru_cache(maxsize=1)
def _get_gemini_model() -> genai.GenerativeModel:
    """
    Configure and return a Gemini model instance.

    Expects GEMINI_API_KEY to be provided via environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY environment variable is not set. "
            "Set it to your Google Gemini API key before starting the backend."
        )

    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": 1,
        "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        generation_config=generation_config,
    )
    return model


def _build_prompt(resume_text: str, job_role_id: str) -> str:
    role_cfg = get_job_role_config(job_role_id)
    role_label = role_cfg.get("label", job_role_id)
    role_description = role_cfg.get("description", "")
    core_skills = role_cfg.get("core_skills", [])

    # The prompt is intentionally explicit, deterministic, and non-storytelling.
    # It requests a strict JSON structure and forbids hallucinating skills
    # that are not grounded in the resume text.
    prompt = f"""
You are an applicant tracking system (ATS) and HR specialist reviewing a candidate's resume.
Your task is to evaluate how well the candidate fits the target role in a professional, concise way.

ROLE INFORMATION
- Role identifier: {job_role_id}
- Role label: {role_label}
- Role description: {role_description}
- Core or expected skills for this role (reference list):
  {core_skills}

RESUME TEXT (VERBATIM, THE ONLY SOURCE OF TRUTH)
---------------- RESUME START ----------------
{resume_text}
----------------- RESUME END -----------------

STRICT ANALYSIS RULES
- Base ALL conclusions ONLY on the resume text above.
- Do NOT invent or hallucinate skills, experience, tools, or technologies that are not clearly present or strongly implied in the resume text.
- When deciding if a skill is "matched", it must be explicitly present or very clearly implied by the resume.
- When listing "missing_skills", only draw from the core skills list for the role. Do NOT introduce additional skills that are not in that list.
- Keep your tone professional and objective (ATS + HR hybrid).
- Do NOT use emojis.
- Do NOT tell a story. Focus on concrete, recruiter-grade evaluation.

REQUIRED OUTPUT FORMAT
- You MUST return a single JSON object only. No explanations, no prose before or after the JSON.
- The JSON object MUST have exactly these fields:
  - "skill_match_percentage": integer from 0 to 100 (no decimals).
  - "matched_skills": array of strings. Each string must be a skill that:
      (a) appears in the resume text, and
      (b) is relevant to the target role.
  - "missing_skills": array of strings. Each string must be drawn ONLY from the role core skills list above and MUST NOT appear in the resume text.
  - "strengths": array of short, bullet-style strings describing the strongest aspects of the resume for this role.
  - "improvement_suggestions": array of short, bullet-style strings with concrete suggestions to improve the resume for this role.
  - "final_verdict": one of exactly these strings:
      "Strong Fit", "Moderate Fit", or "Weak Fit".

JSON SCHEMA EXAMPLE (DO NOT COPY VALUES, ONLY THE STRUCTURE)
{{
  "skill_match_percentage": 72,
  "matched_skills": [
    "Python",
    "REST APIs"
  ],
  "missing_skills": [
    "Kubernetes",
    "Cloud (AWS)"
  ],
  "strengths": [
    "Clear experience building and maintaining backend services.",
    "Demonstrated ownership of end-to-end features."
  ],
  "improvement_suggestions": [
    "Quantify impact with metrics (e.g., latency reduction, cost savings).",
    "Highlight specific cloud platforms and tooling used."
  ],
  "final_verdict": "Moderate Fit"
}}

Now perform the analysis for the given resume and role.
Return ONLY the final JSON object, with no additional commentary.
"""
    return prompt.strip()


def analyze_resume_with_gemini(resume_text: str, job_role_id: str) -> Dict[str, Any]:
    """
    Analyze a resume for a specific job role using Gemini.

    Returns a Python dict parsed from the JSON response.
    """
    if not resume_text.strip():
        raise ValueError("Resume text is empty; cannot analyze.")

    model = _get_gemini_model()
    prompt = _build_prompt(resume_text=resume_text, job_role_id=job_role_id)

    response = model.generate_content(prompt)

    # The generation_config enforces application/json, but we still guard
    # against minor formatting issues by attempting to parse JSON.
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON from Gemini response: {exc}") from exc

