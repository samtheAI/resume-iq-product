# ResumeIQ

ResumeIQ is a polished resume workspace with three features:

- resume quality review with strengths and improvement opportunities;
- explainable resume-to-role matching; and
- safe, code-based resume tailoring with clean DOCX and TXT downloads.

The tailoring feature uses deterministic Python logic to prioritize only content already present in the resume. It does not generate new candidate claims and does not make an API request.

## Run locally

### macOS

```bash
cd /path/to/resume_analyzer_product
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

### Windows

```bat
cd C:\path\to\resume_analyzer_product
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Add your API key to `.env` before starting:

```text
GROQ_API_KEY=your_actual_groq_api_key
```

Open `http://localhost:8501` if the browser does not open automatically.
