#!/usr/bin/env python3
"""
Zabbix Auto-Setup Script for ABEND Monitoring
Automatically registers host, items, and triggers for OpenASP ABEND monitoring
"""

import requests
import json
import sys

# Zabbix API 설정
ZABBIX_URL = "http://localhost/zabbix/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

class ZabbixAPI:
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password
        self.auth_token = None
        self.request_id = 1
        
    def authenticate(self):
        """Zabbix API 인증"""
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": self.user,
                "password": self.password
            },
            "id": self.request_id
        }
        
        try:
            response = requests.post(self.url, json=payload, timeout=10)
            result = response.json()
            
            if "result" in result:
                self.auth_token = result["result"]
                print(f"[SUCCESS] Zabbix authentication successful: {self.auth_token[:20]}...")
                return True
            else:
                print(f"[ERROR] Authentication failed: {result.get('error', {}).get('data', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"[ERROR] API connection failed: {e}")
            return False
    
    def api_call(self, method, params):
        """Zabbix API 호출"""
        if not self.auth_token:
            print("[ERROR] 인증되지 않음")
            return None
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": self.auth_token,
            "id": self.request_id
        }
        self.request_id += 1
        
        try:
            response = requests.post(self.url, json=payload, timeout=10)
            result = response.json()
            
            if "result" in result:
                return result["result"]
            else:
                print(f"[ERROR] API 호출 실패 ({method}): {result.get('error', {})}")
                return None
        except Exception as e:
            print(f"[ERROR] API 요청 실패: {e}")
            return None

    def get_hostgroup_id(self, group_name="Linux servers"):
        """호스트 그룹 ID 조회"""
        result = self.api_call("hostgroup.get", {
            "filter": {"name": [group_name]}
        })
        
        if result and len(result) > 0:
            return result[0]["groupid"]
        else:
            print(f"[WARNING] 호스트 그룹 '{group_name}' 찾을 수 없음")
            return None

    def create_host(self):
        """OpenASP AX 호스트 생성"""
        groupid = self.get_hostgroup_id()
        if not groupid:
            return None
            
        # 기존 호스트 확인
        existing = self.api_call("host.get", {
            "filter": {"host": ["OpenASP-AX-Server"]}
        })
        
        if existing and len(existing) > 0:
            print(f"[INFO] 호스트 'OpenASP-AX-Server' 이미 존재: {existing[0]['hostid']}")
            return existing[0]["hostid"]
        
        # 새 호스트 생성
        result = self.api_call("host.create", {
            "host": "OpenASP-AX-Server",
            "name": "OpenASP AX Production Server",
            "groups": [{"groupid": groupid}],
            "interfaces": [{
                "type": 1,  # Agent
                "main": 1,
                "useip": 1,
                "ip": "127.0.0.1",
                "dns": "",
                "port": "10050"
            }]
        })
        
        if result and "hostids" in result:
            hostid = result["hostids"][0]
            print(f"[SUCCESS] 호스트 생성 완료: {hostid}")
            return hostid
        else:
            print("[ERROR] 호스트 생성 실패")
            return None

    def create_items(self, hostid):
        """ABEND 모니터링 아이템 생성"""
        items = [
            {
                "name": "ABEND Detection Check",
                "key_": "openasp.abend.check",
                "hostid": hostid,
                "type": 0,  # Zabbix agent
                "value_type": 4,  # Text
                "delay": "30s",
                "description": "OpenASP ABEND detection monitoring"
            },
            {
                "name": "ABEND Count",
                "key_": "openasp.abend.count", 
                "hostid": hostid,
                "type": 0,  # Zabbix agent
                "value_type": 3,  # Numeric unsigned
                "delay": "30s",
                "description": "Number of ABENDs detected"
            }
        ]
        
        created_items = []
        for item in items:
            # 기존 아이템 확인
            existing = self.api_call("item.get", {
                "hostids": [hostid],
                "filter": {"key_": [item["key_"]]}
            })
            
            if existing and len(existing) > 0:
                print(f"[INFO] 아이템 '{item['name']}' 이미 존재")
                created_items.append(existing[0]["itemid"])
                continue
            
            # 새 아이템 생성
            result = self.api_call("item.create", item)
            if result and "itemids" in result:
                itemid = result["itemids"][0]
                print(f"[SUCCESS] 아이템 생성: {item['name']} ({itemid})")
                created_items.append(itemid)
            else:
                print(f"[ERROR] 아이템 생성 실패: {item['name']}")
        
        return created_items

    def create_triggers(self, hostid):
        """ABEND 트리거 생성"""
        triggers = [
            {
                "description": "ABEND Detected on OpenASP System",
                "expression": f"last(/OpenASP-AX-Server/openasp.abend.count)>0",
                "priority": 4,  # High
                "comments": "ABEND has been detected in OpenASP AX system. Auto-fix pipeline should be triggered."
            },
            {
                "description": "Multiple ABENDs Detected",
                "expression": f"last(/OpenASP-AX-Server/openasp.abend.count)>2",
                "priority": 5,  # Disaster
                "comments": "Multiple ABENDs detected. System may be unstable."
            }
        ]
        
        for trigger in triggers:
            # 기존 트리거 확인
            existing = self.api_call("trigger.get", {
                "hostids": [hostid],
                "filter": {"description": [trigger["description"]]}
            })
            
            if existing and len(existing) > 0:
                print(f"[INFO] 트리거 '{trigger['description']}' 이미 존재")
                continue
            
            # 새 트리거 생성
            result = self.api_call("trigger.create", trigger)
            if result and "triggerids" in result:
                triggerid = result["triggerids"][0]
                print(f"[SUCCESS] 트리거 생성: {trigger['description']} ({triggerid})")
            else:
                print(f"[ERROR] 트리거 생성 실패: {trigger['description']}")

def main():
    print("=" * 60)
    print("  Zabbix ABEND Monitoring Auto Setup Script")
    print("=" * 60)
    
    # Zabbix API 연결
    zapi = ZabbixAPI(ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD)
    
    # 인증
    if not zapi.authenticate():
        print("[FAILED] Zabbix 인증 실패")
        sys.exit(1)
    
    # 호스트 생성
    print("\n[STEP 1] 호스트 생성...")
    hostid = zapi.create_host()
    if not hostid:
        print("[FAILED] 호스트 생성 실패")
        sys.exit(1)
    
    # 아이템 생성
    print("\n[STEP 2] 아이템 생성...")
    item_ids = zapi.create_items(hostid)
    if not item_ids:
        print("[FAILED] 아이템 생성 실패")
        sys.exit(1)
    
    # 트리거 생성
    print("\n[STEP 3] 트리거 생성...")
    zapi.create_triggers(hostid)
    
    print("\n" + "=" * 60)
    print("  설정 완료!")
    print("=" * 60)
    print("✅ 호스트: OpenASP-AX-Server")
    print("✅ 아이템: openasp.abend.check, openasp.abend.count")
    print("✅ 트리거: ABEND 검지 알림")
    print("\n📋 확인 방법:")
    print("1. Zabbix UI → Monitoring → Latest data")
    print("2. Zabbix UI → Monitoring → Problems")
    print("3. ABEND 테스트 후 알림 확인")
    print("\n🎯 다음 단계: ABEND 테스트 실행")

if __name__ == "__main__":
    main()