#!/usr/bin/env python3
"""
ABEND Detection Script for Zabbix Monitoring
Monitors ABEND occurrences in OpenASP system logs
Author: OpenASP DevOps Team
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta

class ABENDMonitor:
    def __init__(self):
        self.abend_log_file = "/home/aspuser/app/logs/abend.log"
        self.state_file = "/tmp/abend_monitor_state.json"
        self.alert_threshold = 1  # Alert on any ABEND occurrence
        
    def load_state(self):
        """Load previous monitoring state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
        
        return {
            "last_check_time": None,
            "last_abend_count": 0,
            "last_abend_timestamp": None
        }
    
    def save_state(self, state):
        """Save current monitoring state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")
    
    def parse_abend_log(self, since_time=None):
        """Parse ABEND log file and extract entries since specified time"""
        abends = []
        
        if not os.path.exists(self.abend_log_file):
            return abends
        
        try:
            with open(self.abend_log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or not line.startswith('['):
                        continue
                    
                    # Parse log entry
                    try:
                        # Extract timestamp from log format: [2025-08-22 06:30:15] ABEND ...
                        timestamp_str = line.split(']')[0][1:]
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Skip if before since_time
                        if since_time and timestamp <= since_time:
                            continue
                        
                        # Extract ABEND details
                        if 'ABEND' in line:
                            parts = line.split(' ')
                            abend_code = None
                            location = None
                            description = None
                            
                            for i, part in enumerate(parts):
                                if part == 'ABEND' and i + 1 < len(parts):
                                    abend_code = parts[i + 1]
                                elif part == 'in' and i + 1 < len(parts):
                                    location = parts[i + 1].rstrip(':')
                                elif ':' in part and i > 0:
                                    description = ' '.join(parts[i:])
                                    break
                            
                            abends.append({
                                'timestamp': timestamp,
                                'timestamp_str': timestamp_str,
                                'abend_code': abend_code,
                                'location': location,
                                'description': description,
                                'raw_line': line
                            })
                    except Exception as e:
                        print(f"Warning: Could not parse log line: {line[:100]}...")
                        continue
        
        except Exception as e:
            print(f"Error reading ABEND log file: {e}")
        
        return abends
    
    def check_abends(self, output_format='human'):
        """Check for new ABEND occurrences"""
        state = self.load_state()
        current_time = datetime.now()
        
        # Determine time window for checking
        if state['last_check_time']:
            since_time = datetime.fromisoformat(state['last_check_time'])
        else:
            # First run - check last 24 hours
            since_time = current_time - timedelta(hours=24)
        
        # Parse ABEND log for new entries
        new_abends = self.parse_abend_log(since_time)
        
        # Update state
        state['last_check_time'] = current_time.isoformat()
        if new_abends:
            state['last_abend_count'] = len(new_abends)
            state['last_abend_timestamp'] = new_abends[-1]['timestamp_str']
        
        self.save_state(state)
        
        # Generate output
        if output_format == 'json':
            result = {
                'status': 'CRITICAL' if new_abends else 'OK',
                'abend_count': len(new_abends),
                'check_timestamp': current_time.isoformat(),
                'time_window': {
                    'from': since_time.isoformat(),
                    'to': current_time.isoformat()
                },
                'abends': []
            }
            
            for abend in new_abends:
                result['abends'].append({
                    'timestamp': abend['timestamp_str'],
                    'abend_code': abend['abend_code'],
                    'location': abend['location'],
                    'description': abend['description']
                })
            
            print(json.dumps(result, indent=2))
        
        else:
            # Human readable output
            if new_abends:
                print(f"CRITICAL: {len(new_abends)} ABEND(s) detected!")
                print(f"Time window: {since_time.strftime('%Y-%m-%d %H:%M:%S')} to {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("\nABEND Details:")
                for i, abend in enumerate(new_abends, 1):
                    print(f"  {i}. {abend['timestamp_str']} - {abend['abend_code']} in {abend['location']}")
                    if abend['description']:
                        print(f"     Description: {abend['description']}")
            else:
                print("OK: No ABEND occurrences detected")
                print(f"Checked time window: {since_time.strftime('%Y-%m-%d %H:%M:%S')} to {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(new_abends)
    
    def get_abend_count(self):
        """Get ABEND count for Zabbix item (returns numeric value)"""
        try:
            abends = self.parse_abend_log()
            return len(abends)
        except Exception:
            return -1

def main():
    parser = argparse.ArgumentParser(description='ABEND Detection for OpenASP System')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--count-only', action='store_true', help='Output only ABEND count')
    parser.add_argument('--test', action='store_true', help='Test mode - create sample ABEND entry')
    
    args = parser.parse_args()
    
    monitor = ABENDMonitor()
    
    if args.test:
        # Create test ABEND entry
        test_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ABEND CEE3204S in MAIN001.test(): Test ABEND for monitoring verification (Terminal: test, Session: test_session)\n"
        os.makedirs(os.path.dirname(monitor.abend_log_file), exist_ok=True)
        with open(monitor.abend_log_file, 'a') as f:
            f.write(test_entry)
        print("Test ABEND entry created")
        return
    
    if args.count_only:
        print(monitor.get_abend_count())
    else:
        output_format = 'json' if args.json else 'human'
        abend_count = monitor.check_abends(output_format)
        
        # Exit with appropriate code for Zabbix
        if abend_count > 0:
            sys.exit(2)  # Critical
        else:
            sys.exit(0)  # OK

if __name__ == '__main__':
    main()