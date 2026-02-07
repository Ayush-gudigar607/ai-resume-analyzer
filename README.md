## Resume Screening AI (InsForge + FastAPI + Gemini)

Professional, ATS-style resume screening tool that analyzes resumes against predefined job roles using Google Gemini. The backend is built with FastAPI and can be deployed behind InsForge; the frontend is a lightweight Streamlit app.

### 📚 Documentation

For a detailed explanation of the codebase with comprehensive architecture diagrams, flow explanations, and component descriptions, see:

**[CODE_FLOW_DOCUMENTATION.md](./CODE_FLOW_DOCUMENTATION.md)** - Complete technical documentation with:
- System architecture diagrams
- Detailed code flow explanations
- Component breakdown and interactions
- API contracts and data models
- Configuration and deployment guides
- Error handling strategies
- Security and performance considerations

### Features

- **Resume upload**: PDF or plain-text resumes.
- **Job role selection**: Choose from predefined roles (e.g., Software Engineer, Backend Engineer, Data Scientist).
- **Gemini-powered analysis**:
  - Skill match percentage (0–100)
  - Matched skills
  - Missing skills (based only on configured core skills)
  - Resume strengths
  - Concrete improvement suggestions
  - Final verdict: **Strong Fit**, **Moderate Fit**, or **Weak Fit**
- **Strict JSON output**: Backend enforces JSON-only responses from Gemini.

### Project structure

```text
resume-screening-ai/
│
├── backend/
│   ├── main.py                  # FastAPI app (resume analysis API)
│   ├── services/
│   │   ├── resume_parser.py     # PDF/text extraction helpers
│   │   ├── gemini_analyzer.py   # Gemini prompt + analysis logic
│   ├── data/
│   │   └── job_roles.json       # Configured job roles and core skills
│   ├── requirements.txt         # Backend dependencies
│
├── frontend/
│   └── app.py                   # Streamlit UI
│
└── README.md
```

### Prerequisites

- Python 3.10+ recommended.
- A Google Gemini API key (for `google-generativeai`).
- (Optional) InsForge account if you plan to deploy the backend and/or frontend there.

### Environment variables

- **Backend**
  - **`GEMINI_API_KEY`**: Your Google Gemini API key. Required before starting the FastAPI app.

- **Frontend**
  - **`BACKEND_BASE_URL`** (optional): Base URL of the FastAPI backend.
    - Defaults to `http://localhost:8000`.
    - Example for InsForge or remote deployment: `https://your-backend-url.insforge.app`.

### Quick start (Windows + PowerShell + `.venv`)

From the `resume-screening-ai` folder, do the following.

1. **Create and activate `.venv`**

   ```bash
   cd "c:\Users\USER\Desktop\Resume Scrrening AI\resume-screening-ai"
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install backend requirements**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set Gemini API key (same terminal)**

   ```bash
   $env:GEMINI_API_KEY = "your_gemini_api_key_here"
   ```

4. **Start the backend (Terminal 1)**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

   Open in browser:
   - Backend API docs: `http://localhost:8000/docs`
   - Backend health: `http://localhost:8000/health`

5. **Start the frontend (Terminal 2)**

   Open a second PowerShell window:

   ```bash
   cd "c:\Users\USER\Desktop\Resume Scrrening AI\resume-screening-ai"
   .\.venv\Scripts\Activate.ps1
   streamlit run frontend/app.py
   ```

   Open in browser:
   - Streamlit UI: `http://localhost:8501`

### Backend setup (FastAPI + Gemini)

1. **Create and activate a virtual environment** (recommended):

   ```bash
   cd resume-screening-ai/backend
   python -m venv venv
   venv\Scripts\activate  # On Windows (PowerShell)
   # source venv/bin/activate  # On macOS/Linux
   ```

2. **Install backend dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set the Gemini API key**:

   ```bash
   # PowerShell
   $env:GEMINI_API_KEY = "your_gemini_api_key_here"

   # Bash (macOS/Linux)
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```

4. **Run the FastAPI server**:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Verify the backend**:

   - Health check: `GET http://localhost:8000/health`
   - Job roles: `GET http://localhost:8000/job-roles`
   - API docs: `http://localhost:8000/docs`

### Backend API contract

- **POST `/analyze`**
  - **Request**: `multipart/form-data`
    - **`file`**: Uploaded resume file (PDF or plain text).
    - **`job_role_id`**: Target job role identifier (e.g., `software_engineer`).
  - **Response**: JSON

    ```json
    {
      "skill_match_percentage": 72,
      "matched_skills": ["Python", "REST APIs"],
      "missing_skills": ["Kubernetes", "Cloud (AWS)"],
      "strengths": [
        "Clear experience building and maintaining backend services."
      ],
      "improvement_suggestions": [
        "Quantify impact with metrics (e.g., latency reduction, cost savings)."
      ],
      "final_verdict": "Moderate Fit"
    }
    ```

- **GET `/job-roles`**
  - Returns the configured job roles with `id`, `label`, `description`, and `core_skills`.

### Frontend setup (Streamlit)

You can use the same or a separate virtual environment for the frontend.

