#\!/usr/bin/env python3
"""
Test F9 key directly in MAIN001
"""

import subprocess
import os
import time
import threading

def create_input_file():
    """Create F9 input file after 2 seconds"""
    time.sleep(2)
    with open("/tmp/asp_input_webui.txt", "w") as f:
        f.write("F9\n")
    print("\n[TEST] Created F9 input file")

def test_f9_key():
    """Test F9 key handling in MAIN001"""
    print("=== Testing F9 Key Handling in MAIN001 ===")
    print("")
    
    # Clean up previous input file
    if os.path.exists("/tmp/asp_input_webui.txt"):
        os.remove("/tmp/asp_input_webui.txt")
    
    # Change to TESTLIB directory
    os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
    
    # Start thread to create input file
    input_thread = threading.Thread(target=create_input_file)
    input_thread.start()
    
    print("1. Starting MAIN001...")
    print("")
    
    # Run MAIN001
    try:
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for process
        stdout, stderr = process.communicate(timeout=10)
        
        print("=== MAIN001 Output ===")
        print(stdout)
        
        if stderr:
            print("=== MAIN001 Errors ===")
            print(stderr)
            
    except subprocess.TimeoutExpired:
        print("\n[TEST] Process timeout - checking if F9 was processed...")
        process.kill()
        stdout, stderr = process.communicate()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
    
    except Exception as e:
        print(f"Error running MAIN001: {e}")
    
    # Wait for thread
    input_thread.join()
    
    print("\n2. Checking log files...")
    print("")
    
    # Check Invalid Key log
    invalid_log = "/home/aspuser/app/logs/invalid_key.log"
    if os.path.exists(invalid_log):
        print("=== Invalid Key Log (last 5 lines) ===")
        with open(invalid_log, "r") as f:
            lines = f.readlines()
            if lines:
                for line in lines[-5:]:
                    print(line.strip())
            else:
                print("(Invalid key log is empty)")
    else:
        print("(No invalid key log found)")
    
    print("")
    
    # Check ABEND log
    abend_log = "/home/aspuser/app/logs/abend.log"
    if os.path.exists(abend_log):
        print("=== ABEND Log ===")
        with open(abend_log, "r") as f:
            content = f.read()
            if content:
                print("ABEND detected\!")
                print(content)
            else:
                print("(No ABEND - Good, F9 handled as INVALID KEY)")
    else:
        print("(No ABEND log - Good, F9 handled as INVALID KEY)")

if __name__ == "__main__":
    test_f9_key()
