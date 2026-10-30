[← 프로젝트 README로 돌아가기](../README.md)

# 데이터 안내

## 데이터 성격

이 서비스는 KHDP Synthetic-SNUH v4 공개 합성 데이터의 CSV를 등록해 탐색하는 시제품입니다. 화면의 인원수는 실제 환자 수나 임상시험 참여 가능 인원을 뜻하지 않습니다.

## CSV별 역할과 연결 키

| CSV | 내부 테이블 | 기본 키 | 주요 연결/용도 |
|---|---|---|---|
| `person.csv` | `khdp_person` | `person_id` | 생년월일·원본 성별 값, 진단 및 조건별 집계의 기준 인원 |
| `condition_occurrence.csv` | `khdp_condition` | `condition_occurrence_id` | `person_id`, `condition_concept_id`, 진단일; 진단 분석·조건별 집계 |
| `concept.csv` | `khdp_concept` | `concept_id` | 진단·검사·약물 코드의 명칭 표시 |
| `measurement.csv` | `khdp_measurement` | `measurement_id` | 검사 코드·결과·단위·날짜; 코드별 검사 목록 |
| `drug_exposure.csv` | `khdp_drug` | `drug_exposure_id` | 약물 코드·시작/종료일; 코드별 약물 목록 |
| `visit_occurrence.csv` | `khdp_visit` | `visit_occurrence_id` | 방문 유형과 시작/종료일 |
| `observation_period.csv` | `khdp_observation_period` | `observation_period_id` | 사람별 관찰 가능 기간 |
| `observation.csv` | `khdp_observation` | `observation_id` | 데이터 개요용 기타 관찰 기록 |
| `procedure_occurrence.csv` | `khdp_procedure` | `procedure_occurrence_id` | 데이터 개요용 처치 기록 |
| `death.csv` | `khdp_death` | `person_id` | 데이터 개요용 사망 관련 기록 |
| `note.csv`, `provider.csv`, `care_site.csv`, `location.csv`, `device_exposure.csv`, `specimen.csv` | 각각 `khdp_*` | CSV의 해당 ID 또는 행 번호 | 현재는 JSON 원문 형태의 내용 미리보기용 저장 구조 |

코드 사전에 없는 진단·검사·약물 코드는 기록에서 제외하지 않습니다. 이름은 `명칭 확인 필요`로 표시합니다.

## 등록 전 확인

- CSV는 UTF-8 또는 UTF-8 BOM 인코딩이어야 합니다.
- 필수 열은 자료별로 다릅니다. 서버가 헤더와 필수 값을 검증합니다.
- 하나의 파일 안에서 기본 키가 중복되면 등록을 중단하고 기존 데이터는 유지합니다.
- 서버는 파일명을 정리해 보관하며, 파일 내용 자체의 의미·임상적 타당성은 자동 판정하지 않습니다.

## 추가 등록과 전체 교체

### 추가 등록

기본 키가 없는 행은 새로 저장합니다. 기존 키가 있으면 모든 관리 대상 열을 비교합니다.

- 모든 값이 같음: **동일 중복**으로 계산, 기존 행 유지
- 하나라도 다름: **내용 충돌**로 계산, 기존 행 유지
- 새 키: 신규 저장

예를 들어 `person.csv`는 `person_id`, 생년·월·일, 성별 원본 값을 비교합니다. 빈 문자열과 NULL은 모두 비어 있는 값으로 비교합니다.

### 전체 교체

검증과 적재가 성공했을 때만 해당 자료 테이블을 새 파일 내용으로 바꿉니다. 실패하면 기존 테이블을 유지하도록 트랜잭션으로 처리합니다.

## 원본과 이력

적재 성공 뒤 원본 CSV 사본은 `/workspace/data/khdp_files/<자료종류>.csv`에 보관합니다. SQLite에는 최신 등록 정보와 최근 변경 이력이 저장됩니다. 소스 배포본에 이 파일들이 항상 포함된다는 뜻은 아닙니다.

## 집계 규칙

### 조건별 집단 비교

1. 기준일 이후의 진단 기록은 제외합니다.
2. 특정 진단을 고르면 해당 코드의 기록이 있는 `person_id`를 한 번씩만 셉니다.
3. 진단을 고르지 않으면 등록된 `person` 전체를 기준으로 합니다.
4. 나이는 기준일에서 생년월일을 사용해 계산한 만 나이입니다.
5. 나이 조건이 있을 때 생년월일을 해석할 수 없거나 기준일보다 미래이면 연령 조건 통과 인원에 넣지 않고 `생년월일 판별 불가` 제외로 계산합니다.
6. 최소·최대 나이 경계값은 포함합니다.

### 진단·검사·약물 목록

- 진단: 코드별 기록 수와 연결된 고유 인원 수를 보여 줍니다.
- 검사: 코드별 기록 수, 고유 인원, 숫자 결과 여부, 누락, 단위를 요약합니다. 다른 단위는 자동으로 합치지 않습니다.
- 약물: 코드별 기록 수, 고유 인원, 시작·종료 날짜 범위와 날짜 품질 수치를 보여 줍니다.

API 세부 형식은 [API 안내](API.md)를 참고하세요.
