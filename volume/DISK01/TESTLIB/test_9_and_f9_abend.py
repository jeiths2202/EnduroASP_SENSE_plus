#\!/usr/bin/env python3
"""
Test both number 9 and F9 key ABEND scenarios
"""

import subprocess
import os
import time
import threading

def test_key_abend(key_input, test_name):
    """Test ABEND scenario for specific key input"""
    print(f"=== Testing {test_name} ABEND Scenario ===")
    print(f"Input: {key_input}")
    print("")
    
    # Clear ABEND log
    with open("/home/aspuser/app/logs/abend.log", "w") as f:
        f.write("")
    
    # Clean input file
    input_file = "/tmp/asp_input_webui.txt"
    if os.path.exists(input_file):
        os.remove(input_file)
    
    def create_input():
        time.sleep(2)
        with open(input_file, "w") as f:
            f.write(f"{key_input}\n")
        print(f"[TEST] Created input file with: {key_input}")
    
    # Start input thread
    input_thread = threading.Thread(target=create_input)
    input_thread.start()
    
    try:
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=8)
        exit_code = process.returncode
        
        print(f"Exit Code: {exit_code}")
        
        # Check for ABEND output in stderr
        if stderr and "ABEND" in stderr:
            print("ABEND Messages Found:")
            abend_lines = [line for line in stderr.split('\n') if 'ABEND' in line or 'CEE3204S' in line]
            for line in abend_lines[:5]:  # First 5 ABEND lines
                print(f"  {line}")
        
        # Check ABEND log
        with open("/home/aspuser/app/logs/abend.log", "r") as f:
            abend_content = f.read().strip()
            if abend_content:
                print(f"ABEND Logged: {abend_content}")
                success = "CEE3204S" in abend_content and key_input in abend_content
            else:
                print("No ABEND logged")
                success = False
        
        input_thread.join()
        
        result = "SUCCESS" if (exit_code == 204 and success) else "FAILED"
        print(f"Result: {result}")
        print("")
        
        return result == "SUCCESS"
        
    except subprocess.TimeoutExpired:
        process.kill()
        input_thread.join()
        print("Process timeout")
        return False
    except Exception as e:
        input_thread.join()
        print(f"Error: {e}")
        return False

def main():
    """Test both 9 and F9 key ABEND scenarios"""
    os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
    
    print("Testing ABEND scenarios for number 9 and F9 keys")
    print("=" * 60)
    print("")
    
    # Test number 9
    success_9 = test_key_abend("9", "Number 9 Key")
    time.sleep(1)
    
    # Test F9
    success_f9 = test_key_abend("F9", "F9 Key")
    
    print("=" * 60)
    print("FINAL RESULTS:")
    print(f"Number 9 Key ABEND: {'SUCCESS' if success_9 else 'FAILED'}")
    print(f"F9 Key ABEND: {'SUCCESS' if success_f9 else 'FAILED'}")
    
    if success_9 and success_f9:
        print("Overall Result: SUCCESS - Both keys trigger ABEND")
    else:
        print("Overall Result: FAILED - One or both keys did not trigger ABEND")

if __name__ == "__main__":
    main()
