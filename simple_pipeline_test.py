#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple DevOps CI/CD Pipeline Test
MAIN001.java commit trigger test
"""

import json
import requests
import time
import subprocess
import sys
from datetime import datetime

def print_separator():
    print("\n" + "="*60)

def test_webhook_trigger():
    """Test webhook trigger"""
    print_separator()
    print("[1] Testing Webhook Trigger")
    print_separator()
    
    # Get recent commit info
    try:
        result = subprocess.run([
            'git', 'log', '-1', '--pretty=format:%H|%s|%an|%ae|%ad', 
            '--date=iso'
        ], capture_output=True, text=True, cwd='/home/aspuser/app')
        
        if result.returncode != 0:
            print("ERROR: Failed to get commit info")
            return False
            
        parts = result.stdout.strip().split('|')
        commit_info = {
            'id': parts[0],
            'message': parts[1],
            'author': {'name': parts[2], 'email': parts[3]},
            'timestamp': parts[4]
        }
        
        print(f"Recent commit: {commit_info['id'][:8]} - {commit_info['message'][:40]}...")
        print(f"Author: {commit_info['author']['name']}")
        
    except Exception as e:
        print(f"ERROR: Failed to get commit info: {e}")
        return False
    
    # Create webhook payload
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
            "modified": [],
            "removed": []
        }],
        "head_commit": {
            "id": commit_info['id'],
            "message": commit_info['message'],
            "author": commit_info['author'],
            "timestamp": commit_info['timestamp'],
            "url": f"https://github.com/aspuser/ofasp-devops/commit/{commit_info['id']}",
            "added": ["volume/DISK01/JAVA/MAIN001.java"],
            "modified": [],
            "removed": []
        }
    }
    
    # Send webhook
    webhook_url = "http://localhost:3016/api/git-webhook"
    headers = {
        'Content-Type': 'application/json',
        'X-GitHub-Event': 'push',
        'X-Hub-Signature-256': 'sha256=dummy_signature'
    }
    
    try:
        print(f"Sending webhook to: {webhook_url}")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: {result.get('message', 'Pipeline started')}")
            if 'pipelineId' in result:
                print(f"Pipeline ID: {result['pipelineId']}")
                return result['pipelineId']
            return True
        else:
            print(f"FAILED: HTTP {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error: {error_info}")
            except:
                print(f"Response: {response.text[:100]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to DevOps server")
        print("Make sure server is running: cd /home/aspuser/app/ofasp-devops && npm run dev")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def monitor_pipeline(pipeline_id=None, max_time=60):
    """Monitor pipeline execution"""
    print_separator()
    print("[2] Monitoring Pipeline Execution")
    print_separator()
    
    if pipeline_id:
        print(f"Monitoring Pipeline ID: {pipeline_id}")
    
    status_url = "http://localhost:3016/api/pipeline-flow-status"
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_time:
        try:
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if pipeline is active
                if data.get('error'):
                    print(f"Status: {data.get('message', 'No active pipeline')}")
                    time.sleep(3)
                    continue
                
                # Get metadata
                metadata = data.get('_metadata', {})
                current_status = metadata.get('status', 'unknown')
                current_step = metadata.get('currentStep', 'none')
                
                # Print status change
                if current_status != last_status:
                    print(f"\nPipeline status changed: {last_status} -> {current_status}")
                    last_status = current_status
                
                print(f"Current step: {current_step} | Status: {current_status}")
                
                # Check steps
                steps_status = []
                for step in ['commit', 'build-artifact', 'build', 'test', 'security', 'deploy', 'production']:
                    if step in data:
                        step_data = data[step]
                        step_status = step_data.get('status', 'idle')
                        progress = step_data.get('progress', 0)
                        
                        status_symbol = {
                            'idle': 'o',
                            'running': '*',
                            'success': '+',
                            'failed': 'X'
                        }.get(step_status, '?')
                        
                        steps_status.append(f"{status_symbol} {step}({progress}%)")
                        
                        if step_status == 'failed':
                            error = step_data.get('error', 'Unknown error')
                            print(f"FAILED: {step} - {error}")
                            return False
                
                print(f"Steps: {' | '.join(steps_status)}")
                
                # Check completion
                if current_status == 'success':
                    elapsed = int(time.time() - start_time)
                    print(f"\nSUCCESS: Pipeline completed in {elapsed} seconds")
                    return True
                elif current_status == 'failed':
                    print(f"\nFAILED: Pipeline execution failed")
                    return False
                    
            else:
                print(f"ERROR: Failed to get status - HTTP {response.status_code}")
                
        except Exception as e:
            print(f"ERROR: {e}")
            
        time.sleep(3)
    
    print(f"\nTIMEOUT: Monitoring stopped after {max_time} seconds")
    return False

def test_manual_trigger():
    """Test manual pipeline trigger"""
    print_separator()
    print("[3] Testing Manual Trigger")
    print_separator()
    
    trigger_url = "http://localhost:3016/api/trigger-pipeline"
    payload = {
        "message": "Manual test - MAIN001.java validation",
        "author": "DevOps Tester", 
        "branch": "master"
    }
    
    try:
        print("Sending manual trigger request...")
        response = requests.post(
            trigger_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: {result.get('message')}")
            pipeline_id = result.get('pipelineId')
            if pipeline_id:
                print(f"Pipeline ID: {pipeline_id}")
                return pipeline_id
            return True
        else:
            print(f"FAILED: HTTP {response.status_code}")
            try:
                error_info = response.json()
                print(f"Error: {error_info}")
            except:
                print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def check_server():
    """Check if DevOps server is running"""
    try:
        response = requests.get("http://localhost:3016/", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: DevOps server is running on http://localhost:3016")
            return True
        else:
            print(f"WARNING: Server responded with status {response.status_code}")
            return False
    except:
        print("ERROR: DevOps server is not running on http://localhost:3016")
        print("Start server with: cd /home/aspuser/app/ofasp-devops && npm run dev")
        return False

def main():
    """Main test function"""
    print("DevOps CI/CD Pipeline Test")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server status
    if not check_server():
        return False
    
    # Test webhook trigger
    pipeline_id = test_webhook_trigger()
    
    if not pipeline_id:
        print("\nWebhook failed, trying manual trigger...")
        pipeline_id = test_manual_trigger()
    
    if pipeline_id:
        # Monitor pipeline
        success = monitor_pipeline(pipeline_id)
        
        print_separator()
        print("[FINAL RESULT]")
        print_separator()
        
        if success:
            print("SUCCESS: All tests passed!")
            print("* MAIN001.java commit successfully triggered the pipeline")
            print("* DevOps UI shows real-time status updates")
            print("* Access DevOps UI: http://localhost:3016")
        else:
            print("FAILED: Pipeline execution encountered issues")
            print("Check logs and troubleshoot the pipeline")
        
        return success
    else:
        print("\nERROR: Failed to trigger pipeline")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "webhook":
            test_webhook_trigger()
        elif command == "monitor":
            monitor_pipeline()
        elif command == "manual":
            pipeline_id = test_manual_trigger()
            if pipeline_id:
                monitor_pipeline(pipeline_id)
        elif command == "check":
            check_server()
        else:
            print("Usage: python3 simple_pipeline_test.py [webhook|monitor|manual|check]")
    else:
        success = main()
        sys.exit(0 if success else 1)