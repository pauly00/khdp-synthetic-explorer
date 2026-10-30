import type { Trial } from '../types'

type Props = { trial: Trial; onBack: () => void }

const fields = [
  ['승인번호', 'approval_number'], ['승인일', 'approval_date'], ['연구 목적', 'purpose'],
  ['대상 질환', 'condition_name'], ['기관', 'organization'], ['진행 상태', 'status'],
  ['간단한 설명', 'description'], ['데이터 출처', 'source'],
] as const

export default function TrialDetail({ trial, onBack }: Props) {
  return (
    <main className="page detail-page">
      <button type="button" className="back-button" onClick={onBack}>← 결과 목록으로</button>
      <section className="detail-header">
        <p className="eyebrow">승인정보 상세</p>
        <h1>{trial.title}</h1>
        <p className="detail-notice">현재 표시되는 모든 정보는 실제 공공데이터 API 연동 전 예시 데이터입니다.</p>
      </section>
      <section className="detail-list" aria-label="승인정보 세부 내용">
        {fields.map(([label, key]) => (
          <div className="detail-item" key={key}>
            <dt>{label}</dt>
            <dd className={key === 'approval_number' || key === 'approval_date' ? 'tabular' : ''}>{trial[key]}</dd>
          </div>
        ))}
      </section>
    </main>
  )
}
