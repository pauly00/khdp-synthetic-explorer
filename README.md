# 합성 의료데이터 탐색
KHDP 공개 합성 데이터인 Synthetic-SNUH v4의 CSV 구성을 살펴보고, 진단·연령 조건에 맞는 **고유 인원수**를 집계해 보는 분석 시제품입니다. 실제 환자 모집, 임상적 판단 또는 KHDP 서비스 대체를 목적으로 하지 않습니다.
KHDP는 데이터를 제공하는 플랫폼이며, 모두의 AI 실험실은 이 프로젝트 개발에 사용한 환경입니다.
## 주요 기능
- CSV 등록·검증·추가 등록·전체 교체와 등록 이력 확인
- 진단, 검사, 약물, 방문·관찰 기간 조회
- 진단 및 연령 조건별 고유 인원수 집계와 CSV 내려받기
- README.md·LICENSE.txt 원문과 메모 관리
## 현재 기술 구성
React + TypeScript + Vite 화면, FastAPI API, SQLite 데이터베이스를 사용합니다. 등록 CSV 원본은 파일 저장소에, 분석·문서·이력 데이터는 SQLite에 저장합니다.
## 실행 요약
개발 환경에서 의존성을 설치한 뒤 FastAPI와 Vite를 각각 실행합니다. 현재 소스는 `/workspace` 경로를 기본 저장 위치로 사용하므로, Windows에서 직접 실행하는 방법과 경로 제약은 [설치 및 실행 안내](docs/SETUP.md)를 먼저 확인하세요.
## 주요 디렉터리
```text
src/                   # 화면과 사용자 조작 처리
backend/               # API와 데이터 처리
docs/                  # 실행 안내와 개발 기록
data/                  # 실행 중 생성·사용되는 SQLite와 CSV 저장소
archive/               # 현재 실행 경로에서 분리한 이전 시험 보관 자료
```
## 상세 문서
- [개발 이력](docs/DEVELOPMENT_HISTORY.md)
- [설치 및 실행 안내](docs/SETUP.md)
- [구성 구조](docs/ARCHITECTURE.md)
- [데이터 안내](docs/DATA_GUIDE.md)
- [사용자 안내](docs/USER_GUIDE.md)
- [API 안내](docs/API.md)
- [문제 해결](docs/TROUBLESHOOTING.md)
- [Java·Spring·H2 이전 시험 기록](docs/MIGRATION_TROUBLESHOOTING.md)
