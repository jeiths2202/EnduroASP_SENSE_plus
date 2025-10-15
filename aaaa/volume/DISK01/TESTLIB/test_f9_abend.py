#\!/usr/bin/env python3
"""
Test F9 ABEND scenario with the restored ABEND version
"""

import subprocess
import os
import time
import threading

def create_f9_input():
    """Create F9 input file after 3 seconds"""
    time.sleep(3)
    with open("/tmp/asp_input_webui.txt", "w") as f:
        f.write("F9\n")
    print("[TEST] F9 input file created")

def test_f9_abend():
    """Test F9 ABEND scenario"""
    print("=== Testing F9 ABEND Scenario (CEE3204S) ===")
    print("")
    
    # Clear logs first
    for log_file in ["/home/aspuser/app/logs/abend.log", "/tmp/asp_input_webui.txt"]:
        if os.path.exists(log_file):
            if "abend.log" in log_file:
                with open(log_file, "w") as f:
                    f.write("")  # Clear ABEND log
            else:
                os.remove(log_file)
    
    # Start input thread
    input_thread = threading.Thread(target=create_f9_input)
    input_thread.start()
    
    print("Starting MAIN001 with ABEND version...")
    print("Expecting CEE3204S ABEND when F9 is pressed...")
    print("")
    
    try:
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for process (should exit with code 204)
        stdout, stderr = process.communicate(timeout=15)
        exit_code = process.returncode
        
        print(f"=== Process Exit Code: {exit_code} ===")
        if exit_code == 204:
            print("SUCCESS: Process exited with CEE3204S code (204)")
        else:
            print(f"UNEXPECTED: Process exited with code {exit_code}")
        
        print("\n=== MAIN001 Output ===")
        print(stdout[-1500:])  # Last 1500 characters
        
        if stderr:
            print("\n=== MAIN001 ABEND Messages ===")
            print(stderr[-1000:])  # Last 1000 characters
            
    except subprocess.TimeoutExpired:
        print("Process timeout - killing...")
        process.kill()
        stdout, stderr = process.communicate()
        print("=== Timeout Output ===")
        if stdout:
            print(stdout[-1000:])
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Wait for thread
    input_thread.join()
    
    print("\n" + "="*60)
    print("CHECKING ABEND LOGS")
    print("="*60)
    
    # Check ABEND log
    abend_log = "/home/aspuser/app/logs/abend.log"
    if os.path.exists(abend_log):
        with open(abend_log, "r") as f:
            content = f.read().strip()
            if content:
                print("ABEND LOG FOUND:")
                print(content)
                if "CEE3204S" in content and "F9" in content:
                    print("\nSUCCESS: F9 ABEND correctly logged for Zabbix monitoring\!")
                else:
                    print("\nWARNING: ABEND log exists but may not be F9-related")
            else:
                print("ABEND log exists but is empty")
    else:
        print("No ABEND log found")
    
    # Check Zabbix trigger log
    zabbix_log = "/home/aspuser/app/logs/zabbix_trigger.log"
    if os.path.exists(zabbix_log):
        print(f"\nZABBIX TRIGGER LOG:")
        with open(zabbix_log, "r") as f:
            lines = f.readlines()
            if lines:
                for line in lines[-3:]:
                    print(f"  {line.strip()}")
            else:
                print("  (empty)")

if __name__ == "__main__":
    test_f9_abend()
