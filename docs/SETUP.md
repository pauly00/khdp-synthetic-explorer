[← 프로젝트 README로 돌아가기](../README.md)

# 설치 및 실행 안내

## 전제

현재 프로젝트는 Linux 작업 경로 `/workspace`를 기준으로 작성되었습니다.

- API 데이터베이스 기본 경로: `/workspace/data/app.db`
- 등록 CSV 원본 보관 경로: `/workspace/data/khdp_files/`
- 업로드 조각 임시 경로: `/workspace/data/khdp_uploads/`
- 환경 변수 `APP_DB_PATH`로 SQLite DB 경로만 변경할 수 있습니다.

`STORE_DIR`와 `UPLOAD_DIR`은 현재 코드에서 `/workspace/...`로 고정되어 있습니다. 따라서 **Windows 네이티브에서 경로 수정 없이 실행하는 방법은 검증되지 않았습니다.** Windows에서는 WSL2의 Ubuntu 등 `/workspace` 경로를 만들 수 있는 Linux 환경 사용을 권장합니다. 이 문서는 Windows에서 직접 시험한 기록이 아닙니다.

## 필요한 도구

- Node.js 및 npm
- Python 3
- FastAPI와 Uvicorn (`requirements.txt`에 기록됨)

프로젝트의 `package.json`에 정의된 화면 의존성은 React, React DOM, Vite, TypeScript 및 React용 타입입니다.

## Windows에서 권장하는 실행 흐름: WSL2

1. Windows에서 WSL2와 Ubuntu를 준비합니다.
2. WSL 터미널에서 프로젝트를 `/workspace`에 두거나, 프로젝트 위치를 `/workspace`로 연결합니다.
3. 프로젝트 루트에서 다음을 실행합니다.

```bash
npm install
python3 -m pip install -r requirements.txt
```

4. 첫 번째 터미널에서 API 서버를 시작합니다.

```bash
cd /workspace
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

5. 두 번째 터미널에서 화면 서버를 시작합니다.

```bash
cd /workspace
npm run dev
```

Vite 설정은 `/api/` 및 미리보기 하위 경로의 API 요청을 `http://127.0.0.1:8000`으로 전달합니다. API를 먼저 실행하지 않으면 화면의 조회 요청이 실패합니다.

## Windows 네이티브 실행 참고 (미검증)

다음은 일반적인 PowerShell 명령 예시입니다. 그러나 앞서 설명한 `/workspace` 고정 경로 때문에, 현재 코드 그대로의 완전한 실행은 검증되지 않았습니다.

```powershell
npm install
py -m pip install -r requirements.txt
py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
npm run dev
```

Windows 네이티브 지원이 필요하면 실행 전에 백엔드의 파일 저장 경로 정책을 Windows 경로 또는 환경 변수 기반으로 바꾸는 별도 작업이 필요합니다. 이 문서 작성에서는 코드를 변경하지 않았습니다.

## 실행 확인

API 서버가 실행되면 다음 요청은 JSON `{"ok":true}`를 반환해야 합니다.

```bash
wget -qO- http://127.0.0.1:8000/api/health
```

Windows PowerShell에서는 다음과 같이 확인할 수 있습니다.

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health | Select-Object -Expand Content
```

이 명령의 Windows 네이티브 전체 실행은 미검증이며, API 서버가 실제로 기동된 경우의 확인 방법만 안내합니다.

## 데이터 포함 여부

- 소스 코드에 SQLite DB와 원본 CSV가 항상 포함된다고 가정하면 안 됩니다.
- 현재 실행 환경에는 `data/` 아래에 DB·원본 보관 폴더·업로드 임시 폴더가 있을 수 있으나, 소스 다운로드나 배포 묶음에 포함되는지는 배포 방식에 따라 달라집니다.
- 원본 CSV 또는 `app.db`를 다른 환경에 복사할 때는 개인정보·데이터 이용조건·보존정책을 별도로 확인해야 합니다.

데이터 구조와 등록 규칙은 [데이터 안내](DATA_GUIDE.md), API 경로는 [API 안내](API.md), 오류 확인은 [문제 해결](TROUBLESHOOTING.md)을 참고하세요.
