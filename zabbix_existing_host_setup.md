# Add ABEND Monitoring to Existing OpenASP AX Host

## Quick Setup Steps:

### 1. Add Items to OpenASP AX Host
**Configuration → Hosts → OpenASP AX → Items → Create item**

#### Item 1: ABEND Detection
```
Name: ABEND Detection Check
Type: Zabbix agent
Key: openasp.abend.check
Type of information: Text
Update interval: 30s
```

#### Item 2: ABEND Count
```
Name: ABEND Count
Type: Zabbix agent  
Key: openasp.abend.count
Type of information: Numeric (unsigned)
Update interval: 30s
```

### 2. Add Triggers to OpenASP AX Host
**Configuration → Hosts → OpenASP AX → Triggers → Create trigger**

#### Trigger 1: ABEND Alert
```
Name: ABEND Detected on OpenASP System
Severity: High
Expression: last(/OpenASP AX/openasp.abend.count)>0
```

#### Trigger 2: Critical ABEND Alert
```
Name: Multiple ABENDs Critical
Severity: Disaster
Expression: last(/OpenASP AX/openasp.abend.count)>2  
```

### 3. Immediate Verification
After setup, check:
- **Monitoring → Latest data** (filter: OpenASP AX)
- **Monitoring → Problems** (ABEND triggers)

Current ABEND count: 4 (should trigger alerts immediately)

### 4. Test Real-time Monitoring
```bash
# Generate new ABEND for testing
java -cp ".:volume/DISK01/JAVA" trigger_abend_test

# Check Zabbix detection
python3 /home/aspuser/app/monitoring/scripts/check_abend.py --json
```

### 5. Expected Results
- **Problems** menu will show red ABEND alerts
- **Latest data** will show openasp.abend.count = 4+
- Real-time updates every 30 seconds