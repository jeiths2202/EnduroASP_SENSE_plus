#\!/usr/bin/env python3
"""
Test F9 ABEND with direct stdin input
"""

import subprocess
import os

def test_f9_direct():
    """Test F9 with direct stdin"""
    print("=== Testing F9 ABEND with Direct Input ===")
    
    # Clear ABEND log
    with open("/home/aspuser/app/logs/abend.log", "w") as f:
        f.write("")
    
    os.chdir("/home/aspuser/app/volume/DISK01/TESTLIB")
    
    try:
        print("Starting MAIN001 and sending F9...")
        
        process = subprocess.Popen(
            ["java", "-cp", ".:../../../server/java_classes", "MAIN001"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send F9 input directly
        stdout, stderr = process.communicate(input="F9\n", timeout=10)
        exit_code = process.returncode
        
        print(f"\n=== Exit Code: {exit_code} ===")
        
        if stdout:
            print("\n=== Standard Output ===")
            lines = stdout.split('\n')
            for line in lines[-20:]:  # Last 20 lines
                if line.strip():
                    print(line)
        
        if stderr:
            print("\n=== Standard Error (ABEND Messages) ===")
            lines = stderr.split('\n')
            for line in lines:
                if line.strip():
                    print(line)
        
        # Check ABEND log
        print(f"\n=== ABEND Log Check ===")
        with open("/home/aspuser/app/logs/abend.log", "r") as f:
            abend_content = f.read()
            if abend_content:
                print("ABEND logged:")
                print(abend_content)
            else:
                print("No ABEND logged")
                
        return exit_code == 204
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("Process timeout")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_f9_direct()
    print(f"\nTest Result: {'SUCCESS' if success else 'FAILED'}")
