# AI Resume Analyzer - Code Flow Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Breakdown](#component-breakdown)
4. [Detailed Code Flow](#detailed-code-flow)
5. [API Contracts](#api-contracts)
6. [Data Models](#data-models)
7. [Configuration](#configuration)
8. [Error Handling](#error-handling)

---

## System Overview

The AI Resume Analyzer is a full-stack application that uses Google's Gemini AI to analyze resumes against predefined job roles. The system consists of:

- **Frontend**: Streamlit-based web UI for user interaction
- **Backend**: FastAPI REST API for processing and orchestration
- **AI Service**: Google Gemini for intelligent resume analysis
- **Data Store**: JSON configuration file for job role definitions

### Key Features
- Upload resumes in PDF or plain text format
- Select from multiple predefined job roles
- AI-powered analysis with skill matching
- Professional ATS-style feedback
- JSON-enforced structured responses from Gemini

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP (localhost:8501)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                         │
│                     frontend/app.py                             │
│                                                                 │
│  Features:                                                      │
│  • Fetches job roles from backend                              │
│  • Displays job role selection dropdown                        │
│  • Handles file upload (PDF/TXT)                               │
│  • Calls /analyze endpoint                                     │
│  • Renders analysis results with visualizations                │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP/JSON (localhost:8000)
                                │ GET /job-roles
                                │ POST /analyze (multipart/form-data)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                           │
│                      backend/main.py                            │
│                                                                 │
│  Endpoints:                                                     │
│  • GET /health          → Health check                         │
│  • GET /job-roles       → Returns available job roles          │
│  • POST /analyze        → Resume analysis endpoint             │
│                                                                 │
│  Processing Flow:                                               │
│  1. Receives uploaded file                                     │
│  2. Determines file type (PDF/TXT)                             │
│  3. Calls appropriate parser                                   │
│  4. Validates extracted text                                   │
│  5. Calls Gemini analyzer service                              │
│  6. Normalizes response                                        │
│  7. Returns structured JSON                                    │
│                                                                 │
└───┬──────────────────────┬──────────────────────┬──────────────┘
    │                      │                      │
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐      ┌──────────────────┐   ┌────────────────────┐
│ Resume  │      │ Gemini Analyzer  │   │  Job Roles Data   │
│ Parser  │      │   Service        │   │                    │
│         │      │                  │   │ data/              │
│ services│      │ services/        │   │ job_roles.json     │
│ /resume_│      │ gemini_analyzer  │   │                    │
│ parser  │      │ .py              │   │ Cached in memory   │
│ .py     │      │                  │   │ (@lru_cache)       │
│         │      │ • Loads role cfg │   │                    │
│ • PDF   │      │ • Builds prompt  │   │ Defines:           │
│   via   │      │ • Calls Gemini   │   │ • Role IDs         │
│   pdfpl-│      │ • Parses JSON    │   │ • Labels           │
│   umber │      │   response       │   │ • Descriptions     │
│ • Plain │      │                  │   │ • Core skills      │
│   text  │      └────────┬─────────┘   └────────────────────┘
│   via   │               │
│   decode│               │ API Call (HTTPS)
└─────────┘               ▼
              ┌────────────────────────┐
              │   GOOGLE GEMINI API    │
              │                        │
              │ Model: gemini-2.5-     │
              │        flash-lite      │
              │                        │
              │ Config:                │
              │ • temperature: 0.0     │
              │ • response_mime_type:  │
              │   "application/json"   │
              │                        │
              │ Returns structured     │
              │ JSON with:             │
              │ • Skill match %        │
              │ • Matched skills       │
              │ • Missing skills       │
              │ • Strengths            │
              │ • Suggestions          │
              │ • Final verdict        │
              └────────────────────────┘
```

---

## Component Breakdown

### 1. Frontend (`frontend/app.py`)

**Purpose**: Provides user interface for resume screening

**Key Functions**:

```python
fetch_job_roles()
├─ Makes GET request to /job-roles endpoint
├─ Caches results with @st.cache_data
└─ Returns list of available job roles

call_analyze_api(file_name, file_bytes, mime_type, job_role_id)
├─ Makes POST request to /analyze endpoint
├─ Sends multipart form data (file + job_role_id)
├─ Waits up to 60 seconds for response
└─ Returns analysis result JSON

main()
├─ Fetches and displays job roles
├─ Renders job role selector
├─ Handles file upload
├─ Triggers analysis on button click
└─ Displays results with metrics and visualizations
```

**User Flow**:
1. User opens Streamlit UI in browser
2. App fetches available job roles from backend
3. User selects target job role from dropdown
4. User uploads resume file (PDF or TXT)
5. User clicks "Analyze Resume" button
6. App sends request to backend
7. App displays analysis results with visualizations

### 2. Backend API (`backend/main.py`)

**Purpose**: REST API for processing resumes and orchestrating analysis

**Models**:

```python
AnalysisResult (Pydantic Model)
├─ skill_match_percentage: int (0-100)
├─ matched_skills: List[str]
├─ missing_skills: List[str]
├─ strengths: List[str]
├─ improvement_suggestions: List[str]
└─ final_verdict: "Strong Fit" | "Moderate Fit" | "Weak Fit"

JobRole (Pydantic Model)
├─ id: str
├─ label: str
├─ description: str | None
└─ core_skills: List[str]
```

**Endpoints**:

```python
GET /health
├─ Returns {"status": "ok"}
└─ Used for health checks

GET /job-roles
├─ Calls get_job_roles() from gemini_analyzer
├─ Transforms dict to list of JobRole objects
└─ Returns List[JobRole]

POST /analyze
├─ Accepts file (multipart/form-data) + job_role_id
├─ Reads file bytes
├─ Determines file type
├─ Calls appropriate parser
│  ├─ PDF → extract_text_from_pdf_bytes()
│  └─ TXT → extract_text_from_plain_bytes()
├─ Validates text extraction
├─ Calls analyze_resume_with_gemini()
├─ Normalizes response via _normalize_analysis_dict()
└─ Returns AnalysisResult
```

**Key Function - _normalize_analysis_dict()**:
- Ensures Gemini's response matches expected schema
- Coerces skill_match_percentage to int (0-100)
- Converts all list fields to List[str]
- Normalizes final_verdict to exact match

### 3. Resume Parser (`backend/services/resume_parser.py`)

**Purpose**: Extract text from different file formats

**Functions**:

```python
extract_text_from_pdf_bytes(file_bytes: bytes) → str
├─ Uses pdfplumber library
├─ Opens PDF from BytesIO buffer
├─ Iterates through all pages
├─ Extracts text from each page
├─ Joins pages with double newlines
└─ Returns concatenated text

extract_text_from_plain_bytes(file_bytes: bytes) → str
├─ Decodes bytes to string (UTF-8)
├─ Uses errors="ignore" for robustness
└─ Returns decoded text
```

### 4. Gemini Analyzer (`backend/services/gemini_analyzer.py`)

**Purpose**: Interface with Google Gemini for AI-powered analysis

**Key Functions**:

```python
_load_job_roles() [Cached]
├─ Locates job_roles.json file
├─ Loads and parses JSON
├─ Caches result with @lru_cache
└─ Returns Dict[str, Any]

get_job_roles() → Dict[str, Any]
└─ Returns cached job roles dictionary

get_job_role_config(role_id: str) → Dict[str, Any]
├─ Loads job roles
├─ Looks up specific role by ID
├─ Returns role config or fallback
└─ Fallback: minimal config with role_id as label

_get_gemini_model() [Cached]
├─ Reads GEMINI_API_KEY from environment
├─ Configures genai with API key
├─ Sets generation config:
│  ├─ temperature: 0.0 (deterministic)
│  ├─ top_p: 1.0
│  ├─ top_k: 1
│  └─ response_mime_type: "application/json"
├─ Creates GenerativeModel instance
└─ Returns model (cached for reuse)

_build_prompt(resume_text: str, job_role_id: str) → str
├─ Loads role configuration
├─ Extracts role label, description, core_skills
├─ Builds comprehensive prompt with:
│  ├─ Role information
│  ├─ Resume text (verbatim)
│  ├─ Strict analysis rules
│  ├─ Required output format (JSON schema)
│  └─ Example structure
└─ Returns formatted prompt string

analyze_resume_with_gemini(resume_text, job_role_id) → Dict
├─ Validates resume_text is not empty
├─ Gets Gemini model instance
├─ Builds prompt for analysis
├─ Calls model.generate_content(prompt)
├─ Extracts response text
├─ Parses JSON from response
└─ Returns analysis dictionary
```

**Prompt Strategy**:
- **Deterministic**: Uses temperature=0.0 for consistent results
- **Grounded**: Instructs model to use ONLY resume text
- **Structured**: Enforces JSON-only output
- **Professional**: ATS-style evaluation tone
- **No hallucinations**: Explicitly forbids inventing skills

### 5. Data Configuration (`backend/data/job_roles.json`)

**Purpose**: Defines job roles and their core skills

**Structure**:
```json
{
  "role_id": {
    "label": "Display Name",
    "description": "Role description",
    "core_skills": ["Skill1", "Skill2", ...]
  }
}
```

**Predefined Roles**:
- `software_engineer`: Generalist full-stack engineer
- `backend_engineer`: Server-side APIs and services
- `frontend_engineer`: Web UI development
- `data_scientist`: ML and analytics
- `product_manager`: Product strategy and execution

---

## Detailed Code Flow

### Flow 1: Application Startup

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User starts backend (uvicorn main:app)                  │
│    ├─ FastAPI app initializes                              │
│    ├─ CORS middleware configured                           │
│    ├─ Gemini model NOT initialized yet (lazy load)         │
│    └─ Endpoints registered: /health, /job-roles, /analyze  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. User starts frontend (streamlit run frontend/app.py)    │
│    ├─ Streamlit app loads                                  │
│    ├─ BACKEND_BASE_URL read from env (default: localhost)  │
│    ├─ Page configured with title and icon                  │
│    └─ main() function executes                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Frontend calls GET /job-roles                           │
│    ├─ Request sent to backend                              │
│    ├─ Backend loads job_roles.json (cached)               │
│    ├─ Transforms to JobRole list                           │
│    ├─ Returns JSON response                                │
│    └─ Frontend caches result                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. UI rendered with job role dropdown                      │
│    └─ Waiting for user interaction                         │
└─────────────────────────────────────────────────────────────┘
```

### Flow 2: Resume Analysis Request

```
┌─────────────────────────────────────────────────────────────┐
│ USER ACTION: Selects job role + uploads resume + clicks    │
│              "Analyze Resume" button                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (app.py)                                           │
│ ═══════════════════════════════════════════════════════════ │
│ call_analyze_api()                                          │
│ ├─ Reads file bytes from uploaded_file.getvalue()          │
│ ├─ Prepares multipart/form-data:                           │
│ │  ├─ file: (filename, bytes, mime_type)                   │
│ │  └─ job_role_id: selected role ID                        │
│ ├─ POST to /analyze endpoint                               │
│ └─ Waits for response (timeout: 60s)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (main.py)                                           │
│ ═══════════════════════════════════════════════════════════ │
│ @app.post("/analyze")                                       │
│                                                             │
│ Step 1: Receive and validate upload                        │
│ ├─ await file.read() → file_bytes                          │
│ ├─ Check if file_bytes is not empty                        │
│ └─ Extract content_type and filename                       │
│                                                             │
│ Step 2: Determine file type and parse                      │
│ ├─ If PDF (by content_type or extension):                  │
│ │  └─ extract_text_from_pdf_bytes(file_bytes)              │
│ └─ Else (plain text):                                      │
│    └─ extract_text_from_plain_bytes(file_bytes)            │
│                                                             │
│ Step 3: Validate text extraction                           │
│ └─ Check if resume_text.strip() is not empty               │
│                                                             │
│ Step 4: Call Gemini analyzer                               │
│ └─ analyze_resume_with_gemini(resume_text, job_role_id)    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ RESUME PARSER (resume_parser.py)                           │
│ ═══════════════════════════════════════════════════════════ │
│                                                             │
│ For PDF files:                                              │
│ extract_text_from_pdf_bytes()                               │
│ ├─ Create BytesIO buffer from file_bytes                   │
│ ├─ Open PDF with pdfplumber                                │
│ ├─ For each page in PDF:                                   │
│ │  ├─ Extract text with page.extract_text()                │
│ │  ├─ Strip whitespace                                     │
│ │  └─ Add to text_chunks list                              │
│ ├─ Join all chunks with "\n\n"                             │
│ └─ Return complete resume text                             │
│                                                             │
│ For text files:                                             │
│ extract_text_from_plain_bytes()                             │
│ ├─ Decode bytes as UTF-8                                   │
│ ├─ Use errors="ignore" for robustness                      │
│ └─ Return decoded text                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GEMINI ANALYZER (gemini_analyzer.py)                       │
│ ═══════════════════════════════════════════════════════════ │
│ analyze_resume_with_gemini()                                │
│                                                             │
│ Step 1: Validate input                                     │
│ └─ Check resume_text.strip() is not empty                  │
│                                                             │
│ Step 2: Get Gemini model (lazy initialization)             │
│ _get_gemini_model() [First call]                           │
│ ├─ Read GEMINI_API_KEY from environment                    │
│ ├─ Raise GeminiConfigurationError if missing              │
│ ├─ Configure genai.configure(api_key=api_key)             │
│ ├─ Set generation_config:                                  │
│ │  ├─ temperature: 0.0 (deterministic)                     │
│ │  ├─ top_p: 1.0                                           │
│ │  ├─ top_k: 1                                             │
│ │  └─ response_mime_type: "application/json"               │
│ ├─ Create genai.GenerativeModel instance                   │
│ ├─ Cache result with @lru_cache                            │
│ └─ Return model                                            │
│                                                             │
│ Step 3: Build analysis prompt                              │
│ _build_prompt(resume_text, job_role_id)                    │
│ ├─ get_job_role_config(job_role_id)                        │
│ │  ├─ _load_job_roles() [cached]                           │
│ │  └─ Return role config or fallback                       │
│ ├─ Extract: label, description, core_skills                │
│ └─ Build comprehensive prompt with:                        │
│    ├─ Role information section                             │
│    ├─ Resume text (verbatim, marked as source of truth)    │
│    ├─ Strict analysis rules:                               │
│    │  ├─ Base conclusions ONLY on resume text              │
│    │  ├─ No hallucinations                                 │
│    │  ├─ Professional ATS tone                             │
│    │  └─ No emojis or storytelling                         │
│    ├─ Required output format (JSON schema)                 │
│    └─ Example structure                                    │
│                                                             │
│ Step 4: Call Gemini API                                    │
│ ├─ model.generate_content(prompt)                          │
│ ├─ Wait for response (synchronous)                         │
│ └─ Extract response.text                                   │
│                                                             │
│ Step 5: Parse JSON response                                │
│ ├─ Strip whitespace from response text                     │
│ ├─ Check for empty response                                │
│ ├─ json.loads(text)                                        │
│ └─ Return parsed dictionary                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GOOGLE GEMINI API                                           │
│ ═══════════════════════════════════════════════════════════ │
│ Model: gemini-2.5-flash-lite                                │
│                                                             │
│ Processing:                                                 │
│ ├─ Receives prompt with role info + resume text            │
│ ├─ Analyzes resume against role requirements               │
│ ├─ Generates structured JSON response with:                │
│ │  ├─ skill_match_percentage: 0-100                        │
│ │  ├─ matched_skills: [...]                                │
│ │  ├─ missing_skills: [...] (from core_skills only)        │
│ │  ├─ strengths: [...]                                     │
│ │  ├─ improvement_suggestions: [...]                       │
│ │  └─ final_verdict: "Strong|Moderate|Weak Fit"            │
│ └─ Returns JSON string                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (main.py) - Response normalization                 │
│ ═══════════════════════════════════════════════════════════ │
│ _normalize_analysis_dict(raw)                               │
│                                                             │
│ Step 1: Normalize skill_match_percentage                   │
│ ├─ Extract raw_pct from response                           │
│ ├─ Convert to float, then round to int                     │
│ ├─ Clamp to range [0, 100]                                 │
│ └─ Store as integer                                        │
│                                                             │
│ Step 2: Normalize list fields                              │
│ Helper: _as_str_list(value)                                │
│ ├─ If None → return []                                     │
│ ├─ If string → return [string]                             │
│ ├─ If list → convert all items to strings                  │
│ └─ Otherwise → return [str(value)]                         │
│                                                             │
│ Apply to all list fields:                                  │
│ ├─ matched_skills                                           │
│ ├─ missing_skills                                           │
│ ├─ strengths                                                │
│ └─ improvement_suggestions                                  │
│                                                             │
│ Step 3: Normalize final_verdict                            │
│ ├─ Convert to lowercase                                    │
│ ├─ If contains "strong" → "Strong Fit"                     │
│ ├─ If contains "moderate" or "medium" → "Moderate Fit"     │
│ ├─ If contains "weak" or "low" → "Weak Fit"                │
│ └─ Default → "Moderate Fit"                                │
│                                                             │
│ Step 4: Create AnalysisResult model                        │
│ ├─ Validate with Pydantic                                  │
│ └─ Return AnalysisResult instance                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (app.py) - Display results                        │
│ ═══════════════════════════════════════════════════════════ │
│ Response received as JSON                                  │
│                                                             │
│ UI Rendering:                                               │
│ ├─ Section: Analysis Result                                │
│ ├─ Metrics row (2 columns):                                │
│ │  ├─ Skill Match Percentage (large number)                │
│ │  └─ Final Verdict (text)                                 │
│ ├─ Progress bar (0-100% based on skill match)              │
│ ├─ Skills comparison (2 columns):                          │
│ │  ├─ Matched skills (bulleted list)                       │
│ │  └─ Missing skills (bulleted list)                       │
│ ├─ Resume strengths (bulleted list)                        │
│ └─ Improvement suggestions (bulleted list)                 │
└─────────────────────────────────────────────────────────────┘
```

### Flow 3: Error Handling Paths

```
┌─────────────────────────────────────────────────────────────┐
│ Potential Error Points and Handling                         │
└─────────────────────────────────────────────────────────────┘

Error 1: Backend not running
├─ Location: Frontend fetch_job_roles()
├─ Detection: requests.get() fails
├─ Handling: Display error message in Streamlit
└─ User sees: "Could not load job roles from the backend"

Error 2: Missing GEMINI_API_KEY
├─ Location: Backend _get_gemini_model()
├─ Detection: os.getenv() returns None
├─ Handling: Raise GeminiConfigurationError
├─ Caught by: POST /analyze endpoint
└─ Response: HTTP 500 with error message

Error 3: Empty file upload
├─ Location: Backend POST /analyze
├─ Detection: file_bytes is empty
├─ Handling: Raise HTTPException(400)
└─ Response: "Uploaded file is empty"

Error 4: PDF parsing failure
├─ Location: Backend extract_text_from_pdf_bytes()
├─ Detection: Exception during pdfplumber processing
├─ Handling: Raise exception
├─ Caught by: POST /analyze endpoint
└─ Response: HTTP 400 "Failed to parse PDF resume"

Error 5: No text extracted from resume
├─ Location: Backend POST /analyze
├─ Detection: resume_text.strip() is empty
├─ Handling: Raise HTTPException(400)
└─ Response: "Could not extract any text from the resume"

Error 6: Gemini returns invalid JSON
├─ Location: Backend analyze_resume_with_gemini()
├─ Detection: json.loads() raises JSONDecodeError
├─ Handling: Raise RuntimeError
├─ Caught by: POST /analyze endpoint
└─ Response: HTTP 500 "Failed to parse JSON from Gemini"

Error 7: Gemini response doesn't match schema
├─ Location: Backend _normalize_analysis_dict()
├─ Detection: AnalysisResult(**normalized) fails
├─ Handling: Raise exception
├─ Caught by: POST /analyze endpoint
└─ Response: HTTP 500 "Response did not match expected schema"

Error 8: Backend API error
├─ Location: Frontend call_analyze_api()
├─ Detection: requests.post() raises HTTPError
├─ Handling: Try to extract error detail from response
└─ Display: Error message in Streamlit with details
```

---

## API Contracts

### GET /health

**Purpose**: Health check endpoint

**Request**: None

**Response**:
```json
{
  "status": "ok"
}
```

**Status Codes**:
- `200 OK`: Service is healthy

---

### GET /job-roles

**Purpose**: Get list of available job roles

**Request**: None

**Response**:
```json
[
  {
    "id": "software_engineer",
    "label": "Software Engineer",
    "description": "Generalist software engineer...",
    "core_skills": ["Python", "Java", "JavaScript", ...]
  },
  {
    "id": "backend_engineer",
    "label": "Backend Engineer",
    "description": "Engineer focused on server-side...",
    "core_skills": ["Python", "Java", "Go", ...]
  },
  ...
]
```

**Status Codes**:
- `200 OK`: Successfully retrieved job roles

---

### POST /analyze

**Purpose**: Analyze resume against job role

**Request**:
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `file`: Resume file (PDF or plain text)
  - `job_role_id`: Target job role identifier (string)

**Example**:
```http
POST /analyze HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="resume.pdf"
Content-Type: application/pdf

[binary PDF data]
------WebKitFormBoundary
Content-Disposition: form-data; name="job_role_id"

software_engineer
------WebKitFormBoundary--
```

**Response**:
```json
{
  "skill_match_percentage": 72,
  "matched_skills": [
    "Python",
    "REST APIs",
    "SQL",
    "Docker"
  ],
  "missing_skills": [
    "Kubernetes",
    "Cloud (AWS)",
    "GraphQL"
  ],
  "strengths": [
    "Clear experience building and maintaining backend services.",
    "Demonstrated ownership of end-to-end features.",
    "Strong foundation in Python and REST API development."
  ],
  "improvement_suggestions": [
    "Quantify impact with metrics (e.g., latency reduction, cost savings).",
    "Highlight specific cloud platforms and tooling used.",
    "Add more details about system design experience."
  ],
  "final_verdict": "Moderate Fit"
}
```

**Status Codes**:
- `200 OK`: Analysis completed successfully
- `400 Bad Request`: Invalid input (empty file, invalid format, etc.)
- `500 Internal Server Error`: Server error (Gemini API error, configuration error)

**Error Response**:
```json
{
  "detail": "Error message description"
}
```

---

## Data Models

### AnalysisResult (Pydantic Model)

```python
class AnalysisResult(BaseModel):
    skill_match_percentage: int  # Range: 0-100
    matched_skills: List[str]    # Skills found in resume
    missing_skills: List[str]    # Core skills not in resume
    strengths: List[str]         # Resume strong points
    improvement_suggestions: List[str]  # Concrete suggestions
    final_verdict: str          # "Strong Fit" | "Moderate Fit" | "Weak Fit"
```

**Validation**:
- `skill_match_percentage`: Must be integer between 0 and 100
- `final_verdict`: Must match regex pattern for three allowed values
- All list fields: Must be lists of strings

### JobRole (Pydantic Model)

```python
class JobRole(BaseModel):
    id: str                      # Unique identifier (e.g., "software_engineer")
    label: str                   # Display name (e.g., "Software Engineer")
    description: str | None      # Role description (optional)
    core_skills: List[str]       # List of core skills for the role
```

### Job Role Configuration (JSON)

```json
{
  "role_id": {
    "label": "Display Name",
    "description": "Detailed role description",
    "core_skills": [
      "Skill 1",
      "Skill 2",
      "Skill 3"
    ]
  }
}
```

---

## Configuration

### Environment Variables

#### Backend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | **Yes** | None | Google Gemini API key for AI analysis |

**Example**:
```bash
# Linux/macOS
export GEMINI_API_KEY="your_api_key_here"

# Windows PowerShell
$env:GEMINI_API_KEY = "your_api_key_here"
```

#### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_BASE_URL` | No | `http://localhost:8000` | Base URL of the FastAPI backend |

**Example**:
```bash
# Linux/macOS
export BACKEND_BASE_URL="https://api.example.com"

# Windows PowerShell
$env:BACKEND_BASE_URL = "https://api.example.com"
```

### Gemini Configuration

Located in `gemini_analyzer.py` → `_get_gemini_model()`:

```python
generation_config = {
    "temperature": 0.0,      # Deterministic output
    "top_p": 1.0,           # Full probability mass
    "top_k": 1,             # Single most likely token
    "response_mime_type": "application/json"  # Enforce JSON output
}

model_name = "gemini-2.5-flash-lite"  # Fast, cost-effective model
```

**Why these settings?**
- `temperature=0.0`: Ensures consistent, deterministic analysis
- `response_mime_type="application/json"`: Forces model to return JSON
- `gemini-2.5-flash-lite`: Balance between speed and quality

### CORS Configuration

Located in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins (development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Note**: Restrict `allow_origins` to specific domains in production.

---

## Error Handling

### Error Types and Handling Strategy

#### 1. Configuration Errors

**Type**: `GeminiConfigurationError`
**When**: GEMINI_API_KEY is missing
**Handled at**: Backend initialization
**Response**: HTTP 500 with clear error message
**User action**: Set API key and restart backend

#### 2. Validation Errors

**Type**: `HTTPException(400)`
**When**: 
- Empty file upload
- No text extracted from file
- Invalid job_role_id
**Handled at**: Endpoint level
**Response**: HTTP 400 with descriptive message
**User action**: Fix input and retry

#### 3. File Processing Errors

**Type**: Exception during PDF/text extraction
**When**: Corrupted file or unsupported format
**Handled at**: Resume parser
**Response**: HTTP 400 "Failed to parse PDF resume"
**User action**: Upload different file

#### 4. Gemini API Errors

**Type**: RuntimeError, JSONDecodeError
**When**:
- Gemini returns empty response
- Gemini returns invalid JSON
- API connection issues
**Handled at**: Gemini analyzer
**Response**: HTTP 500 with error details
**User action**: Retry or check API status

#### 5. Schema Validation Errors

**Type**: Pydantic ValidationError
**When**: Gemini response doesn't match expected schema
**Handled at**: Response normalization
**Response**: HTTP 500 "Response did not match expected schema"
**User action**: Report issue (should be rare due to normalization)

#### 6. Network Errors

**Type**: requests.RequestException
**When**: Frontend cannot reach backend
**Handled at**: Frontend API calls
**Response**: Streamlit error message
**User action**: Ensure backend is running

---

## Key Design Decisions

### 1. Strict JSON Output
- **Decision**: Enforce JSON-only responses from Gemini
- **Implementation**: `response_mime_type: "application/json"` in config
- **Benefit**: Eliminates parsing complexity and errors

### 2. Deterministic Analysis
- **Decision**: Use temperature=0.0 for Gemini
- **Implementation**: Set in generation_config
- **Benefit**: Consistent results for same input

### 3. Grounded Analysis
- **Decision**: Explicitly forbid hallucinations in prompt
- **Implementation**: Strict rules in prompt template
- **Benefit**: Analysis based only on actual resume content

### 4. Response Normalization
- **Decision**: Normalize Gemini output before validation
- **Implementation**: `_normalize_analysis_dict()` function
- **Benefit**: Handles minor variations in Gemini responses

### 5. Caching
- **Decision**: Cache job roles and Gemini model
- **Implementation**: `@lru_cache` decorators
- **Benefit**: Improved performance, reduced overhead

### 6. Separation of Concerns
- **Decision**: Split parsing, analysis, and presentation
- **Implementation**: Separate modules for each concern
- **Benefit**: Maintainability and testability

### 7. Error Recovery
- **Decision**: Provide fallback values in normalization
- **Implementation**: Default to "Moderate Fit", empty lists
- **Benefit**: Graceful degradation instead of failures

---

## Performance Considerations

### Caching
- **Job roles**: Cached on first load, reused for all requests
- **Gemini model**: Initialized once, reused for all analyses
- **Frontend job roles**: Cached by Streamlit

### Bottlenecks
1. **Gemini API call**: ~2-5 seconds per analysis
2. **PDF parsing**: ~100-500ms for typical resumes
3. **Network latency**: Frontend ↔ Backend

### Optimization Opportunities
1. Add database for storing previous analyses
2. Implement rate limiting to prevent API overuse
3. Add request queuing for high traffic
4. Cache analysis results for identical resumes

---

## Security Considerations

### API Key Protection
- **Storage**: Environment variable (not in code)
- **Transmission**: HTTPS only (Gemini API)
- **Logging**: Never log API keys

### File Upload Safety
- **Size limits**: FastAPI default (no explicit limit set)
- **Type validation**: Check content_type and extension
- **Content parsing**: Use safe libraries (pdfplumber)

### CORS Policy
- **Current**: Allow all origins (development)
- **Production**: Should restrict to specific domains

### Input Validation
- **Resume text**: Must be non-empty
- **Job role ID**: Validated against known roles
- **File uploads**: Type checked before processing

### Error Messages
- **User-facing**: Generic, non-revealing
- **Internal**: Detailed for debugging
- **Never expose**: API keys, file paths, stack traces (in production)

---

## Deployment Considerations

### Backend Deployment
- **Server**: Uvicorn (ASGI server)
- **Requirements**: Python 3.10+, dependencies from requirements.txt
- **Environment**: Must set GEMINI_API_KEY
- **Scaling**: Stateless, can be horizontally scaled

### Frontend Deployment
- **Server**: Streamlit built-in server
- **Requirements**: Python 3.10+, streamlit, requests
- **Environment**: Optionally set BACKEND_BASE_URL
- **Scaling**: Can deploy multiple instances

### InsForge Integration
- Backend can be deployed as containerized service
- Frontend can be deployed as web app
- Use InsForge environment variables for configuration
- Can add InsForge database for persistence

---

## Testing Recommendations

### Unit Tests
1. **Resume parser**:
   - Test PDF extraction with sample PDFs
   - Test plain text extraction with various encodings
   - Test empty file handling

2. **Gemini analyzer**:
   - Mock Gemini API responses
   - Test prompt building with different roles
   - Test JSON parsing and error handling

3. **Response normalization**:
   - Test with various Gemini response formats
   - Test clamping of skill_match_percentage
   - Test verdict normalization

### Integration Tests
1. **Backend API**:
   - Test /health endpoint
   - Test /job-roles endpoint
   - Test /analyze with real files

2. **Frontend**:
   - Test job role loading
   - Test file upload
   - Test result rendering

### End-to-End Tests
1. Upload resume → Receive analysis
2. Test all job roles
3. Test PDF and text formats
4. Test error scenarios

---

## Troubleshooting Guide

### Issue: "GEMINI_API_KEY environment variable is not set"
**Cause**: API key not configured
**Solution**: Set environment variable before starting backend
```bash
export GEMINI_API_KEY="your_key_here"
```

### Issue: "Could not load job roles from the backend"
**Cause**: Backend not running or wrong URL
**Solution**: 
1. Ensure backend is running on correct port
2. Check BACKEND_BASE_URL in frontend

### Issue: "Failed to parse PDF resume"
**Cause**: Corrupted or image-based PDF
**Solution**: Try converting to text PDF or use .txt format

### Issue: "Gemini returned an empty response"
**Cause**: API issue or prompt too large
**Solution**: 
1. Check API key validity
2. Try with shorter resume
3. Check Gemini API status

### Issue: Analysis takes too long
**Cause**: Large resume or API latency
**Solution**: 
1. Optimize resume size
2. Check network connection
3. Consider increasing timeout

---

## Future Enhancements

### Potential Features
1. **Resume history**: Store and compare previous analyses
2. **Batch processing**: Analyze multiple resumes at once
3. **Custom roles**: Allow users to define their own roles
4. **Comparison view**: Compare candidate against candidate
5. **ATS score**: Calculate overall ATS compatibility score
6. **Export reports**: PDF/Word export of analysis results
7. **Authentication**: User accounts and saved preferences
8. **Analytics**: Track hiring trends and insights

### Technical Improvements
1. **Database integration**: PostgreSQL for persistence
2. **Async processing**: Background jobs for large files
3. **Caching layer**: Redis for faster repeat analyses
4. **API versioning**: Support multiple API versions
5. **Rate limiting**: Prevent API abuse
6. **Logging**: Structured logging with ELK stack
7. **Monitoring**: Add metrics and alerting
8. **Testing**: Comprehensive test suite with >80% coverage

---

## Conclusion

This AI Resume Analyzer is a well-architected, production-ready application that demonstrates:
- Clean separation of concerns
- Robust error handling
- Deterministic AI analysis
- User-friendly interface
- Maintainable codebase

The system efficiently processes resumes, provides valuable insights, and maintains professional ATS-style evaluation standards.
