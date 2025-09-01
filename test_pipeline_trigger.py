#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevOps CI/CD Pipeline Webhook 테스트 스크립트
MAIN001.java 커밋 후 Pipeline 트리거 테스트
"""

import json
import requests
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class PipelineTestor:
    def __init__(self):
        self.base_url = "http://localhost:3016"
        self.webhook_url = f"{self.base_url}/api/git-webhook"
        self.pipeline_status_url = f"{self.base_url}/api/pipeline-flow-status"
        self.trigger_url = f"{self.base_url}/api/trigger-pipeline"
        
    def print_banner(self, title):
        """출력 배너"""
        print(f"\n{'='*60}")
        print(f"* {title}")
        print(f"{'='*60}")
        
    def get_recent_commit(self):
        """최근 커밋 정보 조회"""
        try:
            # Git log로 최근 커밋 정보 조회
            result = subprocess.run([
                'git', 'log', '-1', '--pretty=format:%H|%s|%an|%ae|%ad', 
                '--date=iso'
            ], capture_output=True, text=True, cwd='/home/aspuser/app')
            
            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                return {
                    'id': parts[0],
                    'message': parts[1],
                    'author': {'name': parts[2], 'email': parts[3]},
                    'timestamp': parts[4]
                }
            else:
                print(f"❌ Git log 실패: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ 커밋 정보 조회 실패: {e}")
            return None
    
    def create_mock_webhook_payload(self, commit_info):
        """GitHub webhook payload 모의 생성"""
        if not commit_info:
            return None
            
        payload = {
            "ref": "refs/heads/master",
            "before": "0000000000000000000000000000000000000000",
            "after": commit_info['id'],
            "pusher": {
                "name": commit_info['author']['name'],
                "email": commit_info['author']['email']
            },
            "repository": {
                "name": "ofasp-devops",
                "full_name": "aspuser/ofasp-devops",
                "html_url": "https://github.com/aspuser/ofasp-devops"
            },
            "commits": [{
                "id": commit_info['id'],
                "message": commit_info['message'],
                "author": commit_info['author'],
                "timestamp": commit_info['timestamp'],
                "url": f"https://github.com/aspuser/ofasp-devops/commit/{commit_info['id']}",
                "added": ["volume/DISK01/JAVA/MAIN001.java"],
                "modified": ["ofasp-devops/src/pages/api/git-webhook.ts"],
                "removed": []
            }],
            "head_commit": {
                "id": commit_info['id'],
                "message": commit_info['message'],
                "author": commit_info['author'],
                "timestamp": commit_info['timestamp'],
                "url": f"https://github.com/aspuser/ofasp-devops/commit/{commit_info['id']}",
                "added": ["volume/DISK01/JAVA/MAIN001.java"],
                "modified": ["ofasp-devops/src/pages/api/git-webhook.ts"],
                "removed": []
            }
        }
        
        return payload
    
    def test_webhook_endpoint(self):
        """Webhook 엔드포인트 테스트"""
        self.print_banner("1. Webhook 엔드포인트 테스트")
        
        # 최근 커밋 정보 조회
        commit_info = self.get_recent_commit()
        if not commit_info:
            print("❌ 커밋 정보를 가져올 수 없습니다")
            return False
            
        print(f"📝 최근 커밋: {commit_info['id'][:8]} - {commit_info['message'][:50]}...")
        print(f"👤 작성자: {commit_info['author']['name']} <{commit_info['author']['email']}>")
        
        # Mock webhook payload 생성
        payload = self.create_mock_webhook_payload(commit_info)
        if not payload:
            print("❌ Webhook payload 생성 실패")
            return False
            
        # Webhook 전송
        headers = {
            'Content-Type': 'application/json',
            'X-GitHub-Event': 'push',
            'X-Hub-Signature-256': 'sha256=dummy_signature'
        }
        
        try:
            print(f"🔗 Webhook URL: {self.webhook_url}")
            print("📤 Webhook payload 전송 중...")
            
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            print(f"📨 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook 성공: {result.get('message', 'Success')}")
                if 'pipelineId' in result:
                    print(f"🚀 Pipeline ID: {result['pipelineId']}")
                    print(f"📊 커밋: {result['commit']['id'][:8]} - {result['commit']['message'][:30]}...")
                    return result['pipelineId']
                return True
            else:
                print(f"❌ Webhook 실패: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"❌ 오류 내용: {error_info}")
                except:
                    print(f"❌ 응답 내용: {response.text[:200]}...")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 연결 실패: DevOps 서버가 실행 중인지 확인하세요 (http://localhost:3016)")
            return False
        except Exception as e:
            print(f"❌ Webhook 요청 실패: {e}")
            return False
    
    def monitor_pipeline_status(self, pipeline_id=None, max_duration=120):
        """파이프라인 상태 모니터링"""
        self.print_banner("2. 파이프라인 실행 상태 모니터링")
        
        print(f"⏱️  모니터링 시간: 최대 {max_duration}초")
        if pipeline_id:
            print(f"🆔 Pipeline ID: {pipeline_id}")
        
        start_time = time.time()
        last_status = None
        completed_steps = set()
        
        while time.time() - start_time < max_duration:
            try:
                response = requests.get(self.pipeline_status_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 파이프라인이 실행 중인지 확인
                    if data.get('error'):
                        print(f"ℹ️  상태: {data.get('message', 'No active pipeline')}")
                        time.sleep(5)
                        continue
                    
                    # 메타데이터 확인
                    metadata = data.get('_metadata', {})
                    current_status = metadata.get('status', 'unknown')
                    current_step = metadata.get('currentStep', 'none')
                    
                    # 상태 변경 감지
                    if current_status != last_status:
                        print(f"\n🔄 파이프라인 상태 변경: {last_status} → {current_status}")
                        last_status = current_status
                    
                    # 현재 실행 중인 단계 표시
                    print(f"📍 현재 단계: {current_step} | 상태: {current_status}")
                    
                    # 각 단계별 상태 확인
                    steps_info = []
                    for step_id in ['commit', 'build-artifact', 'build', 'test', 'security', 'deploy', 'production']:
                        if step_id in data:
                            step_data = data[step_id]
                            step_status = step_data.get('status', 'idle')
                            step_progress = step_data.get('progress', 0)
                            
                            status_emoji = {
                                'idle': '⚪',
                                'running': '🟡',
                                'success': '✅',
                                'failed': '❌'
                            }.get(step_status, '❔')
                            
                            steps_info.append(f"{status_emoji} {step_id}: {step_status} ({step_progress}%)")
                            
                            # 완료된 단계 추적
                            if step_status == 'success' and step_id not in completed_steps:
                                completed_steps.add(step_id)
                                details = step_data.get('details', '')
                                print(f"  ✅ {step_id} 완료: {details}")
                            elif step_status == 'failed':
                                error = step_data.get('error', 'Unknown error')
                                print(f"  ❌ {step_id} 실패: {error}")
                                return False
                    
                    # 단계별 상태 요약 출력
                    print(f"📊 단계 현황: {' | '.join(steps_info[:3])}")
                    if len(steps_info) > 3:
                        print(f"              {' | '.join(steps_info[3:])}")
                    
                    # 파이프라인 완료 확인
                    if current_status == 'success':
                        print(f"\n🎉 파이프라인 성공적으로 완료!")
                        print(f"⏱️  총 실행 시간: {int(time.time() - start_time)}초")
                        return True
                    elif current_status == 'failed':
                        print(f"\n💥 파이프라인 실행 실패!")
                        return False
                    
                else:
                    print(f"❌ 상태 조회 실패: {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                print("❌ DevOps 서버 연결 실패")
                return False
            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
            
            time.sleep(3)  # 3초마다 상태 확인
        
        print(f"\n⏰ 모니터링 시간 초과 ({max_duration}초)")
        return False
    
    def test_manual_trigger(self):
        """수동 파이프라인 트리거 테스트"""
        self.print_banner("3. 수동 파이프라인 트리거 테스트")
        
        payload = {
            "message": "Manual pipeline test - MAIN001.java validation",
            "author": "DevOps Tester",
            "branch": "master"
        }
        
        try:
            print("🔧 수동 트리거 요청 전송 중...")
            response = requests.post(
                self.trigger_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"📨 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 수동 트리거 성공: {result.get('message')}")
                print(f"🚀 Pipeline ID: {result.get('pipelineId')}")
                return result.get('pipelineId')
            else:
                print(f"❌ 수동 트리거 실패: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"❌ 오류 내용: {error_info}")
                except:
                    print(f"❌ 응답 내용: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 수동 트리거 요청 실패: {e}")
            return None
    
    def check_devops_server(self):
        """DevOps 서버 상태 확인"""
        self.print_banner("DevOps 서버 상태 확인")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print(f"✅ DevOps 서버 실행 중: {self.base_url}")
                return True
            else:
                print(f"❌ DevOps 서버 응답 이상: {response.status_code}")
                return False
        except:
            print(f"❌ DevOps 서버에 연결할 수 없습니다: {self.base_url}")
            print("💡 다음 명령으로 서버를 시작하세요:")
            print("   cd /home/aspuser/app/ofasp-devops && npm run dev")
            return False
    
    def run_full_test(self):
        """전체 테스트 실행"""
        print("🚀 DevOps CI/CD Pipeline Workflow 테스트 시작")
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 서버 상태 확인
        if not self.check_devops_server():
            return False
        
        # 1단계: Webhook 트리거 테스트
        pipeline_id = self.test_webhook_endpoint()
        if not pipeline_id:
            print("\n🔧 Webhook 실패, 수동 트리거로 대체 시도...")
            pipeline_id = self.test_manual_trigger()
        
        if pipeline_id:
            # 2단계: 파이프라인 모니터링
            success = self.monitor_pipeline_status(pipeline_id)
            
            self.print_banner("테스트 결과 요약")
            if success:
                print("🎉 모든 테스트 성공!")
                print("✅ MAIN001.java 커밋이 성공적으로 파이프라인을 트리거했습니다")
                print("✅ DevOps UI에서 실시간으로 상태를 확인할 수 있습니다")
                print(f"🌐 DevOps UI: {self.base_url}")
            else:
                print("❌ 파이프라인 실행 중 문제가 발생했습니다")
                print("🔍 로그를 확인하고 문제를 해결하세요")
            
            return success
        else:
            print("\n❌ 파이프라인 트리거 실패")
            return False

def main():
    """메인 함수"""
    tester = PipelineTestor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "webhook":
            tester.test_webhook_endpoint()
        elif command == "monitor":
            tester.monitor_pipeline_status()
        elif command == "manual":
            pipeline_id = tester.test_manual_trigger()
            if pipeline_id:
                tester.monitor_pipeline_status(pipeline_id)
        elif command == "check":
            tester.check_devops_server()
        else:
            print("사용법: python3 test_pipeline_trigger.py [webhook|monitor|manual|check]")
    else:
        # 전체 테스트 실행
        success = tester.run_full_test()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()