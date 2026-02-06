from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr

from services.resume_parser import (
    extract_text_from_pdf_bytes,
    extract_text_from_plain_bytes,
)
from services.gemini_analyzer import (
    analyze_resume_with_gemini,
    get_job_roles,
    GeminiConfigurationError,
)


class AnalysisResult(BaseModel):
    skill_match_percentage: int = Field(..., ge=0, le=100)
    matched_skills: List[str]
    missing_skills: List[str]
    strengths: List[str]
    improvement_suggestions: List[str]
    final_verdict: constr(pattern=r"^(Strong Fit|Moderate Fit|Weak Fit)$")  # type: ignore[call-arg]


class JobRole(BaseModel):
    id: str
    label: str
    description: str | None = None
    core_skills: List[str]


app = FastAPI(
    title="Resume Screening AI",
    description="Resume screening API powered by FastAPI, Gemini, and InsForge backend.",
    version="1.0.0",
)

# Allow Streamlit frontend and other clients to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/job-roles", response_model=List[JobRole])
def list_job_roles() -> List[JobRole]:
    """
    List available job roles and their core skills.

    The frontend can use this to populate a dropdown.
    """
    roles: Dict[str, Any] = get_job_roles()
    response: List[JobRole] = []
    for role_id, cfg in roles.items():
        response.append(
            JobRole(
                id=role_id,
                label=cfg.get("label", role_id),
                description=cfg.get("description") or None,
                core_skills=list(cfg.get("core_skills", []) or []),
            )
        )
    return response


def _normalize_analysis_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Gemini's JSON into a schema-safe payload for AnalysisResult.

    Gemini might sometimes return floats, different casing, or omit fields.
    This function makes the response robust while keeping the contract.
    """
    normalized: Dict[str, Any] = {}

    # skill_match_percentage: coerce to int and clamp [0, 100]
    raw_pct = raw.get("skill_match_percentage", 0)
    try:
        pct_int = int(round(float(raw_pct)))
    except (TypeError, ValueError):
        pct_int = 0
    pct_int = max(0, min(100, pct_int))
    normalized["skill_match_percentage"] = pct_int

    # List fields: always lists of strings
    def _as_str_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]

    normalized["matched_skills"] = _as_str_list(raw.get("matched_skills"))
    normalized["missing_skills"] = _as_str_list(raw.get("missing_skills"))
    normalized["strengths"] = _as_str_list(raw.get("strengths"))
    normalized["improvement_suggestions"] = _as_str_list(
        raw.get("improvement_suggestions")
    )

    # final_verdict: normalize to one of the allowed strings
    raw_verdict = str(raw.get("final_verdict", "") or "").strip().lower()
    if "strong" in raw_verdict:
        verdict = "Strong Fit"
    elif "moderate" in raw_verdict or "medium" in raw_verdict:
        verdict = "Moderate Fit"
    elif "weak" in raw_verdict or "low" in raw_verdict:
        verdict = "Weak Fit"
    else:
        # Default to Moderate Fit if unclear
        verdict = "Moderate Fit"
    normalized["final_verdict"] = verdict

    return normalized


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_resume(
    file: UploadFile = File(..., description="Resume file (PDF or plain text)."),
    job_role_id: str = Form(..., description="Target job role identifier."),
) -> AnalysisResult:
    """
    Analyze a resume for a given job role using Gemini.

    - Accepts a resume as a PDF or plain text file upload.
    - Uses Gemini to generate a structured JSON evaluation.
    """
    try:
        file_bytes = await file.read()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()

    if content_type == "application/pdf" or filename.endswith(".pdf"):
        try:
            resume_text = extract_text_from_pdf_bytes(file_bytes)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse PDF resume: {exc}",
            )
    else:
        resume_text = extract_text_from_plain_bytes(file_bytes)

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the resume. "
            "Please upload a PDF or text-based resume with readable content.",
        )

    try:
        analysis_dict_raw = analyze_resume_with_gemini(
            resume_text=resume_text,
            job_role_id=job_role_id,
        )
    except GeminiConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze resume with Gemini: {exc}",
        )

    try:
        normalized = _normalize_analysis_dict(analysis_dict_raw)
        return AnalysisResult(**normalized)
    except Exception as exc:
        # If Gemini returns something structurally unexpected, surface a clear error.
        raise HTTPException(
            status_code=500,
            detail=f"Gemini response did not match the expected schema: {exc}",
        )


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}

