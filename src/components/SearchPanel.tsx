import type { FormEvent } from 'react'

type Props = {
  query: string
  onQueryChange: (value: string) => void
  onSearch: () => void
  onReset: () => void
  isLoading: boolean
}

export default function SearchPanel({ query, onQueryChange, onSearch, onReset, isLoading }: Props) {
  const submit = (event: FormEvent) => {
    event.preventDefault()
    onSearch()
  }

  return (
    <section className="search-panel" aria-labelledby="search-heading">
      <div>
        <p className="eyebrow">승인정보 조회</p>
        <h2 id="search-heading">찾고 싶은 승인정보를 검색하세요</h2>
        <p className="search-help">임상시험명, 질환명, 승인번호, 기관명으로 예시 정보를 찾을 수 있어요.</p>
      </div>
      <form className="search-form" onSubmit={submit}>
        <label className="visually-hidden" htmlFor="trial-search">승인정보 검색어</label>
        <input id="trial-search" value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="예: 고혈압, KCT0001001, 서울대학교병원" />
        <button className="primary-button" type="submit" disabled={isLoading}>{isLoading ? '검색 중' : '검색'}</button>
        {query && <button className="reset-button" type="button" onClick={onReset}>초기화</button>}
      </form>
    </section>
  )
}
