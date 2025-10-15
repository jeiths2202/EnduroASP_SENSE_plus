#\!/usr/bin/env python3
"""
Simple test for number 9 input
"""

import subprocess
import os

def test_simple_9():
    """Simple test with direct stdin"""
    os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
    
    # Clear ABEND log
    with open("/home/aspuser/app/logs/abend.log", "w") as f:
        f.write("")
    
    print("Testing number 9 with direct stdin...")
    
    try:
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send "9" directly
        stdout, stderr = process.communicate(input="9\n", timeout=5)
        exit_code = process.returncode
        
        print(f"Exit code: {exit_code}")
        
        if stderr:
            print("STDERR output:")
            stderr_lines = stderr.split('\n')
            for line in stderr_lines[-10:]:  # Last 10 lines
                if line.strip():
                    print(f"  {line}")
        
        # Check ABEND log
        with open("/home/aspuser/app/logs/abend.log", "r") as f:
            abend_log = f.read()
            print(f"ABEND log: '{abend_log}'")
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("Timeout")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_9()
