const ICONS = {
  // flame: it's landing now
  arriving_now: <path d="M12 2c1 3.5 5 5.5 5 10a5 5 0 0 1-10 0c0-2 1-3.5 2-4.5.3 1.6 1.2 2.6 2.3 3C10.6 8 11 5 12 2z" fill="currentColor" />,
  // plane: on its way
  rising_abroad: <path d="M2.5 13.5l19-8-5.5 15-3.2-6.3-10.3-.7zm10.3.7l3.7-5.2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />,
  // check: already here
  already_here: <path d="M4 12.5l5 5L20 6.5" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />,
  // down: cooled off
  peaked_here: <path d="M4 7l6 6 3-3 7 7M20 11v6h-6" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />,
  // dash: not coming
  not_travelling: <path d="M5 12h14" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />,
}

export default function Status({ status, label }) {
  return (
    <span className={`status ${status}`}>
      <svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[status]}</svg>
      {label}
    </span>
  )
}
