#\!/usr/bin/env python3
"""
Simulate ASP System Command Terminal execution
Testing F9 key handling in MAIN001 through CL001
"""

import subprocess
import os
import time
import sys

def simulate_cl001_execution():
    """Simulate CL001 execution with F9 input"""
    print("=== Simulating ASP System Command Terminal ===")
    print("Command: CALL PGM-CL001.TESTLIB,VOL-DISK01")
    print("")
    
    # Change to TESTLIB directory
    os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
    
    # Create F9 input file
    with open("/tmp/asp_input_webui.txt", "w") as f:
        f.write("F9\n")
    
    print("1. Executing MAIN001 with F9 input...")
    print("")
    
    # Run MAIN001 with F9 input
    try:
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send F9 input
        stdout, stderr = process.communicate(input="F9\n", timeout=5)
        
        print("=== MAIN001 Output ===")
        print(stdout)
        
        if stderr:
            print("=== MAIN001 Errors ===")
            print(stderr)
            
    except subprocess.TimeoutExpired:
        print("Process timed out after 5 seconds")
        process.kill()
        stdout, stderr = process.communicate()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
    
    except Exception as e:
        print(f"Error running MAIN001: {e}")
    
    print("")
    print("2. Checking log files...")
    print("")
    
    # Check ABEND log
    abend_log = "/home/aspuser/app/logs/abend.log"
    if os.path.exists(abend_log):
        print("=== ABEND Log ===")
        with open(abend_log, "r") as f:
            lines = f.readlines()
            if lines:
                print("".join(lines[-5:]))
            else:
                print("(ABEND log is empty)")
    else:
        print("(No ABEND log found)")
    
    print("")
    
    # Check Invalid Key log
    invalid_log = "/home/aspuser/app/logs/invalid_key.log"
    if os.path.exists(invalid_log):
        print("=== Invalid Key Log ===")
        with open(invalid_log, "r") as f:
            lines = f.readlines()
            if lines:
                print("".join(lines[-5:]))
            else:
                print("(Invalid key log is empty)")
    else:
        print("(No invalid key log found)")

if __name__ == "__main__":
    simulate_cl001_execution()
