# PostgreSQL 데이터베이스 분석 보고서

## 📊 시스템 개요

### 기본 정보
- **PostgreSQL 버전**: 15
- **포트**: 5432 (localhost)
- **상태**: 정상 운영 중
- **설치 경로**: `/var/lib/postgresql/15/main`
- **설정 파일**: `/etc/postgresql/15/main/postgresql.conf`

### 인증 정보
- **Zabbix DB 사용자**: `zabbix`
- **Zabbix DB 패스워드**: 저장 위치 `postgres.pass`
- **OpenASP DB 사용자**: `aspuser` (DBA 권한)
- **OpenASP DB 패스워드**: `aspuser123`
- **Zabbix 접속**: `PGPASSWORD=$(cat postgres.pass) psql -h localhost -U zabbix -d zabbix`
- **OpenASP 접속**: `PGPASSWORD=aspuser123 psql -h localhost -U aspuser -d ofasp`

## 🗄️ 데이터베이스 목록 및 크기

| 데이터베이스명 | 소유자 | 크기 | 인코딩 | Collation | 용도 |
|---------------|--------|------|--------|-----------|------|
| **zabbix** | zabbix | **252 MB** | UTF8 | C.UTF-8 | Zabbix 모니터링 시스템 |
| **ofasp** | aspuser | **8.5 MB** | UTF8 | C.UTF-8 | **OpenASP AX 카탈로그 시스템** |
| gitlabhq_production | postgres | 7.7 MB | UTF8 | C.UTF-8 | GitLab (현재 비활성) |
| postgres | postgres | 7.6 MB | UTF8 | C.UTF-8 | 시스템 기본 데이터베이스 |
| template1 | postgres | 7.7 MB | UTF8 | C.UTF-8 | 템플릿 데이터베이스 |
| template0 | postgres | 7.5 MB | UTF8 | C.UTF-8 | 원본 템플릿 |

### 📈 크기 분석
- **전체 데이터베이스 크기**: 약 289 MB
- **Zabbix DB 비중**: 87% (252 MB)
- **OpenASP DB 비중**: 3% (8.5 MB)
- **기타 DB 비중**: 10% (28.5 MB)

## 🎯 Zabbix 데이터베이스 상세 분석

### 📋 핵심 통계
- **테이블 개수**: 188개
- **활성 호스트 수**: 43대
- **총 모니터링 아이템**: 15,643개
- **OpenASP AX 전용 호스트**: 1대

### 🏗️ 주요 테이블 구조

#### 1. hosts 테이블 - 모니터링 대상 호스트
```sql
Table "public.hosts"
Column             | Type                    | Description
-------------------|-------------------------|------------------
hostid             | bigint                  | PRIMARY KEY
proxy_hostid       | bigint                  | 프록시 호스트 ID
host               | character varying(128)  | 호스트명
status             | integer                 | 상태 (0=활성)
name               | character varying(128)  | 표시명
description        | text                    | 설명
tls_connect        | integer                 | TLS 연결 설정
tls_accept         | integer                 | TLS 수락 설정
```

**인덱스**:
- `hosts_pkey`: PRIMARY KEY (hostid)
- `hosts_1`: btree (host) 
- `hosts_2`: btree (status)
- `hosts_4`: btree (name)

**외래키 제약조건**:
- `c_hosts_1`: proxy_hostid → hosts(hostid)
- `c_hosts_2`: maintenanceid → maintenances(maintenanceid)

#### 2. items 테이블 - 모니터링 항목
```sql
Table "public.items"  
Column        | Type                     | Description
--------------|--------------------------|------------------
itemid        | bigint                   | PRIMARY KEY
type          | integer                  | 아이템 타입
hostid        | bigint                   | 호스트 ID (FK)
name          | character varying(255)   | 아이템명
key_          | character varying(2048)  | 모니터링 키
delay         | character varying(1024)  | 수집 주기
history       | character varying(255)   | 히스토리 보관기간
trends        | character varying(255)   | 트렌드 보관기간
status        | integer                  | 상태
value_type    | integer                  | 값 타입
```

