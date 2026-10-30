[← 프로젝트 README로 돌아가기](../README.md)

# 구성 구조

## 개요

```text
브라우저
  └─ React + TypeScript 화면 (src/)
       └─ api() 요청 도우미
            └─ Vite 개발 서버 프록시
                 └─ FastAPI (backend/main.py)
                      ├─ SQLite (/workspace/data/app.db)
                      ├─ 원본 CSV (/workspace/data/khdp_files/)
                      └─ 업로드 조각 (/workspace/data/khdp_uploads/)
```

## 화면

`src/`는 React 화면과 사용자 조작을 담당합니다.

- `src/App.tsx`: 메뉴, 화면 전환, 도움말·환경 모달 조합
- `src/components/`: 데이터 관리, 진단, 검사, 약물, 방문, 조건별 집계, 자료실 화면
- `src/lib/api.ts`: 현재 화면의 base 경로를 고려해 `api/<경로>`로 요청하는 공통 함수
- `src/vibe-design/`: 플랫폼 소유 디자인 토큰 및 기본 스타일

프런트엔드는 절대 `/api/...`가 아니라 `api()` 도우미를 통해 요청합니다. 미리보기처럼 하위 경로에서 제공될 때도 API 경로를 유지하기 위한 방식입니다.

## Vite 프록시

`vite.config.ts`는 다음 두 모양의 요청을 FastAPI로 전달합니다.

- `/api/...`
- `/preview/<프로젝트 식별자>/api/...`

프록시 대상은 `http://127.0.0.1:8000`이며, 미리보기 접두 경로만 제거합니다. FastAPI 라우트는 모두 `/api`로 시작합니다.

## API와 SQLite

`backend/main.py`가 FastAPI 앱과 SQLite 접근을 함께 제공합니다. 요청마다 `sqlite3` 연결을 열고, 행은 `sqlite3.Row`로 읽습니다.

주요 저장 테이블은 다음과 같습니다.

- 업무 데이터: `khdp_person`, `khdp_condition`, `khdp_concept`, `khdp_measurement`, `khdp_drug`, `khdp_visit`, `khdp_observation_period` 등
- 대용량 목록 요약: `khdp_measurement_summary`, `khdp_drug_summary`
- 운영 정보: `khdp_import_meta`, `khdp_history`, `khdp_upload_sessions`, `khdp_upload_chunks`
- 자료실: `khdp_documents`

앱 시작 시 `CREATE TABLE IF NOT EXISTS`로 필요한 테이블과 인덱스를 준비하고, 검사·약물 요약 테이블을 갱신합니다. 이는 기존 DB를 초기화하는 동작이 아닙니다.

## CSV 저장과 등록 처리

브라우저는 CSV를 조각으로 나누어 업로드합니다. 서버는 업로드 세션과 조각의 SHA-256 값을 저장하고, 모든 조각이 모인 뒤 하나의 CSV로 복원해 검증·적재합니다. 적재가 성공하면 자료 종류별 원본 사본을 `khdp_files`에 저장합니다.

임시 조각은 `khdp_uploads`에 보관되며, 사용자가 취소하면 해당 세션 정보와 폴더를 삭제합니다. 적재 완료 뒤 조립용 `source.csv`는 정리되지만 세션 폴더 보존 정책 전체는 코드만으로 장기 보장을 하지 않습니다.

## 문서 원문 저장

자료실의 README.md와 LICENSE.txt는 프로젝트 루트의 개발 문서와 다릅니다. 자료실 원문과 메모는 SQLite의 `khdp_documents`에 저장되며, 화면에서 등록·조회·내려받기·삭제합니다. 프로젝트 루트 `README.md`와 `docs/`는 개발자용 파일로 자료실에 자동 등록되지 않습니다.

데이터 관계는 [데이터 안내](DATA_GUIDE.md), 요청·응답은 [API 안내](API.md)를 참고하세요.
