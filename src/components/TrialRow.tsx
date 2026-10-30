import type { Trial } from '../types'

type Props = { trial: Trial; onSelect: (id: number) => void }

export default function TrialRow({ trial, onSelect }: Props) {
  return (
    <button className="trial-row press" type="button" onClick={() => onSelect(trial.id)} aria-label={`${trial.title} 상세 보기`}>
      <div className="trial-main">
        <div className="row-title-line"><h3>{trial.title}</h3><span className="status">{trial.status}</span></div>
        <p className="approval-number tabular">승인번호 {trial.approval_number}</p>
        <p className="condition">{trial.condition_name}</p>
      </div>
      <div className="trial-meta">
        <span>승인일</span>
        <strong className="tabular">{trial.approval_date}</strong>
        <span>{trial.organization}</span>
      </div>
      <div className="source-line">{trial.source}<span aria-hidden="true">›</span></div>
    </button>
  )
}
