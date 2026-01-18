import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .jobs import JobStore
from .process import start_translation_job

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = (BASE_DIR / '..' / 'data').resolve()
UPLOAD_DIR = DATA_DIR / 'uploads'
CHUNK_DIR = DATA_DIR / 'chunks'
OUTPUT_DIR = DATA_DIR / 'outputs'

for d in (UPLOAD_DIR, CHUNK_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title='Large File Translator')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('CORS_ORIGIN', 'http://localhost:5173')],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

jobs = JobStore(OUTPUT_DIR)

@app.get('/health')
def health():
    return {'ok': True}

@app.post('/upload/init')
def upload_init(filename: str = Form(...)):
    upload_id = uuid.uuid4().hex
    up_dir = CHUNK_DIR / upload_id
    up_dir.mkdir(parents=True, exist_ok=True)
    (up_dir / 'meta.txt').write_text(filename, encoding='utf-8')
    return {'upload_id': upload_id}

@app.post('/upload/chunk')
def upload_chunk(
    upload_id: str = Form(...),
    index: int = Form(...),
    chunk: UploadFile = File(...),
):
    up_dir = CHUNK_DIR / upload_id
    if not up_dir.exists():
        raise HTTPException(status_code=404, detail='upload_id not found')

    part_path = up_dir / f'{index:08d}.part'
    with part_path.open('wb') as f:
        while True:
            data = chunk.file.read(1024 * 1024)
            if not data:
                break
            f.write(data)

    return {'ok': True}

@app.post('/upload/complete')
def upload_complete(
    upload_id: str = Form(...),
    total_chunks: int = Form(...),
):
    up_dir = CHUNK_DIR / upload_id
    if not up_dir.exists():
        raise HTTPException(status_code=404, detail='upload_id not found')

    filename = (up_dir / 'meta.txt').read_text(encoding='utf-8').strip() or f'{upload_id}.bin'
    safe_name = Path(filename).name
    final_path = UPLOAD_DIR / f'{upload_id}_{safe_name}'

    with final_path.open('wb') as out:
        for i in range(total_chunks):
            part = up_dir / f'{i:08d}.part'
            if not part.exists():
                raise HTTPException(status_code=400, detail=f'missing chunk {i}')
            with part.open('rb') as pf:
                shutil.copyfileobj(pf, out)

    shutil.rmtree(up_dir, ignore_errors=True)
    return {'upload_id': upload_id, 'stored_path': final_path.name}

@app.post('/jobs/start')
def jobs_start(
    upload_id: str = Form(...),
    stored_path: str = Form(...),
    target_lang: str = Form(...),
    source_lang: Optional[str] = Form(None),
):
    file_path = UPLOAD_DIR / stored_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='uploaded file not found')

    job_id = jobs.create(file_path=file_path, target_lang=target_lang, source_lang=source_lang)
    start_translation_job(job_store=jobs, job_id=job_id)
    return {'job_id': job_id}

@app.get('/jobs/{job_id}')
def jobs_get(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='job not found')
    return job

@app.get('/jobs/{job_id}/download')
def jobs_download(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='job not found')
    if job.get('status') != 'done':
        raise HTTPException(status_code=400, detail='job not finished')

    out_path = Path(job['output_path'])
    if not out_path.exists():
        raise HTTPException(status_code=404, detail='output file missing')

    return FileResponse(
        path=str(out_path),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=out_path.name,
    )
