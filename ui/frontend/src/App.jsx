import React, { useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const CHUNK_SIZE = 5 * 1024 * 1024

async function api(path, opts) {
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      msg = data.detail || msg
    } catch {}
    throw new Error(msg)
  }
  return res
}

function humanBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let b = bytes
  let i = 0
  while (b >= 1024 && i < units.length - 1) {
    b /= 1024
    i++
  }
  return `${b.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

export default function App() {
  const [file, setFile] = useState(null)
  const [targetLang, setTargetLang] = useState('English')
  const [sourceLang, setSourceLang] = useState('')
  const [uploadPct, setUploadPct] = useState(0)
  const [job, setJob] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const canStart = useMemo(() => !!file && !busy, [file, busy])

  async function start() {
    if (!file) return
    setError('')
    setBusy(true)
    setUploadPct(0)
    setJob(null)

    try {
      // 1) init
      const initFd = new FormData()
      initFd.append('filename', file.name)
      const initRes = await api('/upload/init', { method: 'POST', body: initFd })
      const { upload_id } = await initRes.json()

      // 2) chunk upload
      const total = Math.ceil(file.size / CHUNK_SIZE)
      for (let i = 0; i < total; i++) {
        const start = i * CHUNK_SIZE
        const end = Math.min(file.size, start + CHUNK_SIZE)
        const blob = file.slice(start, end)
        const fd = new FormData()
        fd.append('upload_id', upload_id)
        fd.append('index', String(i))
        fd.append('chunk', blob, `${file.name}.part${i}`)
        await api('/upload/chunk', { method: 'POST', body: fd })
        setUploadPct(Math.round(((i + 1) / total) * 100))
      }

      // 3) complete
      const compFd = new FormData()
      compFd.append('upload_id', upload_id)
      compFd.append('total_chunks', String(total))
      const compRes = await api('/upload/complete', { method: 'POST', body: compFd })
      const complete = await compRes.json()

      // 4) start job
      const jobFd = new FormData()
      jobFd.append('upload_id', upload_id)
      jobFd.append('stored_path', complete.stored_path)
      jobFd.append('target_lang', targetLang)
      if (sourceLang.trim()) jobFd.append('source_lang', sourceLang.trim())

      const jobRes = await api('/jobs/start', { method: 'POST', body: jobFd })
      const { job_id } = await jobRes.json()

      // 5) poll
      let done = false
      while (!done) {
        await new Promise((r) => setTimeout(r, 1000))
        const jRes = await api(`/jobs/${job_id}`, { method: 'GET' })
        const j = await jRes.json()
        setJob(j)
        if (j.status === 'done') done = true
        if (j.status === 'error') throw new Error(j.message || 'Translation failed')
      }
    } catch (e) {
      setError(e?.message || String(e))
    } finally {
      setBusy(false)
    }
  }

  const downloadUrl = job?.status === 'done' ? `${API_BASE}/jobs/${job.job_id}/download` : null

  return (
    <div className="container">
      <div className="card">
        <div className="h1">Large File Upload → Translate → Word (.docx)</div>
        <div className="sub">
          Chunked upload (5MB pieces). Backend translates and returns a Word document.
        </div>

        <div className="hr" />

        <div className="row">
          <div className="drop" onClick={() => document.getElementById('file').click()}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>Choose a file</div>
            <div className="small">Supported: .txt, .md, .csv, .srt, .docx</div>
            {file && (
              <div className="small" style={{ marginTop: 10 }}>
                Selected: <b>{file.name}</b> ({humanBytes(file.size)})
              </div>
            )}
          </div>

          <div className="grid">
            <label>
              Target language
              <input value={targetLang} onChange={(e) => setTargetLang(e.target.value)} placeholder="e.g., English" />
            </label>
            <label>
              Source language (optional)
              <input value={sourceLang} onChange={(e) => setSourceLang(e.target.value)} placeholder="e.g., Korean" />
            </label>
            <button className="btn" disabled={!canStart} onClick={start}>
              {busy ? 'Working…' : 'Upload & Translate'}
            </button>
            {downloadUrl && (
              <a className="btn" href={downloadUrl}>
                Download Word (.docx)
              </a>
            )}
          </div>
        </div>

        <input
          id="file"
          type="file"
          style={{ display: 'none' }}
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <div style={{ marginTop: 16 }}>
          <div className="kv">
            <div>Upload progress</div>
            <div>{uploadPct}%</div>
          </div>
          <div className="bar">
            <div style={{ width: `${uploadPct}%` }} />
          </div>
        </div>

        {job && (
          <div style={{ marginTop: 16 }}>
            <div className="kv">
              <div>Job status</div>
              <div>{job.status}</div>
            </div>
            <div className="kv">
              <div>Job progress</div>
              <div>{Math.round((job.progress || 0) * 100)}%</div>
            </div>
            <div className="bar">
              <div style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
            </div>
            <div className="small" style={{ marginTop: 8 }}>
              {job.message}
            </div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 16 }} className="err">
            {error}
          </div>
        )}

        <div className="hr" />

        <div className="small">
          Notes: Set <b>OPENAI_API_KEY</b> on the backend to enable translation. Otherwise the app will produce a Word file
          containing the original text and a warning header.
        </div>
      </div>
    </div>
  )
}
