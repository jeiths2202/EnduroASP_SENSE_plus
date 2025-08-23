# Zabbix UI 설정 가이드 - ABEND 모니터링

## 1. Zabbix UI 접속

**웹 브라우저에서 접속:**
```
http://localhost/zabbix
```

**기본 로그인 정보:**
- 사용자명: `Admin`
- 비밀번호: `zabbix`

## 2. 호스트 등록

### 2.1 호스트 추가
1. **Configuration** → **Hosts** 메뉴 이동
2. **Create host** 버튼 클릭
3. 다음 정보 입력:
   - **Host name**: `OpenASP-AX-Server`
   - **Visible name**: `OpenASP AX Production Server`
   - **Groups**: `Linux servers` 선택
   - **Interfaces**: 
     - Type: `Agent`
     - IP address: `127.0.0.1`
     - Port: `10050`

### 2.2 호스트 활성화
1. **Add** 버튼으로 호스트 저장
2. 호스트 목록에서 **Status** 컬럼이 `Enabled`인지 확인

## 3. ABEND 모니터링 아이템 등록

### 3.1 ABEND 검지 아이템
1. **Configuration** → **Hosts** → **OpenASP-AX-Server** → **Items**
2. **Create item** 클릭
3. 아이템 정보 입력:
   ```
   Name: ABEND Detection Check
   Type: Zabbix agent
   Key: openasp.abend.check
   Type of information: Text
   Update interval: 30s
   Applications: OpenASP Monitoring
   ```

### 3.2 ABEND 카운트 아이템
1. **Create item** 클릭
2. 아이템 정보 입력:
   ```
   Name: ABEND Count
   Type: Zabbix agent  
   Key: openasp.abend.count
   Type of information: Numeric (unsigned)
   Update interval: 30s
   Applications: OpenASP Monitoring
   ```

## 4. 트리거 설정

### 4.1 ABEND 발생 트리거
1. **Configuration** → **Hosts** → **OpenASP-AX-Server** → **Triggers**
2. **Create trigger** 클릭
3. 트리거 정보 입력:
   ```
   Name: ABEND Detected on OpenASP System
   Severity: High
   Expression: last(/OpenASP-AX-Server/openasp.abend.count)>0
   Description: ABEND has been detected in OpenASP AX system. Auto-fix pipeline should be triggered.
   ```

### 4.2 ABEND 급증 트리거
1. **Create trigger** 클릭
2. 트리거 정보 입력:
   ```
   Name: Multiple ABENDs Detected
   Severity: Disaster
   Expression: last(/OpenASP-AX-Server/openasp.abend.count)>2
   Description: Multiple ABENDs detected. System may be unstable.
   ```

## 5. 알림 설정

### 5.1 미디어 타입 설정
1. **Administration** → **Media types**
2. **Email** 미디어 타입 편집 또는 **Create media type** 클릭

### 5.2 사용자 알림 설정
1. **Administration** → **Users** → **Admin** → **Media** 탭
2. **Add** 버튼으로 알림 미디어 추가

### 5.3 액션 설정
1. **Configuration** → **Actions** → **Trigger actions**
2. **Create action** 클릭
3. 액션 정보 입력:
   ```
   Name: ABEND Auto-Fix Notification
   Conditions: Trigger name contains "ABEND"
   Operations: Send message to Admin
   Recovery operations: Send recovery message
   ```

## 6. 대시보드 설정

### 6.1 ABEND 모니터링 대시보드
1. **Monitoring** → **Dashboard** → **Create dashboard**
2. 위젯 추가:
   - **Graph**: ABEND Count 추세
   - **Plain text**: 최근 ABEND 정보
   - **Trigger status**: ABEND 트리거 상태

## 7. 설정 확인

### 7.1 연결 테스트
```bash
# Zabbix 에이전트 테스트
zabbix_get -s 127.0.0.1 -k "openasp.abend.check"
zabbix_get -s 127.0.0.1 -k "openasp.abend.count"
```

### 7.2 로그 확인
```bash
# Zabbix 서버 로그
tail -f /var/log/zabbix/zabbix_server.log

# Zabbix 에이전트 로그  
tail -f /var/log/zabbix/zabbix_agentd.log
```

## 8. ABEND 테스트 시나리오

1. **ABEND 발생**: F3키 테스트로 ABEND 트리거
2. **Zabbix 검지**: 30초 내 트리거 활성화 확인
3. **알림 확인**: 이메일/SMS 알림 수신 확인
4. **대시보드 확인**: 실시간 상태 업데이트 확인

## 현재 상태

- ✅ Zabbix 서버: 실행 중
- ✅ Zabbix 에이전트: 실행 중  
- ✅ UserParameter: 설정 완료
- ⚠️ 호스트 등록: UI에서 수동 등록 필요
- ⚠️ 아이템/트리거: UI에서 수동 설정 필요

## 자동화 스크립트 (선택사항)

더 자세한 자동화가 필요하시면 Zabbix API를 사용한 스크립트를 제공할 수 있습니다.