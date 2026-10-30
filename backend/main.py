import csv
import hashlib
import io
import json
import os
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
DB_PATH = os.environ.get('APP_DB_PATH', '/workspace/data/app.db')
STORE_DIR = Path('/workspace/data/khdp_files')
UPLOAD_DIR = Path('/workspace/data/khdp_uploads')
DATASETS = {
    'person': {'label':'환자 기본정보','description':'사람별 생년월일과 원본 성별 값입니다.','table':'khdp_person','key':'person_id','required':['person_id','year_of_birth','month_of_birth','day_of_birth'],'columns':['person_id','year_of_birth','month_of_birth','day_of_birth','gender_concept_id'],'used':'진단 분석과 조건별 집계'},
    'condition_occurrence': {'label':'진단 기록','description':'사람별 진단 코드와 기록 시작일입니다.','table':'khdp_condition','key':'condition_occurrence_id','required':['condition_occurrence_id','person_id','condition_concept_id','condition_start_date'],'columns':['condition_occurrence_id','person_id','condition_concept_id','condition_start_date'],'used':'진단 분석과 조건별 집계'},
    'concept': {'label':'코드 사전','description':'숫자 의료 코드를 원문 명칭과 연결합니다.','table':'khdp_concept','key':'concept_id','required':['concept_id','concept_name'],'columns':['concept_id','concept_name'],'used':'진단, 검사, 약물 명칭 표시'},
    'measurement': {'label':'검사 기록','description':'검사 코드, 결과값, 단위와 기록일입니다.','table':'khdp_measurement','key':'measurement_id','required':['measurement_id','person_id','measurement_concept_id'],'columns':['measurement_id','person_id','measurement_concept_id','measurement_date','value_as_number','value_as_concept_id','unit_concept_id','value_source_value'],'used':'검사 기록'},
    'drug_exposure': {'label':'약물 기록','description':'약물 코드와 노출 시작·종료 기록입니다.','table':'khdp_drug','key':'drug_exposure_id','required':['drug_exposure_id','person_id','drug_concept_id'],'columns':['drug_exposure_id','person_id','drug_concept_id','drug_exposure_start_date','drug_exposure_end_date'],'used':'약물 기록'},
    'visit_occurrence': {'label':'방문 기록','description':'방문 유형과 시작·종료 기록입니다.','table':'khdp_visit','key':'visit_occurrence_id','required':['visit_occurrence_id','person_id','visit_concept_id'],'columns':['visit_occurrence_id','person_id','visit_concept_id','visit_start_date','visit_end_date'],'used':'방문 및 관찰 기간'},
    'observation_period': {'label':'관찰 기간','description':'사람별 관찰 가능 기간입니다.','table':'khdp_observation_period','key':'observation_period_id','required':['observation_period_id','person_id','observation_period_start_date','observation_period_end_date'],'columns':['observation_period_id','person_id','observation_period_start_date','observation_period_end_date'],'used':'방문 및 관찰 기간'},
    'observation': {'label':'관찰 기록','description':'기타 관찰 코드 기록입니다.','table':'khdp_observation','key':'observation_id','required':['observation_id','person_id','observation_concept_id'],'columns':['observation_id','person_id','observation_concept_id','observation_date'],'used':'데이터 개요'},
    'procedure_occurrence': {'label':'처치 기록','description':'시술과 처치 코드 기록입니다.','table':'khdp_procedure','key':'procedure_occurrence_id','required':['procedure_occurrence_id','person_id','procedure_concept_id'],'columns':['procedure_occurrence_id','person_id','procedure_concept_id','procedure_date'],'used':'데이터 개요'},
    'death': {'label':'사망 정보','description':'사망 관련 원본 기록입니다.','table':'khdp_death','key':'person_id','required':['person_id'],'columns':['person_id','death_date','cause_concept_id'],'used':'데이터 개요'},
    'note': {'label':'서술 기록','description':'서술형 기록입니다.','table':'khdp_note','key':'note_id','required':[],'columns':[],'used':'내용 미리보기','generic':True},
    'provider': {'label':'제공자','description':'의료 제공자 정보입니다.','table':'khdp_provider','key':'provider_id','required':[],'columns':[],'used':'내용 미리보기','generic':True},
    'care_site': {'label':'진료 기관','description':'진료 장소 정보입니다.','table':'khdp_care_site','key':'care_site_id','required':[],'columns':[],'used':'내용 미리보기','generic':True},
    'location': {'label':'위치','description':'위치 관련 정보입니다.','table':'khdp_location','key':'location_id','required':[],'columns':[],'used':'내용 미리보기','generic':True},
    'device_exposure': {'label':'기기 노출','description':'의료기기 사용 기록입니다.','table':'khdp_device_exposure','key':'device_exposure_id','required':[],'columns':[],'used':'내용 미리보기','generic':True},
    'specimen': {'label':'검체','description':'검체 정보입니다.','table':'khdp_specimen','key':'specimen_id','required':[],'columns':[],'used':'내용 미리보기','generic':True},
}
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS trials (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,approval_number TEXT NOT NULL UNIQUE,approval_date TEXT NOT NULL,condition_name TEXT NOT NULL,organization TEXT NOT NULL,status TEXT NOT NULL,purpose TEXT NOT NULL,description TEXT NOT NULL,source TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_person (person_id TEXT PRIMARY KEY,year_of_birth TEXT,month_of_birth TEXT,day_of_birth TEXT,gender_concept_id TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_condition (condition_occurrence_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,condition_concept_id TEXT NOT NULL,condition_start_date TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_concept (concept_id TEXT PRIMARY KEY,concept_name TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_measurement (measurement_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,measurement_concept_id TEXT NOT NULL,measurement_date TEXT,value_as_number TEXT,value_as_concept_id TEXT,unit_concept_id TEXT,value_source_value TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_drug (drug_exposure_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,drug_concept_id TEXT NOT NULL,drug_exposure_start_date TEXT,drug_exposure_end_date TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_visit (visit_occurrence_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,visit_concept_id TEXT NOT NULL,visit_start_date TEXT,visit_end_date TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_observation_period (observation_period_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,observation_period_start_date TEXT NOT NULL,observation_period_end_date TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_observation (observation_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,observation_concept_id TEXT NOT NULL,observation_date TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_procedure (procedure_occurrence_id TEXT PRIMARY KEY,person_id TEXT NOT NULL,procedure_concept_id TEXT NOT NULL,procedure_date TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_death (person_id TEXT PRIMARY KEY,death_date TEXT,cause_concept_id TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_measurement_summary (concept_id TEXT PRIMARY KEY,concept_name TEXT NOT NULL,record_count INTEGER NOT NULL,people_count INTEGER NOT NULL,numeric_count INTEGER NOT NULL,missing_count INTEGER NOT NULL,units TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_drug_summary (concept_id TEXT PRIMARY KEY,concept_name TEXT NOT NULL,record_count INTEGER NOT NULL,people_count INTEGER NOT NULL,first_date TEXT,last_date TEXT)')
        for table in ('khdp_note','khdp_provider','khdp_care_site','khdp_location','khdp_device_exposure','khdp_specimen'):
            c.execute(f'CREATE TABLE IF NOT EXISTS {table} (row_key TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_import_meta (dataset TEXT PRIMARY KEY,filename TEXT NOT NULL,imported_rows INTEGER NOT NULL,unique_people INTEGER NOT NULL DEFAULT 0,invalid_rows INTEGER NOT NULL DEFAULT 0,imported_at TEXT NOT NULL,validation_note TEXT NOT NULL DEFAULT \'\',new_rows INTEGER NOT NULL DEFAULT 0,duplicate_rows INTEGER NOT NULL DEFAULT 0,conflict_rows INTEGER NOT NULL DEFAULT 0)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_history (id INTEGER PRIMARY KEY AUTOINCREMENT,dataset TEXT NOT NULL,action TEXT NOT NULL,filename TEXT,rows_count INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,note TEXT NOT NULL DEFAULT \'\')')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_documents (kind TEXT PRIMARY KEY,filename TEXT NOT NULL,content TEXT NOT NULL,uploaded_at TEXT NOT NULL,summary TEXT NOT NULL DEFAULT \'\',checks TEXT NOT NULL DEFAULT \'\')')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_upload_sessions (session_id TEXT PRIMARY KEY,dataset TEXT NOT NULL,filename TEXT NOT NULL,mode TEXT NOT NULL,total_chunks INTEGER NOT NULL,total_bytes INTEGER NOT NULL,received_bytes INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT \'전송 중\',error_text TEXT NOT NULL DEFAULT \'\',created_at TEXT NOT NULL,updated_at TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS khdp_upload_chunks (session_id TEXT NOT NULL,chunk_index INTEGER NOT NULL,chunk_size INTEGER NOT NULL,checksum TEXT NOT NULL,PRIMARY KEY(session_id,chunk_index))')
        c.execute('CREATE INDEX IF NOT EXISTS idx_measurement_concept_person ON khdp_measurement(measurement_concept_id, person_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_drug_concept_person ON khdp_drug(drug_concept_id, person_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_observation_person ON khdp_observation_period(person_id, observation_period_start_date)')
        cols = {r[1] for r in c.execute('PRAGMA table_info(khdp_person)')}
        if 'gender_concept_id' not in cols:
            c.execute('ALTER TABLE khdp_person ADD COLUMN gender_concept_id TEXT')
    refresh_summaries()
def refresh_summaries():
    with get_db() as c:
        c.execute('DELETE FROM khdp_measurement_summary')
        c.execute("INSERT INTO khdp_measurement_summary SELECT m.measurement_concept_id,COALESCE(c.concept_name,'명칭 확인 필요'),COUNT(*),COUNT(DISTINCT m.person_id),SUM(CASE WHEN TRIM(COALESCE(m.value_as_number,''))<>'' THEN 1 ELSE 0 END),SUM(CASE WHEN TRIM(COALESCE(m.value_as_number,''))='' THEN 1 ELSE 0 END),GROUP_CONCAT(DISTINCT NULLIF(TRIM(m.unit_concept_id),'')) FROM khdp_measurement m LEFT JOIN khdp_concept c ON c.concept_id=m.measurement_concept_id GROUP BY m.measurement_concept_id")
        c.execute('DELETE FROM khdp_drug_summary')
        c.execute("INSERT INTO khdp_drug_summary SELECT d.drug_concept_id,COALESCE(c.concept_name,'명칭 확인 필요'),COUNT(*),COUNT(DISTINCT d.person_id),MIN(NULLIF(d.drug_exposure_start_date,'')),MAX(NULLIF(d.drug_exposure_end_date,'')) FROM khdp_drug d LEFT JOIN khdp_concept c ON c.concept_id=d.drug_concept_id GROUP BY d.drug_concept_id")
app = FastAPI()
init_db()
class NotePayload(BaseModel):
    summary: str = ''
    checks: str = ''
class UploadStart(BaseModel):
    session_id: str
    filename: str
    mode: str
    total_chunks: int
    total_bytes: int
def count(c, dataset):
    return c.execute(f"SELECT COUNT(*) FROM {DATASETS[dataset]['table']}").fetchone()[0]
def parse_ref(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, '기준일 형식이 올바르지 않습니다.')
def birth(row):
    try:
        return date(int(row['year_of_birth']), int(row['month_of_birth']), int(row['day_of_birth']))
    except (ValueError, TypeError):
        return None
def required(*keys):
    with get_db() as c:
        missing = [f'{key}.csv' for key in keys if count(c, key) == 0]
    if missing:
        raise HTTPException(409, '분석에 필요한 자료가 없습니다: ' + ', '.join(missing))
def norm(value):
    return '' if value is None else str(value).strip()
def normalize_values(values):
    return tuple(norm(value) for value in values)
def parse_csv_file(path, dataset):
    spec = DATASETS[dataset]
    try:
        stream = open(path, 'r', encoding='utf-8-sig', newline='')
    except UnicodeDecodeError:
        raise HTTPException(400, 'UTF-8 또는 UTF-8 BOM 형식의 CSV만 등록할 수 있습니다.')
    with stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise HTTPException(400, '헤더 행을 찾을 수 없습니다.')
        headers = [(header or '').strip() for header in reader.fieldnames]
        if spec.get('generic'):
            rows, read_rows = [], 0
            key_name = spec['key'] if spec['key'] in headers else None
            for index, rawrow in enumerate(reader, start=1):
                read_rows += 1
                row = {key: norm(rawrow.get(key)) for key in headers}
                row_key = row.get(key_name) or f'row-{index}'
                rows.append((row_key, json.dumps(row, ensure_ascii=False, separators=(',', ':'))))
            return rows, 0, read_rows
        missing = set(spec['required']) - set(headers)
        if missing:
            raise HTTPException(400, '필수 열이 없습니다: ' + ', '.join(sorted(missing)))
        rows, invalid, read_rows = [], 0, 0
        for rawrow in reader:
            read_rows += 1
            row = {(key or '').strip(): norm(value) for key, value in rawrow.items()}
            values = tuple(row.get(key, '') for key in spec['columns'])
            if all(row.get(key, '') for key in spec['required']):
                rows.append(values)
            else:
                invalid += 1
    return rows, invalid, read_rows
def session_dir(session_id):
    return UPLOAD_DIR / session_id
def session_info(session_id):
    with get_db() as c:
        row = c.execute('SELECT * FROM khdp_upload_sessions WHERE session_id=?', (session_id,)).fetchone()
    if not row:
        raise HTTPException(404, '업로드 작업을 찾을 수 없습니다.')
    return dict(row)
def data_status():
    with get_db() as c:
        meta = {row['dataset']: dict(row) for row in c.execute('SELECT * FROM khdp_import_meta')}
        tables = []
        for key, spec in DATASETS.items():
            stored = count(c, key) if spec['table'] else 0
            item = meta.get(key)
            if stored:
                state = '분석 가능' if spec['table'] and spec['used'] != '분석 기능 미구현' else '기록 있음'
            elif item:
                state = '등록됐으나 기록 없음'
            else:
                state = '미등록'
            if item:
                item['stored_rows'] = stored
            tables.append({'dataset':key,'label':spec['label'],'description':spec['description'],'used':spec['used'],'meta':item,'state':state,'registration_ready':bool(spec['table'])})
        present = {key: count(c, key) > 0 for key in ('person','condition_occurrence','concept')}
        issues = {
            'ready': all(present.values()),
            'unmatched_conditions': c.execute('SELECT COUNT(DISTINCT person_id) FROM khdp_condition WHERE person_id NOT IN (SELECT person_id FROM khdp_person)').fetchone()[0] if present['person'] and present['condition_occurrence'] else None,
            'unknown_codes': c.execute('SELECT COUNT(DISTINCT condition_concept_id) FROM khdp_condition WHERE condition_concept_id NOT IN (SELECT concept_id FROM khdp_concept)').fetchone()[0] if present['condition_occurrence'] and present['concept'] else None,
        }
        history = [dict(row) for row in c.execute('SELECT * FROM khdp_history ORDER BY id DESC LIMIT 30')]
    return {'ready':all(present.values()),'analysis_ready':present['person'] and present['condition_occurrence'],'tables':tables,'history':history,'issues':issues}
def apply_import(dataset, filename, mode, csv_path):
    spec = DATASETS[dataset]
    rows, invalid, read_rows = parse_csv_file(csv_path, dataset)
    keys = [row[0] for row in rows]
    if len(keys) != len(set(keys)):
        raise HTTPException(400, '파일 안에 같은 기본 키가 중복되어 있습니다. 기존 데이터는 유지됩니다.')
    now = datetime.now().isoformat(timespec='seconds')
    new = duplicate = conflict = 0
    try:
        with get_db() as c:
            c.execute('BEGIN')
            if spec.get('generic'):
                if mode == 'replace':
                    c.execute(f'DELETE FROM {spec["table"]}')
                    if rows: c.executemany(f'INSERT INTO {spec["table"]}(row_key,payload) VALUES(?,?)', rows)
                    new = len(rows)
                else:
                    for values in rows:
                        old = c.execute(f'SELECT payload FROM {spec["table"]} WHERE row_key=?', (values[0],)).fetchone()
                        if not old:
                            c.execute(f'INSERT INTO {spec["table"]}(row_key,payload) VALUES(?,?)', values); new += 1
                        elif old['payload'] == values[1]: duplicate += 1
                        else: conflict += 1
            elif mode == 'replace':
                c.execute(f'DELETE FROM {spec["table"]}')
                if rows:
                    c.executemany(f"INSERT INTO {spec['table']} ({','.join(spec['columns'])}) VALUES ({','.join('?' * len(spec['columns']))})", rows)
                new = len(rows)
            else:
                for values in rows:
                    old = c.execute(f"SELECT {','.join(spec['columns'])} FROM {spec['table']} WHERE {spec['key']}=?", (values[0],)).fetchone()
                    if not old:
                        c.execute(f"INSERT INTO {spec['table']} ({','.join(spec['columns'])}) VALUES ({','.join('?' * len(spec['columns']))})", values)
                        new += 1
                    elif normalize_values(tuple(old)) == normalize_values(values):
                        duplicate += 1
                    else:
                        conflict += 1
            stored = count(c, dataset)
            people = c.execute(f"SELECT COUNT(DISTINCT person_id) FROM {spec['table']}").fetchone()[0] if 'person_id' in spec['columns'] else stored
            note = f"{('전체 교체' if mode == 'replace' else '추가 등록')} 완료: 읽은 {read_rows}행, 신규 {new}행, 중복 {duplicate}행, 충돌 {conflict}행, 오류 {invalid}행, 저장 {stored}행"
            c.execute('INSERT OR REPLACE INTO khdp_import_meta(dataset,filename,imported_rows,unique_people,invalid_rows,imported_at,validation_note,new_rows,duplicate_rows,conflict_rows) VALUES(?,?,?,?,?,?,?,?,?,?)', (dataset, Path(filename or f'{dataset}.csv').name, stored, people, invalid, now, note, new, duplicate, conflict))
            c.execute('INSERT INTO khdp_history(dataset,action,filename,rows_count,created_at,note) VALUES(?,?,?,?,?,?)', (dataset, '전체 교체' if mode == 'replace' else '추가 등록', filename, read_rows, now, note))
        shutil.copyfile(csv_path, STORE_DIR / f'{dataset}.csv')
        if dataset in ('measurement','drug_exposure','concept'):
            refresh_summaries()
    except sqlite3.Error as error:
        raise HTTPException(400, f'저장 중 오류가 발생했습니다: {error}')
    return {'read_rows':read_rows,'new_rows':new,'duplicate_rows':duplicate,'conflict_rows':conflict,'invalid_rows':invalid,'stored_rows':stored}
@app.get('/api/health')
def health():
    return {'ok': True}
@app.get('/api/data/status')
def status():
    return data_status()
@app.get('/api/data/person-conflicts')
def person_conflicts():
    with get_db() as c:
        meta = c.execute("SELECT * FROM khdp_import_meta WHERE dataset='person'").fetchone()
        recent = c.execute("SELECT created_at,filename,note FROM khdp_history WHERE dataset='person' AND action='추가 등록' ORDER BY id DESC LIMIT 1").fetchone()
        stored_with_gender = c.execute("SELECT COUNT(*) FROM khdp_person WHERE NULLIF(trim(gender_concept_id),'') IS NOT NULL").fetchone()[0]
        total = count(c,'person')
    return {'stored_rows':total,'stored_with_gender':stored_with_gender,'last_import':dict(meta) if meta else None,'last_history':dict(recent) if recent else None,'comparison_rule':'기본 키가 같을 때 person_id, year_of_birth, month_of_birth, day_of_birth, gender_concept_id를 비교합니다. NULL과 빈 문자열은 모두 비어 있음으로 비교합니다. 기존에 비어 있던 성별 값과 새 파일의 실제 성별 값은 실제 차이로 보며, 추가 등록으로 덮어쓰지 않습니다.','next_action':'성별처럼 기존 값과 다른 열을 반영하려면 원본 파일을 확인한 뒤 전체 교체를 사용해 주세요.'}
@app.post('/api/data/upload/{dataset}/start')
def upload_start(dataset: str, payload: UploadStart):
    if dataset not in DATASETS or not DATASETS[dataset]['table']:
        raise HTTPException(400, '현재 등록 기능이 준비된 자료가 아닙니다.')
    if payload.mode not in ('append', 'replace') or payload.total_chunks < 1 or payload.total_bytes < 0:
        raise HTTPException(400, '업로드 정보를 확인해 주세요.')
    safe_id = ''.join(ch for ch in payload.session_id if ch.isalnum() or ch in '-_')
    if safe_id != payload.session_id:
        raise HTTPException(400, '업로드 식별자를 확인해 주세요.')
    now = datetime.now().isoformat(timespec='seconds')
    folder = session_dir(payload.session_id)
    folder.mkdir(parents=True, exist_ok=True)
    with get_db() as c:
        existing = c.execute('SELECT * FROM khdp_upload_sessions WHERE session_id=?', (payload.session_id,)).fetchone()
        if existing:
            if existing['dataset'] != dataset or existing['total_chunks'] != payload.total_chunks or existing['total_bytes'] != payload.total_bytes:
                raise HTTPException(409, '같은 업로드 식별자가 다른 파일에 사용되었습니다.')
        else:
            c.execute('INSERT INTO khdp_upload_sessions(session_id,dataset,filename,mode,total_chunks,total_bytes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)', (payload.session_id,dataset,Path(payload.filename).name,payload.mode,payload.total_chunks,payload.total_bytes,now,now))
    return session_info(payload.session_id)
@app.put('/api/data/upload/{session_id}/chunk/{chunk_index}')
async def upload_chunk(session_id: str, chunk_index: int, request: Request):
    info = session_info(session_id)
    if info['status'] not in ('전송 중', '실패'):
        raise HTTPException(409, '현재 작업에는 조각을 추가할 수 없습니다.')
    if chunk_index < 0 or chunk_index >= info['total_chunks']:
        raise HTTPException(400, '조각 번호를 확인해 주세요.')
    raw = await request.body()
    if not raw:
        raise HTTPException(400, '전송된 조각이 비어 있습니다.')
    if len(raw) > 700_000:
        raise HTTPException(413, '요청 용량 제한으로 조각을 받지 못했습니다. 더 작은 조각으로 다시 시도해 주세요.')
    digest = hashlib.sha256(raw).hexdigest()
    folder = session_dir(session_id)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{chunk_index:08d}.part'
    with get_db() as c:
        current = c.execute('SELECT checksum,chunk_size FROM khdp_upload_chunks WHERE session_id=? AND chunk_index=?', (session_id,chunk_index)).fetchone()
        if current:
            if current['checksum'] == digest:
                return session_info(session_id)
            raise HTTPException(409, '같은 조각 번호에 다른 내용이 전송되었습니다.')
        target.write_bytes(raw)
        c.execute('INSERT INTO khdp_upload_chunks(session_id,chunk_index,chunk_size,checksum) VALUES(?,?,?,?)', (session_id,chunk_index,len(raw),digest))
        received = c.execute('SELECT COALESCE(SUM(chunk_size),0) FROM khdp_upload_chunks WHERE session_id=?', (session_id,)).fetchone()[0]
        c.execute('UPDATE khdp_upload_sessions SET received_bytes=?,status=?,error_text=?,updated_at=? WHERE session_id=?', (received,'전송 중','',datetime.now().isoformat(timespec='seconds'),session_id))
    return session_info(session_id)
@app.get('/api/data/upload/{session_id}')
def upload_status(session_id: str):
    info = session_info(session_id)
    with get_db() as c:
        info['received_chunks'] = c.execute('SELECT COUNT(*) FROM khdp_upload_chunks WHERE session_id=?', (session_id,)).fetchone()[0]
    return info
@app.post('/api/data/upload/{session_id}/complete')
def upload_complete(session_id: str):
    info = session_info(session_id)
    if info['status'] == '완료':
        return {'status':'완료','result':data_status()}
    with get_db() as c:
        chunks = [row['chunk_index'] for row in c.execute('SELECT chunk_index FROM khdp_upload_chunks WHERE session_id=? ORDER BY chunk_index', (session_id,))]
    if chunks != list(range(info['total_chunks'])):
        raise HTTPException(409, '누락된 전송 조각이 있어 적재를 시작할 수 없습니다.')
    if info['received_bytes'] != info['total_bytes']:
        raise HTTPException(409, '전송된 용량이 원본 파일과 일치하지 않습니다.')
    folder = session_dir(session_id)
    assembled = folder / 'source.csv'
    try:
        with open(assembled, 'wb') as output:
            for index in chunks:
                with open(folder / f'{index:08d}.part', 'rb') as part:
                    shutil.copyfileobj(part, output, length=1024 * 1024)
        with get_db() as c:
            c.execute('UPDATE khdp_upload_sessions SET status=?,error_text=?,updated_at=? WHERE session_id=?', ('적재 중','',datetime.now().isoformat(timespec='seconds'),session_id))
        result = apply_import(info['dataset'], info['filename'], info['mode'], assembled)
        with get_db() as c:
            c.execute('UPDATE khdp_upload_sessions SET status=?,error_text=?,updated_at=? WHERE session_id=?', ('완료','',datetime.now().isoformat(timespec='seconds'),session_id))
        return {'status':'완료','import':result,'result':data_status()}
    except HTTPException as error:
        with get_db() as c:
            c.execute('UPDATE khdp_upload_sessions SET status=?,error_text=?,updated_at=? WHERE session_id=?', ('실패',str(error.detail),datetime.now().isoformat(timespec='seconds'),session_id))
        raise
    finally:
        if assembled.exists():
            assembled.unlink()
@app.delete('/api/data/upload/{session_id}')
def upload_cancel(session_id: str):
    session_info(session_id)
    with get_db() as c:
        c.execute('DELETE FROM khdp_upload_chunks WHERE session_id=?', (session_id,))
        c.execute('DELETE FROM khdp_upload_sessions WHERE session_id=?', (session_id,))
    shutil.rmtree(session_dir(session_id), ignore_errors=True)
    return {'ok': True}
@app.delete('/api/data/{dataset}')
def data_delete(dataset: str):
    if dataset not in DATASETS or not DATASETS[dataset]['table']:
        raise HTTPException(400, '현재 등록 기능이 준비된 자료가 아닙니다.')
    with get_db() as c:
        c.execute(f"DELETE FROM {DATASETS[dataset]['table']}")
        c.execute('DELETE FROM khdp_import_meta WHERE dataset=?', (dataset,))
        c.execute('INSERT INTO khdp_history(dataset,action,filename,rows_count,created_at,note) VALUES(?,?,?,?,?,?)', (dataset,'삭제','',0,datetime.now().isoformat(timespec='seconds'),'해당 자료를 삭제했습니다.'))
    if dataset in ('measurement','drug_exposure','concept'):
        refresh_summaries()
    return data_status()
@app.get('/api/synthetic/concepts')
def concepts(q: str = ''):
    required('person','condition_occurrence')
    with get_db() as c:
        term = f'%{q.strip()}%'
        rows = c.execute("SELECT DISTINCT d.condition_concept_id concept_id,COALESCE(cn.concept_name,'명칭 확인 필요') concept_name FROM khdp_condition d LEFT JOIN khdp_concept cn ON cn.concept_id=d.condition_concept_id WHERE d.condition_concept_id LIKE ? OR COALESCE(cn.concept_name,'') LIKE ? ORDER BY concept_name,concept_id LIMIT 100", (term,term)).fetchall()
    return [dict(row) for row in rows]
@app.get('/api/diagnoses/distribution')
def distribution(q: str = '', sort: str = 'people', limit: int = 20):
    required('person','condition_occurrence')
    limit = min(max(limit,1),100)
    order = 'people_count DESC,record_count DESC' if sort == 'people' else 'record_count DESC,people_count DESC'
    with get_db() as c:
        total = count(c,'person')
        term = f'%{q.strip()}%'
        rows = c.execute(f"SELECT d.condition_concept_id concept_id,COALESCE(cn.concept_name,'명칭 확인 필요') concept_name,COUNT(DISTINCT CASE WHEN p.person_id IS NOT NULL THEN d.person_id END) people_count,COUNT(*) record_count FROM khdp_condition d LEFT JOIN khdp_person p ON p.person_id=d.person_id LEFT JOIN khdp_concept cn ON cn.concept_id=d.condition_concept_id WHERE d.condition_concept_id LIKE ? OR COALESCE(cn.concept_name,'') LIKE ? GROUP BY d.condition_concept_id,cn.concept_name ORDER BY {order} LIMIT ?", (term,term,limit)).fetchall()
    return {'total_people':total,'items':[dict(row) | {'ratio':(row['people_count'] / total * 100 if total else 0)} for row in rows]}
@app.get('/api/diagnoses/{concept_id}')
def diagnosis_detail(concept_id: str, reference_date: str = '2025-12-31'):
    required('person','condition_occurrence')
    ref = parse_ref(reference_date)
    with get_db() as c:
        label = c.execute('SELECT concept_name FROM khdp_concept WHERE concept_id=?', (concept_id,)).fetchone()
        base = 'FROM khdp_condition d JOIN khdp_person p ON p.person_id=d.person_id WHERE d.condition_concept_id=? AND date(d.condition_start_date)<=date(?)'
        summary = c.execute('SELECT COUNT(DISTINCT d.person_id) people_count,COUNT(*) record_count,MIN(d.condition_start_date) first_date,MAX(d.condition_start_date) last_date ' + base, (concept_id,reference_date)).fetchone()
        rows = c.execute('SELECT DISTINCT p.* ' + base, (concept_id,reference_date)).fetchall()
        bands = {'0–17세':0,'18–39세':0,'40–64세':0,'65세 이상':0,'판별 불가':0}
        sexes = {}
        for row in rows:
            born = birth(row)
            if not born or born > ref:
                bands['판별 불가'] += 1
            else:
                age = ref.year - born.year - ((ref.month,ref.day) < (born.month,born.day))
                bands['0–17세' if age <= 17 else '18–39세' if age <= 39 else '40–64세' if age <= 64 else '65세 이상'] += 1
            value = row['gender_concept_id'] or '미상 또는 미저장'
            sexes[value] = sexes.get(value,0) + 1
        years = c.execute("SELECT strftime('%Y',date(condition_start_date)) year,COUNT(DISTINCT person_id) people_count FROM khdp_condition WHERE condition_concept_id=? AND date(condition_start_date)<=date(?) AND strftime('%Y',date(condition_start_date)) IS NOT NULL GROUP BY year ORDER BY year", (concept_id,reference_date)).fetchall()
    return {'concept_id':concept_id,'concept_name':label['concept_name'] if label else '명칭 확인 필요','reference_date':reference_date,**dict(summary),'age_bands':[{'label':key,'count':value} for key,value in bands.items()],'sex':[{'value':key,'count':value} for key,value in sexes.items()],'sex_stored':any(row['gender_concept_id'] for row in rows),'years':[dict(row) for row in years]}
def cohort(reference_date, concept_id, min_age, max_age):
    ref = parse_ref(reference_date)
    required('person','condition_occurrence')
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(400,'나이 범위를 확인해 주세요.')
    with get_db() as c:
        people = c.execute('SELECT * FROM khdp_person').fetchall()
        ids = {row['person_id'] for row in people}
        concept = None
        base = ids
        if concept_id:
            named = c.execute('SELECT concept_name FROM khdp_concept WHERE concept_id=?', (concept_id,)).fetchone()
            concept = {'concept_id':concept_id,'concept_name':named['concept_name'] if named else '명칭 확인 필요'}
            base = {row[0] for row in c.execute('SELECT DISTINCT person_id FROM khdp_condition WHERE condition_concept_id=? AND date(condition_start_date)<=date(?)', (concept_id,reference_date))}
        selected, unavailable = set(), 0
        age_filter = min_age is not None or max_age is not None
        for person in people:
            if person['person_id'] not in base:
                continue
            born = birth(person)
            if not age_filter:
                selected.add(person['person_id'])
            elif not born or born > ref:
                unavailable += 1
            else:
                age = ref.year - born.year - ((ref.month,ref.day) < (born.month,born.day))
                if (min_age is None or age >= min_age) and (max_age is None or age <= max_age):
                    selected.add(person['person_id'])
    return {'reference_date':reference_date,'min_age':min_age,'max_age':max_age,'concept':concept,'total_people':len(ids),'diagnosis_people':len(base),'age_filtered_people':len(selected),'age_unavailable_excluded':unavailable,'age_excluded':len(base)-len(selected),'has_age_filter':age_filter,'has_diagnosis':bool(concept_id)}
@app.get('/api/synthetic/query')
def synthetic_query(reference_date: str, concept_id: Optional[str] = None, min_age: Optional[int] = None, max_age: Optional[int] = None):
    return cohort(reference_date,concept_id,min_age,max_age)
@app.get('/api/synthetic/export')
def synthetic_export(reference_date: str, concept_id: Optional[str] = None, min_age: Optional[int] = None, max_age: Optional[int] = None):
    result = cohort(reference_date,concept_id,min_age,max_age)
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    diagnosis = result['concept']
    writer.writerow(['항목','값'])
    writer.writerows([
        ['데이터 설명','KHDP Synthetic-SNUH v4 합성 데이터의 집계'],
        ['기준일',result['reference_date']],
        ['선택 진단명',diagnosis['concept_name'] if diagnosis else '선택 안 함'],
        ['선택 진단 코드',diagnosis['concept_id'] if diagnosis else '선택 안 함'],
        ['최소 나이',result['min_age'] if result['min_age'] is not None else '제한 없음'],
        ['최대 나이',result['max_age'] if result['max_age'] is not None else '제한 없음'],
        ['진단 조건에 해당하는 고유 인원수',result['diagnosis_people']],
        ['연령 조건 적용 후 고유 인원수',result['age_filtered_people']],
        ['연령 조건으로 제외된 인원수',result['age_excluded']],
        ['생년월일 판별 불가로 제외된 인원수',result['age_unavailable_excluded']],
    ])
    return Response(output.getvalue().encode('utf-8-sig'), media_type='text/csv; charset=utf-8', headers={'Content-Disposition':'attachment; filename="synthetic-cohort-summary.csv"'})
def extra_distribution(dataset, code_col, person_col='person_id'):
    if dataset not in DATASETS:
        raise HTTPException(404,'자료를 찾을 수 없습니다.')
    with get_db() as c:
        if count(c,dataset) == 0:
            raise HTTPException(409,f'{dataset}.csv를 먼저 등록해 주세요.')
        table = DATASETS[dataset]['table']
        rows = c.execute(f"SELECT x.{code_col} concept_id,COALESCE(n.concept_name,'명칭 확인 필요') concept_name,COUNT(*) record_count,COUNT(DISTINCT x.{person_col}) people_count,MIN(x.{DATASETS[dataset]['columns'][3]}) first_date,MAX(x.{DATASETS[dataset]['columns'][3]}) last_date FROM {table} x LEFT JOIN khdp_concept n ON n.concept_id=x.{code_col} GROUP BY x.{code_col},n.concept_name ORDER BY people_count DESC,record_count DESC LIMIT 100").fetchall()
    return [dict(row) for row in rows]
@app.get('/api/measurements')
def measurements(q: str = '', sort: str = 'records', offset: int = 0, limit: int = 20):
    with get_db() as c:
        if count(c,'measurement') == 0:
            raise HTTPException(409,'measurement.csv를 먼저 등록해 주세요.')
        limit, offset = min(max(limit,1),100), max(offset,0)
        order = 'record_count DESC, concept_id ASC' if sort == 'records' else 'concept_name COLLATE NOCASE ASC, concept_id ASC'
        term = f'%{q.strip()}%'
        rows = c.execute(f"SELECT * FROM khdp_measurement_summary WHERE concept_id LIKE ? OR concept_name LIKE ? ORDER BY {order} LIMIT ? OFFSET ?", (term,term,limit + 1,offset)).fetchall()
    items = [dict(row) for row in rows[:limit]]
    return {'items':items,'has_more':len(rows)>limit,'next_offset':offset+len(items)}
@app.get('/api/measurements/{concept_id}')
def measurement_detail(concept_id: str):
    with get_db() as c:
        if count(c,'measurement') == 0:
            raise HTTPException(409,'measurement.csv를 먼저 등록해 주세요.')
        name = c.execute('SELECT concept_name FROM khdp_concept WHERE concept_id=?', (concept_id,)).fetchone()
        rows = c.execute("SELECT COALESCE(NULLIF(unit_concept_id,''),'단위 미상') unit,COUNT(*) record_count,COUNT(DISTINCT person_id) people_count,COUNT(value_as_number) numeric_count,MIN(CAST(value_as_number AS REAL)) min_value,MAX(CAST(value_as_number AS REAL)) max_value,AVG(CAST(value_as_number AS REAL)) avg_value,SUM(CASE WHEN value_as_number IS NULL OR value_as_number='' THEN 1 ELSE 0 END) nonnumeric_count FROM khdp_measurement WHERE measurement_concept_id=? GROUP BY unit ORDER BY unit", (concept_id,)).fetchall()
    return {'concept_id':concept_id,'concept_name':name['concept_name'] if name else '명칭 확인 필요','units':[dict(row) for row in rows]}
@app.get('/api/drugs')
def drugs(q: str = '', sort: str = 'records', offset: int = 0, limit: int = 20):
    with get_db() as c:
        if count(c,'drug_exposure') == 0:
            raise HTTPException(409,'drug_exposure.csv를 먼저 등록해 주세요.')
        limit, offset = min(max(limit,1),100), max(offset,0)
        order = 'record_count DESC, concept_id ASC' if sort == 'records' else 'concept_name COLLATE NOCASE ASC, concept_id ASC'
        term = f'%{q.strip()}%'
        rows = c.execute(f"SELECT * FROM khdp_drug_summary WHERE concept_id LIKE ? OR concept_name LIKE ? ORDER BY {order} LIMIT ? OFFSET ?", (term,term,limit + 1,offset)).fetchall()
        quality = c.execute("SELECT SUM(CASE WHEN drug_exposure_start_date IS NULL OR trim(drug_exposure_start_date)='' THEN 1 ELSE 0 END) start_missing,SUM(CASE WHEN drug_exposure_end_date IS NULL OR trim(drug_exposure_end_date)='' THEN 1 ELSE 0 END) end_missing,SUM(CASE WHEN (drug_exposure_start_date IS NOT NULL AND trim(drug_exposure_start_date)!='' AND date(drug_exposure_start_date) IS NULL) OR (drug_exposure_end_date IS NOT NULL AND trim(drug_exposure_end_date)!='' AND date(drug_exposure_end_date) IS NULL) THEN 1 ELSE 0 END) invalid_format,SUM(CASE WHEN date(drug_exposure_start_date) IS NOT NULL AND date(drug_exposure_end_date) IS NOT NULL AND date(drug_exposure_end_date)<date(drug_exposure_start_date) THEN 1 ELSE 0 END) reversed_dates FROM khdp_drug").fetchone()
    items = [dict(row) for row in rows[:limit]]
    return {'items':items,'has_more':len(rows)>limit,'next_offset':offset+len(items),'quality':dict(quality)}
@app.get('/api/visits')
def visits():
    with get_db() as c:
        if count(c,'visit_occurrence') == 0:
            raise HTTPException(409,'visit_occurrence.csv를 먼저 등록해 주세요.')
        types = c.execute('SELECT visit_concept_id concept_id,COUNT(*) record_count,COUNT(DISTINCT person_id) people_count FROM khdp_visit GROUP BY visit_concept_id ORDER BY record_count DESC').fetchall()
        years = c.execute("SELECT strftime('%Y',date(visit_start_date)) year,COUNT(*) record_count,COUNT(DISTINCT person_id) people_count FROM khdp_visit WHERE strftime('%Y',date(visit_start_date)) IS NOT NULL GROUP BY year ORDER BY year").fetchall()
        periods = c.execute("SELECT COUNT(*) record_count,COUNT(DISTINCT person_id) people_count,AVG(CASE WHEN date(observation_period_start_date) IS NOT NULL AND date(observation_period_end_date) IS NOT NULL AND date(observation_period_end_date)>=date(observation_period_start_date) THEN julianday(observation_period_end_date)-julianday(observation_period_start_date)+1 END) avg_days,SUM(CASE WHEN date(observation_period_start_date) IS NULL OR date(observation_period_end_date) IS NULL OR date(observation_period_end_date)<date(observation_period_start_date) THEN 1 ELSE 0 END) invalid_dates FROM khdp_observation_period").fetchone() if count(c,'observation_period') else None
    return {'types':[dict(row) for row in types],'years':[dict(row) for row in years],'periods':dict(periods) if periods else None}
@app.get('/api/observation-periods')
def observation_periods(q: str = '', page: int = 1, size: int = 20):
    with get_db() as c:
        if count(c,'observation_period') == 0:
            raise HTTPException(409,'observation_period.csv를 먼저 등록해 주세요.')
        page, size = max(page,1), min(max(size,5),100)
        term = f'%{q.strip()}%'
        where = 'WHERE person_id LIKE ?'
        total = c.execute(f'SELECT COUNT(*) FROM khdp_observation_period {where}', (term,)).fetchone()[0]
        rows = c.execute(f"SELECT person_id,observation_period_start_date,observation_period_end_date,CASE WHEN date(observation_period_start_date) IS NOT NULL AND date(observation_period_end_date) IS NOT NULL AND date(observation_period_end_date)>=date(observation_period_start_date) THEN CAST(julianday(observation_period_end_date)-julianday(observation_period_start_date)+1 AS INTEGER) END days FROM khdp_observation_period {where} ORDER BY person_id,observation_period_start_date LIMIT ? OFFSET ?", (term,size,(page-1)*size)).fetchall()
        bands = c.execute("SELECT CASE WHEN days BETWEEN 1 AND 30 THEN '1–30일' WHEN days BETWEEN 31 AND 90 THEN '31–90일' WHEN days BETWEEN 91 AND 365 THEN '91–365일' WHEN days > 365 THEN '366일 이상' END label,COUNT(*) record_count FROM (SELECT CASE WHEN date(observation_period_start_date) IS NOT NULL AND date(observation_period_end_date) IS NOT NULL AND date(observation_period_end_date)>=date(observation_period_start_date) THEN CAST(julianday(observation_period_end_date)-julianday(observation_period_start_date)+1 AS INTEGER) END days FROM khdp_observation_period) WHERE days IS NOT NULL GROUP BY label ORDER BY MIN(days)").fetchall()
        invalid = c.execute("SELECT COUNT(*) FROM khdp_observation_period WHERE date(observation_period_start_date) IS NULL OR date(observation_period_end_date) IS NULL OR date(observation_period_end_date)<date(observation_period_start_date)").fetchone()[0]
    return {'page':page,'size':size,'total':total,'rows':[dict(row) for row in rows],'bands':[dict(row) for row in bands],'invalid_dates':invalid}
@app.get('/api/data/{dataset}/preview')
def data_preview(dataset: str, q: str = '', offset: int = 0, limit: int = 20):
    if dataset not in DATASETS or not DATASETS[dataset].get('generic'):
        raise HTTPException(404, '내용 미리보기를 지원하지 않는 자료입니다.')
    with get_db() as c:
        if count(c, dataset) == 0:
            raise HTTPException(409, f'{dataset}.csv를 먼저 등록해 주세요.')
        term, limit, offset = f'%{q.strip()}%', min(max(limit,1),100), max(offset,0)
        rows = c.execute(f"SELECT row_key,payload FROM {DATASETS[dataset]['table']} WHERE row_key LIKE ? OR payload LIKE ? ORDER BY row_key COLLATE NOCASE LIMIT ? OFFSET ?", (term,term,limit+1,offset)).fetchall()
    items = [{'row_key':row['row_key'],'values':json.loads(row['payload'])} for row in rows[:limit]]
    return {'items':items,'has_more':len(rows)>limit,'next_offset':offset+len(items)}
@app.get('/api/documents')
def documents():
    with get_db() as c:
        return [dict(row) for row in c.execute('SELECT kind,filename,uploaded_at,summary,checks FROM khdp_documents ORDER BY kind')]
@app.get('/api/documents/{kind}')
def document(kind: str):
    if kind not in ('README','LICENSE'):
        raise HTTPException(404,'자료를 찾을 수 없습니다.')
    with get_db() as c:
        row = c.execute('SELECT * FROM khdp_documents WHERE kind=?', (kind,)).fetchone()
    if not row:
        raise HTTPException(404,'등록된 문서가 없습니다.')
    return dict(row)
@app.post('/api/documents/{kind}')
async def document_import(kind: str, request: Request):
    if kind not in ('README','LICENSE'):
        raise HTTPException(400,'지원하지 않는 문서입니다.')
    try:
        payload = await request.json()
        content = __import__('base64').b64decode(payload.get('content',''),validate=True).decode('utf-8-sig')
        filename = payload.get('filename','')
    except UnicodeDecodeError:
        raise HTTPException(400,'UTF-8 문서만 등록할 수 있습니다.')
    except Exception:
        raise HTTPException(400,'문서 내용을 읽을 수 없습니다.')
    with get_db() as c:
        c.execute("INSERT OR REPLACE INTO khdp_documents(kind,filename,content,uploaded_at,summary,checks) VALUES(?,?,?,?,COALESCE((SELECT summary FROM khdp_documents WHERE kind=?),''),COALESCE((SELECT checks FROM khdp_documents WHERE kind=?),''))", (kind,Path(filename or kind).name,content,datetime.now().isoformat(timespec='seconds'),kind,kind))
    return document(kind)
@app.put('/api/documents/{kind}/notes')
def document_notes(kind: str, payload: NotePayload):
    with get_db() as c:
        changed = c.execute('UPDATE khdp_documents SET summary=?,checks=? WHERE kind=?', (payload.summary,payload.checks,kind)).rowcount
    if not changed:
        raise HTTPException(404,'등록된 문서가 없습니다.')
    return document(kind)
@app.get('/api/documents/{kind}/download')
def document_download(kind: str):
    item = document(kind)
    return Response(item['content'].encode(),media_type='text/plain; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{item["filename"]}"'})
@app.delete('/api/documents/{kind}')
def document_delete(kind: str):
    with get_db() as c:
        changed = c.execute('DELETE FROM khdp_documents WHERE kind=?', (kind,)).rowcount
    if not changed:
        raise HTTPException(404,'등록된 문서가 없습니다.')
    return {'ok': True}
