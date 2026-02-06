from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import streamlit as st


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")


st.set_page_config(
    page_title="Resume Screening AI",
    page_icon="📄",
    layout="centered",
)

st.title("Resume Screening AI")
st.markdown(
    "Professional, ATS-style resume screening powered by Gemini and FastAPI."
)


@st.cache_data(show_spinner=False)
def fetch_job_roles() -> List[Dict[str, Any]]:
    """Fetch available job roles from the backend."""
    url = f"{BACKEND_BASE_URL}/job-roles"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def call_analyze_api(
    file_name: str,
    file_bytes: bytes,
    mime_type: str,
    job_role_id: str,
) -> Dict[str, Any]:
    """Call the backend /analyze endpoint."""
    url = f"{BACKEND_BASE_URL}/analyze"

    files = {
        "file": (file_name, file_bytes, mime_type or "application/octet-stream"),
    }
    data = {"job_role_id": job_role_id}

    resp = requests.post(url, files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    # Load job roles from backend
    try:
        roles = fetch_job_roles()
    except Exception as exc:
        st.error(
            "Could not load job roles from the backend. "
            "Please ensure the FastAPI backend is running and BACKEND_BASE_URL is correct."
        )
        st.caption(f"Details: {exc}")
        return

    if not roles:
        st.warning("No job roles are configured in the backend.")
        return

    # Build a mapping for the select box
    role_options = {role["label"]: role for role in roles}

    st.subheader("1. Select target job role")
    selected_label = st.selectbox(
        "Job role",
        options=list(role_options.keys()),
        help="Select the role you want to screen this resume against.",
    )
    selected_role = role_options[selected_label]

    with st.expander("View role details and expected skills", expanded=False):
        st.markdown(f"**Role ID:** `{selected_role['id']}`")
        if selected_role.get("description"):
            st.markdown(f"**Description:** {selected_role['description']}")
        core_skills = selected_role.get("core_skills") or []
        if core_skills:
            st.markdown("**Core skills for this role:**")
            st.write(", ".join(core_skills))

    st.subheader("2. Upload resume")
    uploaded_file = st.file_uploader(
        "Upload resume file (PDF or text)",
        type=["pdf", "txt", "text"],
        help="Upload a PDF or plain text resume. The content will be analyzed against the selected role.",
    )

    if uploaded_file is None:
        st.info("Please upload a resume file to continue.")
        return

    st.subheader("3. Run analysis")
    analyze_clicked = st.button("Analyze Resume", type="primary")

    if not analyze_clicked:
        return

    # Read file bytes
    file_bytes = uploaded_file.getvalue()
    if not file_bytes:
        st.error("The uploaded file is empty.")
        return

    with st.spinner("Analyzing resume with Gemini..."):
        try:
            result = call_analyze_api(
                file_name=uploaded_file.name,
                file_bytes=file_bytes,
                mime_type=uploaded_file.type or "",
                job_role_id=selected_role["id"],
            )
        except requests.HTTPError as http_err:
            # Try to surface backend error details if present
            try:
                detail = http_err.response.json()
            except Exception:
                detail = http_err.response.text if http_err.response is not None else str(http_err)
            st.error("Backend returned an error while analyzing the resume.")
            st.caption(f"Details: {detail}")
            return
        except Exception as exc:  # pragma: no cover - defensive
            st.error("Unexpected error while contacting the backend.")
            st.caption(f"Details: {exc}")
            return

    # Display results
    st.subheader("Analysis Result")

    # High-level metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Skill Match Percentage",
            value=f"{result.get('skill_match_percentage', 0)}%",
        )
    with col2:
        st.metric(
            label="Final Verdict",
            value=result.get("final_verdict", "N/A"),
        )

    st.progress(min(max(int(result.get("skill_match_percentage", 0)), 0), 100) / 100.0)

    # Skills overview
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Matched skills**")
        matched_skills = result.get("matched_skills") or []
        if matched_skills:
            for skill in matched_skills:
                st.write(f"- {skill}")
        else:
            st.write("_No matched skills detected in the resume for this role._")

    with col_right:
        st.markdown("**Missing skills (based on role core skills)**")
        missing_skills = result.get("missing_skills") or []
        if missing_skills:
            for skill in missing_skills:
                st.write(f"- {skill}")
        else:
            st.write("_No missing skills from the configured core skills list._")

    st.markdown("---")

    st.markdown("**Resume strengths**")
    strengths = result.get("strengths") or []
    if strengths:
        for s in strengths:
            st.write(f"- {s}")
    else:
        st.write("_No strengths were returned by the model._")

    st.markdown("**Improvement suggestions**")
    suggestions = result.get("improvement_suggestions") or []
    if suggestions:
        for s in suggestions:
            st.write(f"- {s}")
    else:
        st.write("_No improvement suggestions were returned by the model._")


if __name__ == "__main__":
    main()

