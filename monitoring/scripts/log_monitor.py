#!/usr/bin/env python3
"""
OpenASP AX Log Monitor
Monitors log files in both /home/aspuser/app/logs and /home/aspuser/app/ofasp-refactor/logs
Author: Claude Code Assistant
Created: 2025-08-21
Complies with: CODING_RULES.md (No hardcoding, <200 lines)
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path


def load_config():
    """Load log monitoring configuration from environment variables"""
    return {
        'log_dirs': [
            os.environ.get('OPENASP_LOG_DIR', '/home/aspuser/app/logs'),
            os.environ.get('OPENASP_REFACTOR_LOG_DIR', '/home/aspuser/app/ofasp-refactor/logs')
        ],
        'error_patterns': [
            r'ERROR',
            r'CRITICAL',
            r'FATAL',
            r'Exception',
            r'Traceback',
            r'Failed',
            r'Connection refused',
            r'Timeout'
        ],
        'warning_patterns': [
            r'WARNING',
            r'WARN',
            r'deprecated',
            r'retry',
            r'fallback'
        ],
        'time_window': int(os.environ.get('LOG_MONITOR_WINDOW_MINUTES', 10)),
        'max_file_size': int(os.environ.get('MAX_LOG_FILE_SIZE_MB', 100)) * 1024 * 1024
    }


def parse_log_timestamp(line):
    """Extract timestamp from log line (various formats)"""
    timestamp_patterns = [
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'
    ]
    
    for pattern in timestamp_patterns:
        match = re.search(pattern, line)
        if match:
            try:
                ts_str = match.group(1)
                if 'T' in ts_str:
                    return datetime.fromisoformat(ts_str.replace('T', ' '))
                elif '/' in ts_str:
                    return datetime.strptime(ts_str, '%d/%m/%Y %H:%M:%S')
                else:
                    return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
    return None


def analyze_log_file(log_path, config):
    """Analyze a single log file for errors and warnings"""
    try:
        if not log_path.exists():
            return None
        
        stat_info = log_path.stat()
        if stat_info.st_size > config['max_file_size']:
            return {
                'file': str(log_path),
                'error': f'File too large ({stat_info.st_size} bytes)',
                'size': stat_info.st_size
            }
        
        cutoff_time = datetime.now() - timedelta(minutes=config['time_window'])
        errors = 0
        warnings = 0
        recent_errors = []
        recent_warnings = []
        
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                timestamp = parse_log_timestamp(line)
                if timestamp and timestamp < cutoff_time:
                    continue
                
                # Check for error patterns
                for pattern in config['error_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        errors += 1
                        if len(recent_errors) < 5:
                            recent_errors.append({
                                'line': line_num,
                                'message': line[:200],
                                'timestamp': timestamp.isoformat() if timestamp else None
                            })
                        break
                
                # Check for warning patterns
                for pattern in config['warning_patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        warnings += 1
                        if len(recent_warnings) < 3:
                            recent_warnings.append({
                                'line': line_num,
                                'message': line[:200],
                                'timestamp': timestamp.isoformat() if timestamp else None
                            })
                        break
        
        return {
            'file': str(log_path),
            'size': stat_info.st_size,
            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'errors': errors,
            'warnings': warnings,
            'recent_errors': recent_errors,
            'recent_warnings': recent_warnings,
            'status': 'critical' if errors > 10 else 'warning' if errors > 0 or warnings > 5 else 'ok'
        }
        
    except Exception as e:
        return {
            'file': str(log_path),
            'error': str(e),
            'status': 'error'
        }


def main():
    """Main log monitoring function"""
    config = load_config()
    timestamp = datetime.now().isoformat()
    
    results = {
        'timestamp': timestamp,
        'time_window_minutes': config['time_window'],
        'log_files': {},
        'summary': {
            'total_files': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'critical_files': 0,
            'warning_files': 0
        }
    }
    
    # Scan all log directories
    for log_dir in config['log_dirs']:
        log_path = Path(log_dir)
        if not log_path.exists():
            continue
        
        for log_file in log_path.glob('*.log'):
            results['summary']['total_files'] += 1
            analysis = analyze_log_file(log_file, config)
            
            if analysis:
                results['log_files'][log_file.name] = analysis
                
                if 'errors' in analysis:
                    results['summary']['total_errors'] += analysis['errors']
                if 'warnings' in analysis:
                    results['summary']['total_warnings'] += analysis['warnings']
                
                if analysis.get('status') == 'critical':
                    results['summary']['critical_files'] += 1
                elif analysis.get('status') == 'warning':
                    results['summary']['warning_files'] += 1
    
    # Output format based on arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print(json.dumps(results, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == '--errors':
        print(results['summary']['total_errors'])
    elif len(sys.argv) > 1 and sys.argv[1] == '--warnings':
        print(results['summary']['total_warnings'])
    else:
        # Default: critical files count for Zabbix
        print(results['summary']['critical_files'])
    
    return 0 if results['summary']['critical_files'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())