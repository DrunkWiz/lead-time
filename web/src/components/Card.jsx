import Status from './Status.jsx'
import Sparkline from './Sparkline.jsx'
import StageButtons from './StageButtons.jsx'
import FoodArt from './FoodArt.jsx'
import { PROVIDER_LABEL } from '../format.js'

export default function Card({ card, rank, asOf }) {
  const { fit, launch, spark } = card
  return (
    <article className="card">
      <a className="card-link" href={`#/c/${card.id}`}>
        <FoodArt id={card.id} category={card.category} />
        <div className="card-head">
          <div>
            <h2>{card.name}</h2>
            <Status status={card.status} label={card.status_label} />
          </div>
          {rank && <span className="rank num" aria-label={`Pick ${rank}`}>#{rank}</span>}
        </div>
        <p className="why">{card.why}</p>
        {fit?.verdict === 'adapt' && (
          <p className="adapt"><b>Your version:</b> {fit.adaptation}. <span className="muted">{fit.reason}</span></p>
        )}
        {fit?.verdict === 'make' && <p className="adapt"><b>You can make the original.</b> <span className="muted">{fit.reason}</span></p>}
        {fit?.overlaps?.length > 0 && (
          <p className="small muted" style={{ marginTop: 6 }}>Close to your {fit.overlaps.join(' and ')}.</p>
        )}
        <Sparkline
          weeks={spark.weeks} lines={spark.lines} originGeo={spark.origin} originName={spark.origin_name}
          takeoffs={card.takeoffs} window={card.window} asOf={asOf} height={120} width={420}
          label={`${card.evidence} Lines show search interest, each scaled to its own peak.`}
        />
        <div className="card-foot">
          <span className="launch-line">{launch.text}</span>
          <span className="btn ghost" aria-hidden="true">Launch plan →</span>
        </div>
        <p className="provider">Kitchen check: {PROVIDER_LABEL[card.fit_provider] || card.fit_provider}</p>
      </a>
      <div className="card-actions"><StageButtons id={card.id} asOf={asOf} /></div>
    </article>
  )
}
