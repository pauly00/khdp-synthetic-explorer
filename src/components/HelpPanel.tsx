import { useRef } from 'react'
import Modal from './Modal'
type Page = 'intro'|'overview'|'distribution'|'detail'|'measurements'|'drugs'|'visits'|'cohort'|'management'|'library'
type Props = { page: Page; onClose: () => void; onOpenEnvironment: () => void }
type Guide = { title: string; what: string; how: string; read: string; limits: string }
const guides: Record<Page, Guide> = {
  intro: { title:'서비스 안내', what:'이 서비스는 가상 환자의 의료 기록을 살펴보고, 정한 조건에 해당하는 사람 수를 계산해 보는 시제품입니다. KHDP는 데이터를 제공하는 플랫폼이며, 모두의 AI 실험실은 이 화면을 개발한 환경입니다.', how:'등록된 자료가 있다면 다시 올리지 않아도 됩니다. 데이터 개요에서 자료를 확인한 뒤 진단 분석과 조건별 집단 비교로 이동하세요.', read:'고유 인원수는 같은 사람이 여러 기록을 가져도 한 번만 세는 수입니다.', limits:'실제 환자 모집 규모, 진단 또는 임상시험 참여 가능 여부를 판단하는 서비스가 아닙니다.' },
  overview: { title:'데이터 개요', what:'등록된 CSV 자료와 현재 저장된 기록 수를 확인합니다.', how:'표에서 파일별 등록 상태, 저장 행 수와 연결된 화면을 확인하세요. 등록 자료가 있어도 모든 파일에 전용 분석 화면이 있는 것은 아닙니다.', read:'행은 기록 한 줄입니다. 진단과 검사는 한 사람이 여러 행을 가질 수 있어 행 수와 사람 수가 다를 수 있습니다.', limits:'표의 행 수를 전체 인원수로 해석하면 안 됩니다.' },
  distribution: { title:'진단 분석', what:'등록된 진단 코드와 해당 기록을 가진 고유 인원수를 살펴봅니다.', how:'진단명 또는 코드를 검색하고 목록의 행을 선택하면 정확한 코드 하나의 상세 결과를 볼 수 있습니다.', read:'같은 사람의 반복 진단 기록은 인원수에 한 번만 반영됩니다.', limits:'비슷한 진단이나 하위 진단을 자동으로 합치고, 증상으로 질병을 판단하지 않습니다.' },
  detail: { title:'진단별 상세', what:'선택한 정확한 진단 코드의 기록 수와 고유 인원 분포를 보여줍니다.', how:'기준일을 바꾸면 그 날짜 이후의 진단 기록을 제외해 다시 계산합니다.', read:'연령대, 성별 원본 값, 연도별 인원은 각각 다른 기준의 요약입니다.', limits:'관련 진단을 자동으로 묶거나 실제 환자 상태를 판단하지 않습니다.' },
  measurements: { title:'검사 기록', what:'검사 항목의 이름, 결과값, 단위와 기록일을 확인합니다.', how:'표에서 검사 항목을 선택해 단위별 기록 수와 숫자 결과 요약을 확인하세요.', read:'같은 검사라도 단위가 다르면 값을 바로 비교하거나 합치면 안 됩니다.', limits:'표시된 값만으로 정상 여부나 질병 여부를 판정하지 않습니다.' },
  drugs: { title:'약물 기록', what:'데이터에 포함된 약물 사용 기록과 시작일, 종료일을 살펴봅니다.', how:'약물명과 코드, 기록 수, 날짜 범위를 확인하세요.', read:'시작일·종료일 누락과 날짜 형식 오류는 별도로 집계합니다.', limits:'기록만으로 실제 복용 여부나 치료 효과를 알 수 없습니다.' },
  visits: { title:'방문 및 관찰 기간', what:'의료기관 이용 기록과 데이터에 기록된 관찰 가능 기간을 보여줍니다.', how:'관찰 기간 표에서 환자 번호로 찾고 페이지를 이동해 기록별 기간을 확인하세요.', read:'기간 막대와 구간은 고유 인원이 아니라 관찰 기간 기록 수를 기준으로 합니다.', limits:'관찰 기간 전체를 입원 기간이나 모든 진료 정보가 완전한 기간으로 해석할 수 없습니다.' },
  cohort: { title:'조건별 집단 비교', what:'선택한 진단과 나이 조건에 해당하는 고유 인원수를 조건 적용 전후로 비교합니다.', how:'진단을 고르고 기준일, 필요한 최소·최대 나이를 입력한 뒤 조회하세요. 나이 칸을 비우면 해당 제한을 적용하지 않습니다.', read:'기준일은 진단 기록 포함 여부와 만 나이를 계산하는 날짜입니다. 결과 파일은 현재 조회한 결과와 같은 집계를 저장합니다.', limits:'0명 결과는 오류가 아닐 수 있으며 실제 환자나 임상시험 참여 가능 인원을 뜻하지 않습니다.' },
  management: { title:'데이터 관리', what:'지원 대상 CSV를 등록하고 저장 상태를 관리합니다.', how:'파일을 선택해 추가 등록 또는 전체 교체를 실행하세요. 전체 교체는 검증과 적재가 모두 성공한 경우에만 기존 자료를 바꿉니다.', read:'전송 완료와 서버 적재 완료는 다릅니다. 최종 결과에서 신규, 동일 중복, 실제 충돌, 오류를 구분해 확인하세요.', limits:'파일별 상세 분석 기능이 없을 수 있으며, 삭제하면 해당 자료의 저장 내용을 제거합니다.' },
  library: { title:'자료실', what:'데이터 설명서 README와 이용조건 LICENSE 원문을 보관하고 읽는 화면입니다.', how:'문서를 등록한 뒤 원문을 열고, 필요하면 메모를 따로 저장하세요.', read:'메모는 원문과 별도로 저장됩니다. 이용조건은 LICENSE 원문으로 확인하세요.', limits:'분석 결과를 보여주거나 이용조건을 자동 해석하는 메뉴는 아닙니다.' },
}
export default function HelpPanel({ page, onClose, onOpenEnvironment }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const guide = guides[page]
  const showEnvironment = () => { onClose(); window.setTimeout(onOpenEnvironment, 0) }
  return <Modal titleId="help-title" className="help-modal" onClose={onClose}>
    <header className="modal-header"><div><p className="eyebrow">현재 화면 안내</p><h1 id="help-title">{guide.title}</h1></div><button ref={closeRef} className="outline-button" type="button" onClick={onClose}>닫기</button></header>
    <div className="modal-scroll help-scroll"><section><h2>이 화면은 무엇을 보여주나요?</h2><p>{guide.what}</p></section><section><h2>어떻게 사용하나요?</h2><p>{guide.how}</p></section><section><h2>결과는 어떻게 읽나요?</h2><p>{guide.read}</p></section><section><h2>이 화면에서 알 수 없는 것은 무엇인가요?</h2><p>{guide.limits}</p></section>{page==='intro'&&<section className="help-global"><h2>처음이라면 이렇게 시작하세요</h2><ol><li>데이터 개요에서 등록된 자료를 확인합니다.</li><li>진단 분석에서 들어 있는 진단 기록을 살펴봅니다.</li><li>조건별 집단 비교에서 진단과 나이 조건의 고유 인원수를 확인합니다.</li></ol><p>등록 자료가 이미 있다면 파일을 다시 올리지 않고 바로 분석 화면을 사용할 수 있습니다.</p></section>}<section className="help-global"><h2>실행 환경 확인</h2><p>현재 미리보기의 실행 구성과 데이터 저장 방식은 개발 및 저장환경에서 확인할 수 있습니다.</p><button className="outline-button" type="button" onClick={showEnvironment}>개발 및 저장환경 자세히 보기</button></section></div>
  </Modal>
}
