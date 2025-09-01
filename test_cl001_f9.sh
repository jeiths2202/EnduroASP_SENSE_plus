#\!/bin/bash

echo "=== Testing F9 key in MAIN001 through CL001 ==="
echo ""

# Create test input file for F9
echo "F9" > /tmp/test_f9_input.txt

echo "1. Running CL001 with F9 input..."
cd /home/aspuser/app
echo "F9" | timeout 5 /home/aspuser/app/asp_runtime/asp_runtime.sh CALL PGM-CL001.TESTLIB,VOL-DISK01

echo ""
echo "2. Checking for ABEND or INVALID KEY logs..."
echo ""

echo "=== ABEND log ===" 
if [ -f /home/aspuser/app/logs/abend.log ]; then
    tail -5 /home/aspuser/app/logs/abend.log
else
    echo "(No ABEND log found)"
fi

echo ""
echo "=== Invalid key log ==="
if [ -f /home/aspuser/app/logs/invalid_key.log ]; then
    tail -5 /home/aspuser/app/logs/invalid_key.log
else
    echo "(No invalid key log found)"
fi

echo ""
echo "=== Testing direct MAIN001 execution with F9 ==="
cd /home/aspuser/app/volume/DISK01/TESTLIB
echo "F9" | timeout 5 java -cp .:../../../server/java_classes MAIN001

echo ""
echo "Test completed."
