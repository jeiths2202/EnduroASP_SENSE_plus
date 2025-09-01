#\!/bin/bash

echo "=== Starting Zabbix ABEND Monitor ==="
echo "Monitor will:"
echo "1. Watch /home/aspuser/app/logs/zabbix_trigger.log for ABEND triggers"
echo "2. Wait 5 seconds after ABEND detection"
echo "3. Execute /home/aspuser/app/ofasp_demo/auto-trigger-cicd.sh"
echo "4. Deploy fixed MAIN001.class to volume/DISK01/TESTLIB"
echo ""

# Start the monitor
python3 /home/aspuser/app/monitoring/scripts/zabbix_abend_monitor.py
