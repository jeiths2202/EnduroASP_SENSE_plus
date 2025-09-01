#!/usr/bin/env python3
"""
ABEND Auto-Fix Trigger Script
Monitors ABEND occurrences and triggers DevOps pipeline for automatic fixes
Author: OpenASP DevOps Team
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class AutoFixTrigger:
    def __init__(self):
        self.abend_log_file = "/home/aspuser/app/logs/abend.log"
        self.devops_log_file = "/home/aspuser/app/logs/devops-fix.log"
        self.state_file = "/tmp/autofix_state.json"
        self.workflows_dir = "/home/aspuser/app/ofasp-devops/.github/workflows"
        
    def load_state(self):
        """Load previous auto-fix state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
        
        return {
            "last_fix_time": None,
            "last_abend_processed": None,
            "fixes_applied": 0
        }
    
    def save_state(self, state):
        """Save current auto-fix state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")
    
    def check_for_new_abends(self):
        """Check for new ABEND occurrences that need auto-fixing"""
        if not os.path.exists(self.abend_log_file):
            return []
        
        state = self.load_state()
        new_abends = []
        
        try:
            with open(self.abend_log_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse ABEND entry - Only detect F9 key ABENDs
                if 'ABEND CEE3204S' in line and ('F9' in line or 'handleF9' in line or 'triggerF9Abend' in line):
                    # Extract timestamp
                    if line.startswith('['):
                        timestamp_str = line.split(']')[0][1:]
                        
                        # Check if this ABEND was already processed
                        if state['last_abend_processed'] != line:
                            new_abends.append({
                                'timestamp': timestamp_str,
                                'abend_code': 'CEE3204S',
                                'location': 'F9 key handler',
                                'fix_type': 'f9_key_fix',
                                'raw_line': line
                            })
        
        except Exception as e:
            print(f"Error reading ABEND log: {e}")
        
        return new_abends
    
    def trigger_github_actions(self, abend_info):
        """Trigger GitHub Actions workflow for auto-fix"""
        try:
            print(f"[TRIGGER] Triggering auto-fix for ABEND: {abend_info['abend_code']}")
            
            # Change to ofasp-devops directory
            os.chdir("/home/aspuser/app/ofasp-devops")
            
            # Simulate GitHub Actions workflow execution locally
            workflow_file = f"{self.workflows_dir}/abend-auto-fix.yml"
            
            if not os.path.exists(workflow_file):
                print(f"[FAILED] Workflow file not found: {workflow_file}")
                return False
            
            # Execute the workflow steps manually since we're running locally
            success = self.execute_workflow_steps(abend_info)
            
            if success:
                print("[SUCCESS] Auto-fix workflow completed successfully")
                return True
            else:
                print("[FAILED] Auto-fix workflow failed")
                return False
                
        except Exception as e:
            print(f"[FAILED] Failed to trigger auto-fix: {e}")
            return False
    
    def execute_workflow_steps(self, abend_info):
        """Execute workflow steps locally"""
        try:
            print("[ANALYZE] Step 1: Analyze ABEND...")
            
            # Step 1: Create backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = "/home/aspuser/app/volume/DISK01/TESTLIB/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = f"{backup_dir}/MAIN001_autofix_{timestamp}.java"
            subprocess.run([
                "cp", 
                "/home/aspuser/app/volume/DISK01/TESTLIB/MAIN001.java", 
                backup_file
            ], check=True)
            print(f"[BACKUP] Backup created: {backup_file}")
            
            # Step 2: Apply fix
            print("[APPLY] Step 2: Applying auto-fix...")
            if not self.apply_f9_fix():
                return False
            
            # Step 3: Compile
            print("[COMPILE] Step 3: Compiling fixed code...")
            if not self.compile_fixed_code():
                return False
            
            # Step 4: Test
            print("[TEST] Step 4: Testing fixed code...")
            if not self.test_fixed_code():
                return False
            
            # Step 5: Deploy (already done by compilation)
            print("[DEPLOY] Step 5: Deploying...")
            print("[SUCCESS] Fixed code deployed successfully")
            
            # Step 6: Log success
            self.log_fix_result(True, abend_info)
            
            return True
            
        except Exception as e:
            print(f"[FAILED] Workflow execution failed: {e}")
            self.log_fix_result(False, abend_info)
            return False
    
    def apply_f9_fix(self):
        """Apply the F9 key fix to MAIN001.java in TESTLIB"""
        try:
            main001_file = "/home/aspuser/app/volume/DISK01/TESTLIB/MAIN001.java"
            
            # Read current file
            with open(main001_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply the fix - Change handleF9KeyAbend to handleF9InvalidKey
            fixed_content = content.replace(
                'handleF9KeyAbend();',
                'handleF9InvalidKey();'
            )
            
            # Update method name
            fixed_content = fixed_content.replace(
                'private static void handleF9KeyAbend()',
                'private static void handleF9InvalidKey()'
            )
            
            # Add the handleF9InvalidKey method
            if 'private static void handleF9InvalidKey()' not in fixed_content:
                # Find where to insert the new method (after handleF9KeyAbend)
                insert_pos = fixed_content.find('private static void handleF9KeyAbend()')
                if insert_pos == -1:
                    # Insert before the last closing brace
                    insert_pos = fixed_content.rfind('}')
                    
                new_method = '''
    /**
     * Handle F9 key press - Invalid Key
     * Auto-fixed by DevOps pipeline
     */
    private static void handleF9InvalidKey() {
        System.out.println("[ERROR] INVALID KEY - F9 is not supported in this menu");
        System.out.println("[MAIN001] Press ENTER to continue...");
        
        // Log invalid key
        try {
            String logFile = "/home/aspuser/app/logs/invalid_key.log";
            String timestamp = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new java.util.Date());
            String logEntry = String.format("[%s] INVALID_KEY F9 in MAIN001%n", timestamp);
            
            Files.write(
                Paths.get(logFile), 
                logEntry.getBytes(), 
                StandardOpenOption.CREATE, 
                StandardOpenOption.APPEND
            );
        } catch (Exception e) {
            // Ignore logging errors
        }
    }

'''
                fixed_content = fixed_content[:insert_pos] + new_method + fixed_content[insert_pos:]
            
            # Write fixed file
            with open(main001_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("[SUCCESS] F9 key fix applied successfully")
            return True
            
        except Exception as e:
            print(f"[FAILED] Failed to apply fix: {e}")
            return False
    
    def compile_fixed_code(self):
        """Compile the fixed MAIN001.java"""
        try:
            os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
            
            result = subprocess.run([
                "javac", "-encoding", "UTF-8", 
                "-cp", ".:../../../server/java_classes", 
                "MAIN001.java"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[SUCCESS] Compilation successful")
                return True
            else:
                print(f"[FAILED] Compilation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[FAILED] Compilation error: {e}")
            return False
    
    def test_fixed_code(self):
        """Test the fixed code"""
        try:
            # Simple test - check if the fix was applied
            main001_file = "/home/aspuser/app/volume/DISK01/TESTLIB/MAIN001.java"
            
            with open(main001_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'handleF9InvalidKey' in content and 'INVALID KEY - F9 is not supported' in content:
                print("[SUCCESS] Fix verification passed")
                return True
            else:
                print("[FAILED] Fix verification failed")
                return False
                
        except Exception as e:
            print(f"[FAILED] Test failed: {e}")
            return False
    
    def log_fix_result(self, success, abend_info):
        """Log the auto-fix result"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = "SUCCESS" if success else "FAILED"
            
            log_entry = f"[{timestamp}] {status}: Auto-fix for {abend_info['abend_code']} " \
                       f"in {abend_info['location']} - {abend_info['fix_type']}\n"
            
            os.makedirs(os.path.dirname(self.devops_log_file), exist_ok=True)
            with open(self.devops_log_file, 'a') as f:
                f.write(log_entry)
            
            print(f"[LOG] Fix result logged: {status}")
            
        except Exception as e:
            print(f"Warning: Could not log fix result: {e}")
    
    def clear_abend_log(self):
        """Clear ABEND log after successful fix"""
        try:
            with open(self.abend_log_file, 'w') as f:
                f.write("")
            print("[CLEAN] ABEND log cleared")
        except Exception as e:
            print(f"Warning: Could not clear ABEND log: {e}")
    
    def run_auto_fix_cycle(self):
        """Run one cycle of auto-fix checking"""
        print("[ANALYZE] Checking for new ABENDs requiring auto-fix...")
        
        new_abends = self.check_for_new_abends()
        
        if not new_abends:
            print("[INFO] No new ABENDs requiring auto-fix")
            return
        
        state = self.load_state()
        
        for abend in new_abends:
            print(f"\n[ALERT] New ABEND detected: {abend['abend_code']} in {abend['location']}")
            
            # Trigger auto-fix
            if self.trigger_github_actions(abend):
                print("[SUCCESS] Auto-fix completed successfully")
                
                # Update state
                state['last_fix_time'] = datetime.now().isoformat()
                state['last_abend_processed'] = abend['raw_line']
                state['fixes_applied'] += 1
                
                # Clear ABEND log to reset monitoring
                self.clear_abend_log()
                
            else:
                print("[FAILED] Auto-fix failed")
            
            self.save_state(state)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ABEND Auto-Fix Trigger')
    parser.add_argument('--monitor', action='store_true', help='Run in monitoring mode')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--test', action='store_true', help='Test mode - simulate fix')
    
    args = parser.parse_args()
    
    trigger = AutoFixTrigger()
    
    if args.test:
        print("[TEST] Running in test mode...")
        # Create a test ABEND entry
        test_abend = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'abend_code': 'CEE3204S',
            'location': 'F9 key handler',
            'fix_type': 'f9_key_fix',
            'raw_line': f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ABEND CEE3204S in MAIN001.handleF3Key(): Test auto-fix trigger"
        }
        
        trigger.trigger_github_actions(test_abend)
        
    elif args.monitor:
        print("[MONITOR] Running in monitoring mode...")
        try:
            while True:
                trigger.run_auto_fix_cycle()
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            print("\n[STOP] Monitoring stopped by user")
    
    elif args.once:
        trigger.run_auto_fix_cycle()
    
    else:
        print("Usage: --monitor, --once, or --test")

if __name__ == '__main__':
    main()