1. **Install frontend dependencies**:

   ```bash
   # From the project root or frontend folder
   pip install streamlit requests
   ```

2. **Point the frontend to your backend** (optional):

   ```bash
   # PowerShell
   $env:BACKEND_BASE_URL = "http://localhost:8000"

   # Or if deployed (example InsForge URL)
   $env:BACKEND_BASE_URL = "https://your-backend-url.insforge.app"
   ```

   If not set, the frontend defaults to `http://localhost:8000`.

3. **Run the Streamlit app**:

   ```bash
   cd resume-screening-ai
   streamlit run frontend/app.py
   ```

4. **Use the UI**:

   - Select a job role from the dropdown.
   - Upload a resume (PDF or text).
   - Click **“Analyze Resume”** to see:
     - Skill match percentage and verdict.
     - Matched and missing skills.
     - Strengths and improvement suggestions.

### InsForge integration notes

- This project is designed so the **FastAPI backend** can be hosted on InsForge (for example, via containers or functions), and the **Streamlit frontend** can be deployed as a static or containerized app.
- For database, authentication, storage, or additional AI endpoints, you can integrate InsForge services using their official SDKs and REST APIs as your needs grow.
- The core resume analysis pipeline itself uses **Google Gemini directly** via the `google-generativeai` Python package, as required.

### System design overview

At a high level the system is split into:

- **Frontend (Streamlit)**: Simple web UI for users.
- **Backend (FastAPI)**: API that parses resumes and talks to Gemini.
- **External AI (Gemini)**: Large language model that performs the actual analysis.

#### High-level architecture

```text
User Browser
   │
   │ HTTP (Streamlit)
   ▼
Streamlit App (`frontend/app.py`)
   │  - Renders UI
   │  - Lets user pick job role + upload resume
   │  - Calls backend /job-roles and /analyze
   │
   │ HTTP (JSON + multipart)
   ▼
FastAPI Backend (`backend/main.py`)
   │  - /job-roles: serves job_roles.json for dropdown
   │  - /analyze:
   │      * Reads uploaded file
   │      * Uses pdfplumber or text decoder
   │      * Calls Gemini analyzer service
   │      * Normalizes and returns JSON response
   │
   │ Function call
   ▼
Gemini Analyzer (`services/gemini_analyzer.py`)
   │  - Loads role config from job_roles.json
   │  - Builds strict prompt (no hallucinations, JSON only)
   │  - Calls Google Gemini via google-generativeai
   │  - Parses model JSON and returns dict
   │
   │ HTTPS (Gemini API)
   ▼
Google Gemini API
```

#### Request/response flow

1. **User action**
   - User opens Streamlit UI in browser.
   - Selects a job role and uploads a resume.
   - Clicks **“Analyze Resume”**.

2. **Frontend → Backend**
   - Streamlit sends a `POST /analyze` request to the FastAPI backend:
     - `multipart/form-data` with `file` (PDF/text) and `job_role_id`.

3. **Backend processing**
   - FastAPI endpoint:
     - Reads the uploaded file and detects file type.
     - Uses:
       - `resume_parser.extract_text_from_pdf_bytes` for PDFs, or
       - `resume_parser.extract_text_from_plain_bytes` for text.
     - Validates that some text was extracted.
     - Calls `analyze_resume_with_gemini(resume_text, job_role_id)`.

4. **Gemini analysis**
   - `gemini_analyzer`:
     - Loads the chosen role from `data/job_roles.json`.
     - Builds a structured, deterministic prompt with:
       - Role description + core skills.
       - Raw resume text as the only source of truth.
       - Instructions to return **only JSON** in a fixed schema.
     - Calls Google Gemini via `google-generativeai`.
     - Parses the JSON response into a Python `dict`.

5. **Backend response**
   - FastAPI normalizes the dict to match `AnalysisResult` (Pydantic model).
   - Returns a clean JSON object to the client.

6. **Frontend rendering**
   - Streamlit receives the JSON and renders:
     - Skill match percentage + progress bar.
     - Final verdict.
     - Matched / missing skills.
     - Strengths and improvement suggestions.

#### Where InsForge fits

- You can host **FastAPI** as your backend service behind InsForge.
- The Streamlit frontend can point at that InsForge backend via `BACKEND_BASE_URL`.
- If you later add persistence (e.g., saving analyses), InsForge’s database and auth SDKs can be integrated into the FastAPI layer without changing the frontend–Gemini contract.



1. Create and activate .venv (once)

cd "c:\Users\USER\Desktop\Resume Scrrening AI\resume-screening-ai"

# Create virtual env named .venv
python -m venv .venv

# Activate it (PowerShell)
.\.venv\Scripts\Activate.ps1

2. Install dependencies inside .venv


# Backend deps
cd backend
pip install -r requirements.txt

# Frontend deps
cd ..
pip install streamlit requests


3. Set your Gemini API key (backend)

$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

4. Run the FastAPI backend

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

5. Run the Streamlit frontend (web UI)


cd "c:\Users\USER\Desktop\Resume Scrrening AI\resume-screening-ai"
.\.venv\Scripts\Activate.ps1

streamlit run frontend/app.py