**주요 value_type**:
- `0`: Numeric (float)
- `1`: Character
- `2`: Log
- `3`: Numeric (unsigned)  
- `4`: Text

#### 3. 기타 핵심 테이블
- **triggers**: 트리거 정의 (알림 조건)
- **actions**: 액션 정의 (알림 동작)
- **alerts**: 발생한 알림 기록
- **history**: 모니터링 데이터 히스토리
- **trends**: 장기 트렌드 데이터
- **auditlog**: 감사 로그

## 🔧 OpenASP AX 전용 모니터링 설정

### 📊 등록된 호스트 정보
```sql
Host: "OpenASP AX"
Name: "OpenASP AX"
Status: 0 (활성)
Host ID: (자동 생성)
```

### 🎯 커스텀 모니터링 아이템

#### ABEND 감지 시스템
- **openasp.abend.count**: ABEND 발생 개수 추적
- **openasp.abend.check**: ABEND 감지 상태 확인

#### 서비스 상태 모니터링  
- **openasp.service.api**: API 서버 상태 (포트 8000)
- **openasp.service.smed**: SMED Viewer 상태 (포트 3000)  
- **openasp.service.python**: Python 변환 서비스 (포트 3003)
- **openasp.service.refactor**: Refactor 서비스 (포트 3005)
- **openasp.service.manager**: Manager 서비스 (포트 3007)
- **openasp.services.check**: 전체 서비스 상태 체크

#### 시스템 모니터링
- **openasp.logs.check**: 로그 파일 모니터링
- **openasp.dslock.check**: dslock_suite 상태 확인

#### 표준 시스템 모니터링
- **vfs.fs.discovery**: 파일시스템 디스커버리
- **vfs.fs.dependent**: 파일시스템 사용량, 여유공간
- **net.if.discovery**: 네트워크 인터페이스 디스커버리
- **system.cpu**: CPU 사용률
- **vm.memory**: 메모리 사용률

## 🚀 성능 및 운영 상태

### 📈 프로세스 분석
```
Process                    | PID  | Runtime | Memory  | Status
--------------------------|------|---------|---------|--------
postgres (main)           | 857  | 1:39    | 24.3 MB | 정상
checkpointer              | 858  | 1:27    | 126 MB  | 정상  
background writer         | 859  | 0:08    | 11.2 MB | 정상
walwriter                 | 881  | 1:05    | 9.0 MB  | 정상
autovacuum launcher       | 882  | 0:04    | 7.8 MB  | 정상
logical replication       | 883  | 0:00    | 6.5 MB  | 정상
```

### 🔄 활성 연결 상태
- **총 활성 연결**: 28개
- **연결 사용자**: zabbix 
- **연결 유형**: IPv6 localhost (::1)
- **평균 메모리 사용량**: 연결당 약 50MB

### 📊 데이터베이스 통계
```sql
-- 주요 테이블 레코드 수 (추정)
호스트 수: 43개 (활성)
모니터링 아이템: 15,643개
히스토리 데이터: 수백만 건 (자동 정리)
트렌드 데이터: 수십만 건 (장기 보관)
```

## 💡 최적화 권장사항

### ✅ 현재 상태 평가
**강점**:
1. **안정적 운영**: 모든 프로세스 정상 동작
2. **완전한 OpenASP AX 모니터링**: 모든 서비스 실시간 추적
3. **ABEND 자동 감지**: 장애 상황 즉시 탐지
4. **확장 가능**: 새로운 모니터링 항목 추가 용이

### 🔧 개선 권장사항

#### 1. 성능 최적화
```sql
-- 히스토리 데이터 정리 (90일 → 30일)
UPDATE items SET history = '30d' WHERE history = '90d';

-- 트렌드 데이터 정리 (365일 → 180일)  
UPDATE items SET trends = '180d' WHERE trends = '365d';

-- 사용하지 않는 아이템 비활성화
UPDATE items SET status = 1 WHERE key_ LIKE 'vfs.fs.%' AND hostid IN (SELECT hostid FROM hosts WHERE status = 1);
```

