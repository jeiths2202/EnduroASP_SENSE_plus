#!/bin/bash

# ABEND Test Script for OpenASP System
# This script simulates F3 key press to trigger ABEND in MAIN001

echo "=== OpenASP ABEND Test Script ==="
echo "Testing F3 key ABEND scenario in MAIN001"
echo "Current time: $(date)"
echo ""

# Navigate to Java directory
cd /home/aspuser/app/volume/DISK01/JAVA

echo "Starting MAIN001 program with F3 key simulation..."
echo "Expected: ABEND CEE3204S should be triggered"
echo ""

# Run MAIN001 with F3 input
echo "F3" | java -cp ".:../../../server/java_classes" MAIN001

echo ""
echo "=== ABEND Test Results ==="
echo "Exit code: $?"

# Check if ABEND log was created
if [ -f "/home/aspuser/app/logs/abend.log" ]; then
    echo "✓ ABEND log file created successfully"
    echo "=== Latest ABEND Log Entry ==="
    tail -5 /home/aspuser/app/logs/abend.log
else
    echo "✗ ABEND log file not found"
fi

echo ""
echo "=== Test completed at $(date) ==="