# Zabbix Manual Setup Guide for ABEND Monitoring

## Step 1: Create Host
1. Go to **Configuration → Hosts**
2. Click **Create host**
3. Fill in:
   - Host name: `OpenASP-AX-Server`
   - Visible name: `OpenASP AX Production Server`
   - Groups: Select `Linux servers`
   - Interfaces: Agent, IP: `127.0.0.1`, Port: `10050`
4. Click **Add**

## Step 2: Create Items
1. Go to **Configuration → Hosts** → Find `OpenASP-AX-Server` → Click **Items**
2. Click **Create item**

### Item 1: ABEND Detection
- Name: `ABEND Detection Check`
- Type: `Zabbix agent`
- Key: `openasp.abend.check`
- Type of information: `Text`
- Update interval: `30s`

### Item 2: ABEND Count
- Name: `ABEND Count`
- Type: `Zabbix agent`
- Key: `openasp.abend.count`
- Type of information: `Numeric (unsigned)`
- Update interval: `30s`

## Step 3: Create Triggers
1. Go to **Configuration → Hosts** → Find `OpenASP-AX-Server` → Click **Triggers**
2. Click **Create trigger**

### Trigger 1: ABEND Alert
- Name: `ABEND Detected on OpenASP System`
- Severity: `High`
- Expression: `last(/OpenASP-AX-Server/openasp.abend.count)>0`

### Trigger 2: Multiple ABEND Alert  
- Name: `Multiple ABENDs Detected`
- Severity: `Disaster`
- Expression: `last(/OpenASP-AX-Server/openasp.abend.count)>2`

## Step 4: Test Connection
After setup, test the Zabbix agent connection:
```bash
# Check if items are collecting data
python3 /home/aspuser/app/monitoring/scripts/check_abend.py --json
```

## Step 5: Generate ABEND for Testing
```bash
# Trigger new ABEND for testing
java -cp ".:volume/DISK01/JAVA" trigger_abend_test
```

After these steps, you should see ABEND alerts in:
- **Monitoring → Problems**
- **Monitoring → Latest data**
- **Monitoring → Dashboard**