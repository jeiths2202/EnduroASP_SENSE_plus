#\!/usr/bin/env python3
"""
Zabbix ABEND Monitor - Auto-trigger CI/CD on ABEND detection
Monitors zabbix_trigger.log and executes auto-trigger-cicd.sh after 5 seconds
"""

import os
import time
import subprocess
import threading
from datetime import datetime, timedelta
import json

class ZabbixAbendMonitor:
    def __init__(self):
        self.trigger_log = "/home/aspuser/app/logs/zabbix_trigger.log"
        self.cicd_script = "/home/aspuser/app/ofasp_demo/auto-trigger-cicd.sh"
        self.state_file = "/tmp/zabbix_abend_monitor_state.json"
        self.monitoring = False
        self.last_processed_entry = None
        
    def load_state(self):
        """Load last processed entry from state file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_processed_entry = state.get('last_processed_entry')
                    print(f"[MONITOR] Loaded state - Last processed: {self.last_processed_entry}")
        except Exception as e:
            print(f"[MONITOR] Error loading state: {e}")
    
    def save_state(self, last_entry):
        """Save last processed entry to state file"""
        try:
            state = {'last_processed_entry': last_entry}
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
            print(f"[MONITOR] Saved state - Last processed: {last_entry}")
        except Exception as e:
            print(f"[MONITOR] Error saving state: {e}")
    
    def check_new_abend_triggers(self):
        """Check for new ABEND triggers in log"""
        if not os.path.exists(self.trigger_log):
            return []
        
        new_triggers = []
        try:
            with open(self.trigger_log, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or not line.startswith('['):
                    continue
                
                # Skip if already processed
                if self.last_processed_entry and line == self.last_processed_entry:
                    continue
                
                # Check if this is an ABEND trigger
                if 'ZABBIX_TRIGGER' in line and 'ABEND=CEE3204S' in line:
                    # Parse trigger details
                    trigger_info = self.parse_trigger_line(line)
                    if trigger_info:
                        new_triggers.append((line, trigger_info))
            
        except Exception as e:
            print(f"[MONITOR] Error reading trigger log: {e}")
        
        return new_triggers
    
    def parse_trigger_line(self, line):
        """Parse Zabbix trigger log line"""
        try:
            # Extract timestamp
            timestamp_str = line.split(']')[0][1:]
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Extract ABEND details
            parts = line.split()
            abend_code = None
            scenario = None
            program = None
            
            for part in parts:
                if part.startswith('ABEND='):
                    abend_code = part.split('=')[1]
                elif part.startswith('SCENARIO='):
                    scenario = part.split('=')[1]
                elif part.startswith('PROGRAM='):
                    program = part.split('=')[1]
            
            return {
                'timestamp': timestamp,
                'abend_code': abend_code,
                'scenario': scenario,
                'program': program,
                'raw_line': line
            }
            
        except Exception as e:
            print(f"[MONITOR] Error parsing trigger line: {e}")
            return None
    
    def trigger_cicd_delayed(self, trigger_info, delay_seconds=5):
        """Trigger CI/CD script after specified delay"""
        def delayed_execution():
            print(f"[MONITOR] Waiting {delay_seconds} seconds before triggering CI/CD...")
            time.sleep(delay_seconds)
            
            print(f"[MONITOR] *** EXECUTING CI/CD AUTO-FIX ***")
            print(f"[MONITOR] ABEND: {trigger_info['abend_code']}")
            print(f"[MONITOR] Scenario: {trigger_info['scenario']}")
            print(f"[MONITOR] Program: {trigger_info['program']}")
            print(f"[MONITOR] Timestamp: {trigger_info['timestamp']}")
            
            try:
                # Execute CI/CD script
                result = subprocess.run(
                    ['bash', self.cicd_script],
                    cwd=os.path.dirname(self.cicd_script),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    print(f"[MONITOR] ✅ CI/CD script executed successfully")
                    print(f"[MONITOR] Output: {result.stdout}")
                    
                    # Deploy fixed MAIN001.class
                    self.deploy_fixed_class()
                    
                else:
                    print(f"[MONITOR] ❌ CI/CD script failed")
                    print(f"[MONITOR] Error: {result.stderr}")
                
            except subprocess.TimeoutExpired:
                print(f"[MONITOR] ❌ CI/CD script timeout after 5 minutes")
            except Exception as e:
                print(f"[MONITOR] ❌ Error executing CI/CD script: {e}")
        
        # Start delayed execution in separate thread
        thread = threading.Thread(target=delayed_execution)
        thread.daemon = True
        thread.start()
        print(f"[MONITOR] CI/CD trigger scheduled in {delay_seconds} seconds...")
    
    def deploy_fixed_class(self):
        """Deploy fixed MAIN001.class from ofasp_demo to TESTLIB"""
        try:
            print(f"[MONITOR] *** DEPLOYING FIXED MAIN001.class ***")
            
            # Source and destination paths
            source_class = "/home/aspuser/app/ofasp_demo/MAIN001.class"
            dest_class = "/home/aspuser/app/volume/DISK01/TESTLIB/MAIN001.class"
            
            # Check if fixed class exists
            if os.path.exists(source_class):
                # Create backup of current ABEND version
                backup_class = f"/home/aspuser/app/volume/DISK01/TESTLIB/backups/MAIN001_abend_backup_{int(time.time())}.class"
                os.makedirs(os.path.dirname(backup_class), exist_ok=True)
                
                if os.path.exists(dest_class):
                    subprocess.run(['cp', dest_class, backup_class], check=True)
                    print(f"[MONITOR] Created backup: {backup_class}")
                
                # Copy fixed version
                subprocess.run(['cp', source_class, dest_class], check=True)
                print(f"[MONITOR] ✅ Deployed fixed MAIN001.class to TESTLIB")
                
                # Log deployment
                log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AUTO-DEPLOY: Fixed MAIN001.class deployed to TESTLIB (ABEND auto-fix completed)\n"
                with open("/home/aspuser/app/logs/devops-fix.log", "a") as f:
                    f.write(log_entry)
                
            else:
                print(f"[MONITOR] ❌ Fixed MAIN001.class not found at {source_class}")
                
        except Exception as e:
            print(f"[MONITOR] ❌ Error deploying fixed class: {e}")
    
    def start_monitoring(self):
        """Start monitoring for ABEND triggers"""
        print(f"[MONITOR] *** Starting Zabbix ABEND Monitor ***")
        print(f"[MONITOR] Watching: {self.trigger_log}")
        print(f"[MONITOR] CI/CD Script: {self.cicd_script}")
        print(f"[MONITOR] Monitoring started at {datetime.now()}")
        
        # Load previous state
        self.load_state()
        self.monitoring = True
        
        try:
            while self.monitoring:
                # Check for new ABEND triggers
                new_triggers = self.check_new_abend_triggers()
                
                for line, trigger_info in new_triggers:
                    print(f"\n[MONITOR] *** NEW ABEND DETECTED! ***")
                    print(f"[MONITOR] Raw: {line}")
                    
                    # Update last processed entry IMMEDIATELY
                    self.last_processed_entry = line
                    self.save_state(line)
                    
                    # Trigger CI/CD after 5 seconds
                    self.trigger_cicd_delayed(trigger_info, delay_seconds=5)
                    
                    # Exit after triggering to prevent duplicate processing
                    print(f"[MONITOR] CI/CD triggered. Exiting to prevent duplicate processing.")
                    self.monitoring = False
                    return
                
                # Wait before next check
                time.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n[MONITOR] Monitoring stopped by user")
        except Exception as e:
            print(f"[MONITOR] Error in monitoring loop: {e}")
        
        self.monitoring = False
        print(f"[MONITOR] Monitoring ended at {datetime.now()}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Zabbix ABEND Monitor for CI/CD Auto-trigger')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--once', action='store_true', help='Check once and exit')
    
    args = parser.parse_args()
    
    monitor = ZabbixAbendMonitor()
    
    if args.once:
        print("[MONITOR] Running single check...")
        triggers = monitor.check_new_abend_triggers()
        if triggers:
            for line, info in triggers:
                print(f"Found ABEND trigger: {info}")
                monitor.trigger_cicd_delayed(info, delay_seconds=1)  # Immediate for testing
        else:
            print("No new ABEND triggers found")
    else:
        # Start continuous monitoring
        monitor.start_monitoring()

if __name__ == '__main__':
    main()
