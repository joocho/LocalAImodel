import os
from pathlib import Path
from typing import Callable, Optional, List

from .word import write_docx
from .readers import extract_text


def _split_text(text: str, max_chars: int = 8000) -> List[str]:
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + max_chars)
        # try to split on a newline or sentence boundary
        cut = text.rfind('\n', start, end)
        if cut == -1:
            cut = text.rfind('. ', start, end)
        if cut != -1 and cut > start + int(max_chars * 0.5):
            end = cut + 1
        chunks.append(text[start:end])
        start = end
    return chunks


def _translate_with_openai(chunk: str, source_lang: Optional[str], target_lang: str) -> str:
    """Translate using the OpenAI Python SDK (v1+). Requires OPENAI_API_KEY."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    src = source_lang.strip() if source_lang else 'auto-detect'
    system = (
        'You are a professional translator.\n'
        'Rules:\n'
        '1) Translate faithfully and naturally.\n'
        '2) Preserve line breaks and basic formatting.\n'
        '3) Do not add commentary. Output only the translation.'
    )
    user = f'Translate from {src} to {target_lang}.\n\nTEXT:\n{chunk}'

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    # The SDK returns a structured response; output_text is the easiest accessor.
    return resp.output_text.strip()


def _translate_fallback(chunk: str, source_lang: Optional[str], target_lang: str) -> str:
    """Fallback when OPENAI_API_KEY isn't set."""
    header = f'[Translation disabled: set OPENAI_API_KEY to translate to {target_lang}]\n\n'
    return header + chunk


def translate_file_to_docx(
    file_path: Path,
    source_lang: Optional[str],
    target_lang: str,
    out_docx: Path,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> None:
    text = extract_text(file_path)

    chunks = _split_text(text, max_chars=int(os.environ.get('CHUNK_CHARS', '8000')))
    total = max(1, len(chunks))

    use_openai = bool(os.environ.get('OPENAI_API_KEY'))
    translated_parts: List[str] = []

    for i, chunk in enumerate(chunks):
        if progress_cb:
            progress_cb(i / total, f'Translating chunk {i+1}/{total}')

        if use_openai:
            out = _translate_with_openai(chunk, source_lang=source_lang, target_lang=target_lang)
        else:
            out = _translate_fallback(chunk, source_lang=source_lang, target_lang=target_lang)
        translated_parts.append(out)

    full = '\n'.join(translated_parts)
    if progress_cb:
        progress_cb(0.95, 'Writing Word document')

    write_docx(full, out_docx)
    if progress_cb:
        progress_cb(1.0, 'Done')
