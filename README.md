# SchemeSathi

SchemeSathi is a Flask-based educational prototype for discovering Indian government scheme information. It includes a responsive website, a rule-based eligibility matcher, a SQLite scheme catalogue and an optional Gemini-powered assistant.

## Important data disclaimer

The included records are **demonstration seed data**, not a verified or complete government scheme database. Some records contain illustrative criteria. Do not use them to make real eligibility decisions. Before presenting recommendations as factual, review each scheme's current official guidelines, encode all mandatory conditions and exclusions, and record a verification date. The application is not affiliated with a government department and cannot guarantee approval.

## Requirements

- Python 3.10+
- Internet connection for installing packages
- Optional Gemini API key for live AI answers

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and add your Gemini API key to `GEMINI_API_KEY`. If you leave it blank, the chatbot uses a clearly labelled deterministic demo fallback.

Then run:

```powershell
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Run locally (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your key to .env, then:
python app.py
```

## Features

- Responsive home page
- Profile-based scheme discovery
- Rule-based eligibility checks with pass/fail/unknown explanations
- Scheme information cards and official source links
- Chat assistant with optional Gemini API integration
- Simple keyword-based retrieval over the local scheme catalogue
- English/Hindi response-language selection
- Basic local admin API for adding records

## API endpoints

- `GET /api/schemes` — list scheme records
- `POST /api/recommend` — evaluate a profile against scheme records
- `POST /api/chat` — retrieve relevant records and generate an answer
- `POST /api/admin/schemes` — add a scheme record (local development only)

Example recommendation request:

```json
{
  "age": "20",
  "income": "200000",
  "state": "Madhya Pradesh",
  "occupation": "Student",
  "education": "BTech"
}
```

## Before public deployment

The admin endpoint is intentionally unauthenticated for local demonstration only. Add authentication, CSRF protection, rate limiting, input validation, secure secret management, privacy controls and HTTPS before any public deployment. Add tests for each scheme's actual eligibility rules. Do not store Aadhaar numbers, bank credentials or unnecessary personal data.

## Suggested next development milestones

1. Replace demonstration scheme records with verified official data.
2. Add an authenticated admin interface and scheme update workflow.
3. Implement document ingestion, chunking, embeddings and vector retrieval for true RAG.
4. Add automated tests for eligibility rules and prompt grounding.
5. Add deployment configuration and monitoring.
