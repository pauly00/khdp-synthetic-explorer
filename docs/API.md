[← 프로젝트 README로 돌아가기](../README.md)

# API 안내

모든 API는 FastAPI의 `/api` 접두 경로를 사용합니다. 화면은 `src/lib/api.ts`의 `api()` 도우미를 통해 요청하며, Vite는 `/api/` 또는 `/preview/<식별자>/api/` 요청을 내부 API 서버로 프록시합니다.

응답 예시는 구조 설명용입니다. 등록 데이터에 따라 배열·수치는 달라집니다.

## 상태와 데이터 관리

| 메서드·경로 | 입력 | 응답/설명 |
|---|---|---|
| `GET /api/health` | 없음 | `{ "ok": true }` |
| `GET /api/data/status` | 없음 | 등록 상태, 자료별 메타데이터, 최근 이력, 분석 준비 상태 |
| `GET /api/data/person-conflicts` | 없음 | person 비교 규칙과 최근 등록 정보 |
| `POST /api/data/upload/{dataset}/start` | 경로 `dataset`; JSON `session_id`, `filename`, `mode`, `total_chunks`, `total_bytes` | 업로드 세션 생성 또는 조회 |
| `PUT /api/data/upload/{session_id}/chunk/{chunk_index}` | 바이너리 CSV 조각 | 조각 저장 후 세션 정보 |
| `GET /api/data/upload/{session_id}` | 없음 | 세션 및 수신 조각 수 |
| `POST /api/data/upload/{session_id}/complete` | 없음 | 적재 결과와 최신 데이터 상태 |
| `DELETE /api/data/upload/{session_id}` | 없음 | 취소 결과 `{ "ok": true }` |
| `DELETE /api/data/{dataset}` | 경로 `dataset` | 해당 자료 삭제 뒤 최신 상태 |
| `GET /api/data/{dataset}/preview` | `q`, `offset`, `limit` | generic 자료의 원문 JSON 미리보기. 현재 generic 자료 외에는 404 |

`mode`는 `append` 또는 `replace`입니다. 조각 하나가 700,000바이트를 넘으면 413이 반환됩니다.

## 진단과 조건별 집계

| 메서드·경로 | 입력 | 응답/설명 |
|---|---|---|
| `GET /api/synthetic/concepts` | `q` (선택) | 진단 코드·명칭 배열, 최대 100개 |
| `GET /api/diagnoses/distribution` | `q`, `sort=people|records`, `limit` | `total_people`, 코드별 `items` |
| `GET /api/diagnoses/{concept_id}` | `reference_date` | 코드명, 인원·기록 수, 날짜 범위, 연령대·성별·연도별 요약 |
| `GET /api/synthetic/query` | `reference_date` 필수, `concept_id`, `min_age`, `max_age` 선택 | 조건별 고유 인원 집계 |
| `GET /api/synthetic/export` | query와 동일 | UTF-8 BOM CSV 파일 응답 |

집계 응답의 주요 필드:

```json
{
  "reference_date": "2025-12-31",
  "min_age": 15,
  "max_age": 44,
  "concept": { "concept_id": "433456", "concept_name": "예시" },
  "total_people": 10000,
  "diagnosis_people": 8,
  "age_filtered_people": 3,
  "age_unavailable_excluded": 0,
  "age_excluded": 5,
  "has_age_filter": true,
  "has_diagnosis": true
}
```

위 숫자는 형식 설명이며 현재 DB의 실제 값으로 보장되지 않습니다.

## 검사·약물·방문

| 메서드·경로 | 입력 | 응답/설명 |
|---|---|---|
| `GET /api/measurements` | `q`, `sort=records|name`, `offset`, `limit` | `items`, `has_more`, `next_offset`; 요약 테이블 기반 |
| `GET /api/measurements/{concept_id}` | 없음 | 검사 코드의 단위별 기록·인원·수치 요약 |
| `GET /api/drugs` | `q`, `sort=records|name`, `offset`, `limit` | 목록 페이지와 날짜 품질 `quality` |
| `GET /api/visits` | 없음 | 방문 유형, 연도별 수치, 관찰 기간 요약 |
| `GET /api/observation-periods` | `q`, `page`, `size` | 관찰 기간 행, 기간 구간, 날짜 오류 수 |

`measurement.csv`, `drug_exposure.csv`, `visit_occurrence.csv`, `observation_period.csv`가 없을 때는 해당 API가 409을 반환합니다.

## 자료실 문서

| 메서드·경로 | 입력 | 응답/설명 |
|---|---|---|
| `GET /api/documents` | 없음 | 문서 목록. 문서가 없으면 `[]` |
| `GET /api/documents/{kind}` | `kind=README|LICENSE` | 원문과 메모 |
| `POST /api/documents/{kind}` | Base64 UTF-8 내용과 파일명 JSON | 문서 등록 또는 교체 |
| `PUT /api/documents/{kind}/notes` | `summary`, `checks` JSON | 메모 저장 |
| `GET /api/documents/{kind}/download` | `kind` | 원문 파일 다운로드 |
| `DELETE /api/documents/{kind}` | `kind` | 문서 삭제 |

문서가 아직 없는데 특정 원문이나 메모를 요청하면 404입니다. 목록 경로의 빈 배열과 경로 오류는 구분해야 합니다.

## 오류 형식

FastAPI 검증·업무 오류는 일반적으로 JSON의 `detail` 필드로 설명을 반환합니다. 화면은 JSON이 아닌 오류 응답도 읽어 메시지로 표시하도록 처리합니다.

등록 규칙 및 의미는 [데이터 안내](DATA_GUIDE.md), 사용자 흐름은 [사용자 안내](USER_GUIDE.md)를 참고하세요.
