import traceback
from threading import Thread
from pathlib import Path

from .jobs import JobStore
from .translator import translate_file_to_docx


def start_translation_job(job_store: JobStore, job_id: str) -> None:
    """Starts a background thread for translation."""

    def run():
        job = job_store.get(job_id)
        if not job:
            return
        try:
            job_store.update(job_id, status='running', progress=0.01, message='Starting')
            out_path = job_store.output_path_for(job_id)

            def on_progress(p: float, msg: str):
                job_store.update(job_id, progress=max(0.0, min(1.0, p)), message=msg)

            translate_file_to_docx(
                file_path=Path(job['file_path']),
                source_lang=job.get('source_lang'),
                target_lang=job['target_lang'],
                out_docx=out_path,
                progress_cb=on_progress,
            )
            job_store.update(job_id, status='done', progress=1.0, message='Done', output_path=str(out_path))
        except Exception:
            job_store.update(job_id, status='error', message=traceback.format_exc(), progress=1.0)

    Thread(target=run, daemon=True).start()