#### 2. 연결 풀 관리
```sql
-- postgresql.conf 설정 권장값
max_connections = 50           # 기본 100에서 축소
shared_buffers = 128MB        # 메모리의 25%
effective_cache_size = 512MB  # 전체 메모리의 75%
```

#### 3. 백업 정책
```bash
# 일일 백업 스크립트
#!/bin/bash
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)

# Zabbix DB 백업
pg_dump -h localhost -U zabbix -d zabbix > $BACKUP_DIR/zabbix_$DATE.sql

# 7일 이상 된 백업 파일 삭제
find $BACKUP_DIR -name "zabbix_*.sql" -mtime +7 -delete
```

#### 4. 모니터링 강화
- **슬로우 쿼리 로깅** 활성화
- **연결 수 모니터링** 알림 설정
- **디스크 사용량** 임계값 설정 (80% 경고, 90% 위험)

## 🔍 문제 해결 가이드

### 일반적인 이슈와 해결방안

#### 1. 연결 수 초과
```sql
-- 현재 연결 수 확인
SELECT count(*) FROM pg_stat_activity;

-- 연결별 상태 확인  
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
```

#### 2. 슬로우 쿼리 확인
```sql
-- 실행 시간이 긴 쿼리 조회
SELECT query, state, query_start 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start;
```

#### 3. 디스크 사용량 확인
```sql
-- 테이블별 크기 확인
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 📞 관리 명령어 참고

### 일반적인 관리 작업
```bash
# 서비스 상태 확인
service postgresql status

# 서비스 재시작
service postgresql restart

# 데이터베이스 접속
PGPASSWORD=$(cat /home/aspuser/app/postgres.pass) psql -h localhost -U zabbix -d zabbix

# 백업 생성
pg_dump -h localhost -U zabbix -d zabbix > zabbix_backup.sql

# 백업 복원  
psql -h localhost -U zabbix -d zabbix < zabbix_backup.sql
```

### 모니터링 쿼리
```sql
-- OpenASP AX 호스트의 모든 아이템 조회
SELECT i.name, i.key_, i.status 
FROM items i 
JOIN hosts h ON i.hostid = h.hostid 
WHERE h.host = 'OpenASP AX'
ORDER BY i.name;

-- 최근 알림 조회
SELECT a.subject, a.message, a.sendto, 
       FROM_UNIXTIME(a.clock) as alert_time
FROM alerts a
ORDER BY a.clock DESC 
LIMIT 10;
```

## 🏗️ OpenASP 데이터베이스 상세 분석 

### 📊 데이터베이스 구조
- **데이터베이스명**: `ofasp`
- **소유자**: `aspuser` (DBA 권한)
- **테이블스페이스**: `ofasp` (`/home/aspuser/app/pg_data/ofasp_tablespace`)
- **스키마**: `aspuser`
- **테이블 개수**: 11개

### 📈 데이터 통계
- **볼륨**: 4개 (DISK01, DISK02, TEST, TEST_VOLUME)
- **라이브러리**: 12개 (TESTLIB, PRODLIB, XMLLIB, JAVA, COB, CL, SMED, LAYOUT 등)
- **전체 오브젝트**: 123개
- **프로그램**: 75개 (JAVA, COBOL, CL, SHELL)
- **데이터셋**: 26개 (FB, VB 형식)
- **맵**: 16개 (SMED, HTML)
- **카피북**: 2개
- **작업**: 2개
- **레이아웃**: 1개

### 🗄️ 주요 테이블 구조

#### 1. 계층 구조 테이블
```sql
-- 볼륨 → 라이브러리 → 오브젝트 계층 구조
aspuser.volumes      (4건)   -- DISK01, DISK02, TEST, TEST_VOLUME
aspuser.libraries    (12건)  -- TESTLIB, PRODLIB, JAVA, SMED 등
aspuser.objects      (123건) -- 모든 오브젝트 (PGM, DATASET, MAP 등)
```

#### 2. 오브젝트 타입별 상세 테이블
```sql
aspuser.programs             (75건)  -- JAVA/COBOL/CL/SHELL 프로그램
aspuser.datasets             (26건)  -- FB/VB 데이터셋
aspuser.dataset_conversions  (변환정보) -- SJIS ↔ UTF-8 변환 이력
aspuser.maps                 (16건)  -- SMED/HTML 맵
aspuser.copybooks            (2건)   -- COBOL 카피북
aspuser.jobs                 (2건)   -- 배치 작업
aspuser.layouts              (1건)   -- 레이아웃 정의
```

### 🔍 OpenASP 데이터베이스 접속 및 조회

#### 기본 접속
```bash
# OpenASP 데이터베이스 접속
PGPASSWORD=aspuser123 psql -h localhost -U aspuser -d ofasp

