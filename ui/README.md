# Large File Upload → Translate → Word (.docx)

A minimal full-stack UI that:
1) Uploads large files in chunks (5MB) 
2) Translates the content on the server 
3) Returns a downloadable Word (.docx) file

## Features
- Chunked upload (works better for large files / unstable networks)
- Background translation job + progress polling
- Word output via `python-docx`

## Supported input types
- `.txt`, `.md`, `.csv`, `.srt`, `.log`
- `.docx` (extracts paragraphs + tables)

> PDFs are not handled in this template. Add a PDF text extractor if you need it.

## Quick start (Docker)
```bash
cd translate-ui
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000/health

### Enable real translation
Set an environment variable on the backend:
- `OPENAI_API_KEY`
- (optional) `OPENAI_MODEL` (default: `gpt-4o-mini`)

In `docker-compose.yml`, uncomment and set:
```yml
environment:
  - OPENAI_API_KEY=sk-...
```

## Quick start (Local dev)
### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Security notes (what you may want to add)
- Authentication / per-user storage
- Max file size limits
- Virus scanning
- Auto-delete uploads/output after N hours
- Rate limiting

## Where to customize
- Chunk size: `frontend/src/App.jsx` (`CHUNK_SIZE`)
- How text is split for translation: `backend/app/translator.py` (`CHUNK_CHARS`)
- File parsing: `backend/app/readers.py`
