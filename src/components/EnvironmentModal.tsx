import { useRef } from 'react'
import Modal from './Modal'

type Props = { onClose: () => void }
type StorageRow = { item: string; location: string; form: string; retention: string }

const storage: StorageRow[] = [
  { item: '분석용 CSV 내용, 문서, 메모, 등록 이력', location: '프로젝트 데이터 영역의 SQLite 파일', form: '자료별 테이블과 문서·이력 테이블', retention: '현재 서버가 같은 파일을 다시 열 수 있는 동안 유지됩니다.' },
  { item: '업로드한 원본 CSV 사본', location: '프로젝트 데이터 영역의 원본 파일 폴더', form: '자료 종류별 CSV 사본', retention: '적재 성공 뒤 보관됩니다.' },
  { item: '분할 업로드 조각', location: '프로젝트 데이터 영역의 임시 업로드 폴더', form: '조각 파일', retention: '취소 시 삭제되고 적재 뒤에는 정리됩니다.' },
]

const licenses = [
  { name: 'React', version: '18.3.1', license: 'MIT', url: 'https://react.dev/' },
  { name: 'Vite', version: '5.4.21', license: 'MIT', url: 'https://vite.dev/' },
  { name: 'FastAPI', version: '현재 실행환경 제공', license: 'MIT', url: 'https://fastapi.tiangolo.com/' },
]

export default function EnvironmentModal({ onClose }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null)

  return <Modal titleId="environment-title" className="environment-modal" onClose={onClose}>
    <header className="modal-header">
      <div><p className="eyebrow">확인된 현재 구성</p><h1 id="environment-title">개발 및 저장환경</h1></div>
      <button ref={closeRef} className="outline-button" type="button" onClick={onClose}>닫기</button>
    </header>
    <div className="modal-scroll">
      <section className="modal-section">
        <h2>현재 실행 중인 구성</h2>
        <p>현재 미리보기는 React와 Vite 화면, FastAPI와 Uvicorn 서버, SQLite 데이터베이스로 실행됩니다.</p>
        <div className="table-wrap"><table><thead><tr><th>구성</th><th>확인된 상태</th><th>역할</th></tr></thead><tbody>
          <tr><td>React와 Vite</td><td>실행 중</td><td>브라우저 화면과 개발 미리보기를 제공합니다.</td></tr>
          <tr><td>FastAPI와 Uvicorn</td><td>실행 중</td><td>등록, 조회, 집계와 CSV 파일 응답을 처리합니다.</td></tr>
          <tr><td>SQLite</td><td>사용 중</td><td>등록 데이터, 문서, 메모와 이력을 저장합니다.</td></tr>
        </tbody></table></div>
      </section>
      <section className="modal-section">
        <h2>데이터 저장 방식</h2>
        <div className="table-wrap"><table><thead><tr><th>자료</th><th>저장 위치</th><th>저장 형태</th><th>유지 범위</th></tr></thead><tbody>{storage.map(row => <tr key={row.item}><td>{row.item}</td><td>{row.location}</td><td>{row.form}</td><td>{row.retention}</td></tr>)}</tbody></table></div>
      </section>
      <section className="modal-section">
        <h2>기술 상세 보기</h2>
        <div className="table-wrap"><table><thead><tr><th>항목</th><th>확인된 실행 정보</th></tr></thead><tbody>
          <tr><td>화면과 API 연결</td><td>브라우저 화면은 미리보기 경로의 API를 요청하고, Vite가 내부 FastAPI 서버로 전달합니다.</td></tr>
          <tr><td>API 처리</td><td>FastAPI와 Uvicorn이 등록, 조회, 집계와 CSV 파일 응답을 처리합니다.</td></tr>
          <tr><td>현재 데이터베이스</td><td>Python 표준 SQLite 연결을 사용하며 등록 데이터·문서·메모·이력을 저장합니다.</td></tr>
        </tbody></table></div>
        <p className="notice-line">클라우드, 별도 마운트와 실행환경 종료 뒤의 영구 저장 정책은 프로젝트 내부에서 확인되지 않았습니다.</p>
      </section>
      <section className="modal-section"><h2>오픈소스 및 라이선스</h2><div className="table-wrap"><table><thead><tr><th>이름</th><th>버전</th><th>라이선스</th><th>공식 프로젝트</th></tr></thead><tbody>{licenses.map(row => <tr key={row.name}><td>{row.name}</td><td>{row.version}</td><td>{row.license}</td><td><a href={row.url} target="_blank" rel="noreferrer">공식 프로젝트 열기</a></td></tr>)}</tbody></table></div></section>
    </div>
  </Modal>
}