# 테이블 목록 조회
\dt aspuser.*

# 스키마 정보 조회
\dn aspuser
```

#### 데이터 조회 예제
```sql
-- 전체 볼륨과 라이브러리 현황
SELECT v.volume_name, COUNT(l.library_id) as library_count
FROM aspuser.volumes v
LEFT JOIN aspuser.libraries l ON v.volume_id = l.volume_id
GROUP BY v.volume_name;

-- 오브젝트 타입별 통계
SELECT object_type, COUNT(*) as count
FROM aspuser.objects
GROUP BY object_type
ORDER BY count DESC;

-- TESTLIB의 모든 프로그램 조회
SELECT o.object_name, p.pgm_type, p.encoding
FROM aspuser.objects o
JOIN aspuser.programs p ON o.object_id = p.object_id
JOIN aspuser.libraries l ON o.library_id = l.library_id
WHERE l.library_name = 'TESTLIB';

-- 데이터셋 변환 정보 조회
SELECT o.object_name, d.rec_type, d.encoding, dc.source_encoding, dc.target_encoding
FROM aspuser.objects o
JOIN aspuser.datasets d ON o.object_id = d.object_id
LEFT JOIN aspuser.dataset_conversions dc ON d.dataset_id = dc.dataset_id
WHERE o.object_type = 'DATASET';
```

## 🎯 pgAdmin 웹 관리 도구

### 📊 pgAdmin 접속 정보
- **URL**: `http://[도커호스트IP]:3009/pgadmin4/`
- **관리자 이메일**: `admin@enduroax.co.jp`
- **관리자 패스워드**: `admin123`
- **웹서버 포트**: 3009 (Apache2)

### 🔗 PostgreSQL 서버 등록 (pgAdmin에서 사용)

#### 서버 연결 설정
- **Host name/address**: `localhost` (또는 `172.17.0.3`)
- **Port**: `5432`
- **Maintenance database**: `ofasp`
- **Username**: `aspuser`
- **Password**: `aspuser123`

#### 고급 설정 (Advanced 탭)
- **DB restriction**: `ofasp` (중요: 이 설정이 누락되면 테이블이 보이지 않음)

### 🔧 pgAdmin 서버 관리 명령어

#### Apache 웹서버 제어
```bash
# Apache 서비스 상태 확인
service apache2 status

# Apache 서비스 시작
service apache2 start

# Apache 서비스 정지
service apache2 stop

# Apache 서비스 재시작
service apache2 restart

# Apache 설정 다시 로드
service apache2 reload
```

#### pgAdmin 로그 확인
```bash
# pgAdmin 애플리케이션 로그
tail -f /var/log/pgadmin/pgadmin4.log

# Apache 오류 로그
tail -f /var/log/apache2/error.log

# Apache 접근 로그
tail -f /var/log/apache2/access.log
```

### 🎯 테이블 접근 방법
pgAdmin에서 OpenASP 테이블에 접근하려면:
```
Servers → [서버명] → Databases → ofasp → Schemas → aspuser → Tables
```

만약 테이블이 보이지 않는다면:
1. Schemas 노드 우클릭 → Refresh
2. Query Tool에서 직접 쿼리: `SET search_path TO aspuser; \dt`

---

**작성일**: 2025년 9월 1일  
**분석 대상**: PostgreSQL 15 / Zabbix Database / OpenASP Database  
**문서 버전**: 2.0  
**작성자**: Database Admin Agent