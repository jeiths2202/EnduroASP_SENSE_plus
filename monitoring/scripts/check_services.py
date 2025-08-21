#!/usr/bin/env python3
"""
OpenASP AX Service Status Monitor
Checks all OpenASP services and returns Zabbix-compatible JSON
Author: Claude Code Assistant
Created: 2025-08-21
Complies with: CODING_RULES.md (No hardcoding, <200 lines)
"""

import json
import os
import sys
import requests
import subprocess
from datetime import datetime


def load_config():
    """Load configuration from environment variables"""
    config_file = os.environ.get('MONITORING_CONFIG', 
                                '/home/aspuser/app/monitoring/config/zabbix.conf')
    
    # Default configuration
    config = {
        'ports': {
            'api_server': int(os.environ.get('OPENASP_API_SERVER_PORT', 8000)),
            'smed_viewer': int(os.environ.get('OPENASP_SMED_VIEWER_PORT', 3000)),
            'python_service': int(os.environ.get('OPENASP_PYTHON_SERVICE_PORT', 3003)),
            'refactor': int(os.environ.get('OPENASP_REFACTOR_PORT', 3005)),
            'manager': int(os.environ.get('OPENASP_MANAGER_PORT', 3007))
        },
        'timeout': int(os.environ.get('HTTP_TIMEOUT', 5)),
        'host': os.environ.get('MONITORING_HOST', 'localhost')
    }
    
    return config


def check_port_open(port, host='localhost', timeout=5):
    """Check if a port is open using netstat"""
    try:
        cmd = f"netstat -tlnp | grep :{port}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0
    except Exception:
        return False


def check_http_service(port, host='localhost', timeout=5):
    """Check HTTP service health"""
    try:
        url = f"http://{host}:{port}"
        response = requests.get(url, timeout=timeout)
        return {
            'status': 1 if response.status_code < 400 else 0,
            'response_code': response.status_code,
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            'status': 0,
            'response_code': 0,
            'response_time': timeout,
            'error': str(e)
        }


def get_process_info(port):
    """Get process information for a specific port"""
    try:
        cmd = f"netstat -tlnp | grep :{port} | awk '{{print $7}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pid_program = result.stdout.strip()
            if '/' in pid_program:
                pid, program = pid_program.split('/', 1)
                return {'pid': pid, 'program': program}
        return {'pid': 'unknown', 'program': 'unknown'}
    except Exception:
        return {'pid': 'error', 'program': 'error'}


def main():
    """Main monitoring function"""
    config = load_config()
    timestamp = datetime.now().isoformat()
    results = {
        'timestamp': timestamp,
        'services': {},
        'summary': {'total': 0, 'up': 0, 'down': 0}
    }
    
    for service_name, port in config['ports'].items():
        results['summary']['total'] += 1
        
        # Check port and HTTP status
        port_open = check_port_open(port, config['host'], config['timeout'])
        http_status = check_http_service(port, config['host'], config['timeout'])
        process_info = get_process_info(port)
        
        service_status = {
            'port': port,
            'port_open': port_open,
            'http_status': http_status['status'],
            'response_code': http_status.get('response_code', 0),
            'response_time': http_status.get('response_time', 0),
            'process': process_info,
            'overall_status': 1 if port_open and http_status['status'] else 0
        }
        
        if 'error' in http_status:
            service_status['error'] = http_status['error']
        
        results['services'][service_name] = service_status
        
        if service_status['overall_status']:
            results['summary']['up'] += 1
        else:
            results['summary']['down'] += 1
    
    # Output results
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print(json.dumps(results, indent=2))
    else:
        # Zabbix format (single value)
        print(results['summary']['up'])
    
    return 0 if results['summary']['down'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())