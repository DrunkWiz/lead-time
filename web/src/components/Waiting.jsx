import { useEffect, useState } from 'react'

const SLOW_AFTER_S = 4   // saved answers come back in well under a second; past this, a model is writing a fresh one

// Loading line for anything that may wait on a live model call.
export default function Waiting({ text, slowText = 'Asking the model to check your kitchen and write this fresh. It can take up to a minute the first time, then it’s saved.' }) {
  const [s, setS] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setS((n) => n + 1), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="loading" role="status" aria-live="polite">
      <p><span className="dot-pulse" aria-hidden="true" />{text}</p>
      {s >= SLOW_AFTER_S && <p className="small muted" style={{ marginTop: 4 }}>{slowText} <span className="num">{s}s</span></p>}
    </div>
  )
}
