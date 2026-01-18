import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock
from typing import Dict, Optional


@dataclass
class Job:
    job_id: str
    status: str  # queued|running|done|error
    progress: float
    message: str
    file_path: str
    source_lang: Optional[str]
    target_lang: str
    output_path: Optional[str] = None


class JobStore:
    def __init__(self, output_dir: Path):
        self._lock = Lock()
        self._jobs: Dict[str, Job] = {}
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create(self, file_path: Path, target_lang: str, source_lang: Optional[str] = None) -> str:
        job_id = uuid.uuid4().hex
        job = Job(
            job_id=job_id,
            status='queued',
            progress=0.0,
            message='Queued',
            file_path=str(file_path),
            source_lang=source_lang,
            target_lang=target_lang,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job_id

    def get(self, job_id: str) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return asdict(job) if job else None

    def update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in kwargs.items():
                if hasattr(job, k):
                    setattr(job, k, v)

    def output_path_for(self, job_id: str) -> Path:
        return self.output_dir / f'{job_id}.docx'
