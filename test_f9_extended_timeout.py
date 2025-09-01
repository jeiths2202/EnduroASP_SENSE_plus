#\!/usr/bin/env python3
"""
Test F9 key with extended timeout configuration
"""

import subprocess
import os
import time
import threading

def create_input_file_delayed():
    """Create F9 input file after 3 seconds delay"""
    print("[TEST] Waiting 3 seconds before creating F9 input...")
    time.sleep(3)
    with open("/tmp/asp_input_webui.txt", "w") as f:
        f.write("F9\n")
    print("[TEST] ✅ Created F9 input file: /tmp/asp_input_webui.txt")

def test_f9_with_extended_timeout():
    """Test F9 key handling with extended timeout"""
    print("=== Testing F9 Key with Extended Timeout (864000 seconds) ===")
    print("")
    
    # Clean up previous input files
    for input_file in ["/tmp/asp_input_webui.txt", "/tmp/asp_input_terminal.txt"]:
        if os.path.exists(input_file):
            os.remove(input_file)
            print(f"[TEST] Cleaned up existing file: {input_file}")
    
    # Change to TESTLIB directory
    os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
    print(f"[TEST] Changed to directory: {os.getcwd()}")
    
    # Start thread to create input file after delay
    input_thread = threading.Thread(target=create_input_file_delayed)
    input_thread.start()
    
    print("[TEST] Starting MAIN001 with extended timeout configuration...")
    print("")
    
    # Run MAIN001 with extended timeout
    try:
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait longer for process (15 seconds should be enough)
        stdout, stderr = process.communicate(timeout=15)
        
        print("=== MAIN001 Output ===")
        print(stdout)
        
        if stderr:
            print("=== MAIN001 Errors/Debug ===")
            print(stderr)
            
    except subprocess.TimeoutExpired:
        print("\n[TEST] Process timeout after 15 seconds")
        process.kill()
        stdout, stderr = process.communicate()
        print("=== Partial Output ===")
        if stdout:
            print(stdout[-2000:])  # Last 2000 characters
        if stderr:
            print("=== Partial Errors ===")
            print(stderr[-1000:])  # Last 1000 characters
    
    except Exception as e:
        print(f"[ERROR] Exception running MAIN001: {e}")
    
    # Wait for input thread to complete
    input_thread.join()
    
    print("\n" + "="*50)
    print("CHECKING RESULTS")
    print("="*50)
    
    # Check if F9 was processed by looking at logs
    print("1. Checking Invalid Key Log:")
    invalid_log = "/home/aspuser/app/logs/invalid_key.log"
    if os.path.exists(invalid_log):
        with open(invalid_log, "r") as f:
            lines = f.readlines()
            if lines:
                print("   Latest entries:")
                for line in lines[-3:]:
                    print(f"   {line.strip()}")
                    
                # Check if new entry was added
                latest_line = lines[-1].strip()
                if "F9" in latest_line and "2025-08-25" in latest_line:
                    current_time = time.strftime("%H:%M")
                    if current_time[:4] in latest_line:  # Check if within current hour/minute
                        print("   ✅ NEW F9 INVALID KEY entry found\!")
                    else:
                        print("   ⚠️  F9 entry found but may be old")
                else:
                    print("   ❌ No recent F9 entry found")
            else:
                print("   (Invalid key log is empty)")
    else:
        print("   (No invalid key log found)")
    
    print("")
    print("2. Checking ABEND Log (should be empty):")
    abend_log = "/home/aspuser/app/logs/abend.log"
    if os.path.exists(abend_log):
        with open(abend_log, "r") as f:
            content = f.read().strip()
            if content:
                print("   ❌ UNEXPECTED ABEND found:")
                print(f"   {content}")
            else:
                print("   ✅ No ABEND - F9 correctly handled as INVALID KEY")
    else:
        print("   ✅ No ABEND log - F9 correctly handled as INVALID KEY")

if __name__ == "__main__":
    test_f9_with_extended_timeout()
