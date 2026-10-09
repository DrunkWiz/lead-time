import { boardStore, todayIso, useBoard } from '../store.js'

// Watch → Plan → (Launched is set from the tracker form). Tapping the active stage removes it.
export default function StageButtons({ id, compact = false, asOf }) {
  const board = useBoard()
  const stage = board[id]?.stage
  const today = asOf || todayIso()
  if (stage === 'launched') {
    return <a className="chip" aria-pressed="true" href={`#/c/${id}#track`}>Launched · track sales</a>
  }
  return (
    <div className="chips" role="group" aria-label="Add to your board">
      <button type="button" className="chip" aria-pressed={stage === 'watching'}
        onClick={() => boardStore.setStage(id, stage === 'watching' ? null : 'watching', today)}>
        {stage === 'watching' ? 'Watching' : 'Watch'}
      </button>
      <button type="button" className="chip" aria-pressed={stage === 'planned'}
        onClick={() => boardStore.setStage(id, stage === 'planned' ? null : 'planned', today)}>
        {stage === 'planned' ? 'In your plan' : compact ? 'Plan' : 'Add to plan'}
      </button>
    </div>
  )
}
