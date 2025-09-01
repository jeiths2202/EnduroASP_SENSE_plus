# OpenASP AX - Legacy Migration Platform

## Project Overview

OpenASP AX is an integrated platform for migrating legacy ASP (Advanced System Products) systems to modern open-source technologies. It's a production-grade tool for actual legacy system migration, not a demo or prototype.

### Core Principle: No Hardcoding
This project strictly prohibits hardcoding under any circumstances:
- ❌ No "demo", "temporary", "test" excuses for hardcoding
- ❌ No mock data instead of real file system data
- ❌ No error bypassing (must solve root causes)
- ✅ All data must be dynamically loaded from real systems
- ✅ Error handling must solve root causes, not bypass them

## System Architecture

### Main Components

1. **SMED Map Viewer** (Port 3000)
   - Purpose: Legacy SMED screen map viewer
   - Tech: React, TypeScript, CSS Grid
   - Command: `npm start`

2. **Python Conversion Service** (Port 3003)
   - Purpose: EBCDIC/ASCII conversion backend
   - Tech: Python, Flask, Flask-CORS
   - Command: `FLASK_PORT=3003 python -c "from src.api.app import api; api.run()"`

3. **OpenASP Refactor** (Port 3005)
   - Purpose: Code conversion and refactoring tools with multimodal AI chat
   - Tech: React, TypeScript, CodeMirror
   - Command: `PORT=3005 npm start`

4. **ASP Manager** (Port 3007)
   - Purpose: AI-based system management interface
   - Tech: React, TensorFlow.js, Express.js
   - Command: `PORT=3007 npm start`

5. **API Server** (Port 8000)
   - Purpose: Unified backend API server with database integration
   - Tech: Python, Flask
   - Command: `python api_server.py`

6. **OpenASP DevOps** (Port 3016)
   - Purpose: Enterprise-grade CI/CD & automated monitoring platform
   - Tech: Next.js 14, TypeScript, Docker, GitHub Actions
   - Command: `cd ofasp-devops && npm run dev`

### Monitoring System (Zabbix)

- **Web Interface**: http://localhost:3015 (Admin/zabbix)
- **Monitoring Targets**: All OpenASP services, logs, dslock_suite, ABEND detection
- **Custom Monitoring**: ABEND CEE3204S real-time detection and auto-fix integration

## ABEND Auto-Fix System

### Integration Test Scenario
The system implements a fully automated failure response system:
**ABEND Occurrence → Zabbix Detection → DevOps CI/CD Auto-Fix → Recovery**

### ABEND Auto-Response Process

1. **ABEND Occurrence Stage**
   - Trigger: F3 key input causes CEE3204S ABEND in MAIN001.java
   - Location: `/home/aspuser/app/volume/DISK01/JAVA/MAIN001.java:handleF3Key()`
   - Logging: ABEND info recorded in `/home/aspuser/app/logs/abend.log`

2. **Zabbix Real-Time Detection**
   - Detection Script: `check_abend.py` (60-second cycle)
   - Zabbix Parameters: `openasp.abend.check`, `openasp.abend.count`
   - Notification: ABEND alert displayed in Zabbix UI

3. **CI/CD Auto-Fix Pipeline**
   - Workflow: ABEND Auto-Fix Pipeline (4 stages)
     1. 🔍 Detect and Analyze ABEND
     2. 🔧 Auto-Fix ABEND
     3. 🚀 Deploy Fixed Code
     4. 📢 Notify Fix Completion

4. **Real-Time Visualization Monitoring**
   - URL: http://localhost:3016 (CI/CD Workflow Visualizer)
   - Features: Real-time workflow status, job dependency graph, history tracking

## Development Environment

### Starting All Services
```bash
./master-start.sh
```

### Stopping All Services
```bash
./master-stop.sh
```

### Key Environment Variables
```bash
# Python conversion service
FLASK_PORT=3003
REACT_APP_PYTHON_CONVERTER_URL=http://localhost:3003

# OpenASP Refactor
PORT=3005

# ASP Manager
PORT=3007

# API Server
API_SERVER_PORT=8000
```

### Service Ports
- 3000: SMED Map Viewer
- 3003: Python EBCDIC Conversion Service
- 3005: OpenASP Refactor
- 3007: ASP Manager
- 3008: ASP Manager Backend
- 3010: Grafana (Monitoring Visualization)
- 3011: Prometheus (Metric Collection)
- 3015: Zabbix (System Monitoring)
- 3016: OpenASP DevOps (CI/CD & Monitoring)
- 8000: API Server

## File System Structure

```
/home/aspuser/app/
├── ofasp-refactor/          # Main refactoring platform
│   ├── src/                 # React source code
│   ├── python-service/      # Python backend
│   └── public/             # Static resources
├── asp-manager/            # AI management interface
│   ├── src/                # React source code
│   └── server.js          # Express proxy
├── server/                 # Backend services
│   └── aspmgr/            # Curses system manager
├── volume/                 # Legacy system file structure
│   └── DISK01/            # Main disk
│       └── JAVA/          # Java components
├── monitoring/             # Monitoring scripts and configs
├── ofasp-devops/           # CI/CD and DevOps platform
└── master-start.sh        # Complete environment startup
```

## Development Guidelines

### Critical Principle: No Hardcoding
This project is a production tool for actual legacy system processing. Hardcoding is absolutely prohibited.

### Internationalization Rules
1. **SJIS Encoding**: System scripts must use SHIFT_JIS encoding for ja_JP.sjis locale compatibility
2. **Emoji Ban**: No emojis in source code or system files (ASCII alternatives: [START], [OK], [NG])
3. **Comments**: All source code comments must be in English
4. **Language**: English preferred for messages (consider internationalization)

### File Creation Guidelines
1. **Shell Scripts (.sh)**: UTF-8 → SHIFT_JIS conversion, no emojis, English comments
2. **Python Scripts (.py)**: UTF-8 encoding, `# -*- coding: utf-8 -*-` declaration
3. **JavaScript/TypeScript**: UTF-8 encoding, English comments
4. **Configuration Files**: Consider SHIFT_JIS for system configs

## Testing

### ABEND Integration Testing
```bash
# Run complete ABEND auto-fix integration test scenario
./test_complete_scenario.sh
```

### Service Health Checks
```bash
curl http://localhost:3000         # SMED Viewer
curl http://localhost:3003/health  # Python conversion service
curl http://localhost:3005         # OpenASP Refactor
curl http://localhost:3007         # ASP Manager
curl http://localhost:8000         # API Server
curl http://localhost:3015         # Zabbix monitoring
curl http://localhost:3016         # OpenASP DevOps
```

## Program Registration

### Critical Requirement
All programs must be registered in `catalog.json` before execution. Unregistered programs cannot be run via CALL command.

### Registration Format
```json
{
  "DISK01": {
    "TESTLIB": {
      "CUINP001": {
        "TYPE": "PGM",
        "PGMTYPE": "JAVA",
        "PGMNAME": "CUINP001",
        "CLASSFILE": "CUINP001.class",
        "DESCRIPTION": "Customer data input program",
        "VERSION": "1.0",
        "CREATED": "2025-07-24T17:04:00.000000Z",
        "UPDATED": "2025-07-24T17:04:00.000000Z"
      }
    }
  }
}
```

### Related Files
- **catalog.json**: `/home/aspuser/app/asp-manager/public/config/catalog.json`
- **Program Files**: `/home/aspuser/app/volume/DISK01/TESTLIB/`
- **CL Parser**: `/home/aspuser/app/server/system-cmds/cl_parser.py`

## Key Directories

### Source Code
- `/home/aspuser/app/ofasp-refactor/src/` - Main React frontend
- `/home/aspuser/app/asp-manager/src/` - ASP Manager frontend
- `/home/aspuser/app/server/` - Backend services
- `/home/aspuser/app/ofasp-devops/src/` - DevOps platform frontend

### Legacy System Files
- `/home/aspuser/app/volume/DISK01/JAVA/` - Java components
- `/home/aspuser/app/volume/DISK01/SMED/` - SMED map files
- `/home/aspuser/app/volume/DISK01/LAYOUT/` - Layout files

### Monitoring and Logs
- `/home/aspuser/app/monitoring/scripts/` - Monitoring scripts
- `/home/aspuser/app/logs/` - Main log directory
- `/home/aspuser/app/ofasp-refactor/logs/` - Refactor logs

## Contributing

1. Read and understand the "No Hardcoding" principle
2. Plan implementation with real file system integration
3. Ensure file count matches user requirements exactly
4. Solve errors at root cause, don't bypass them
5. Commit changes with proper encoding rules
6. Verify file count consistency
7. Create pull request for code review

## Key AI Agent Reminder

```
This project is not a toy - it's a production tool for actual legacy system migration.

Never hardcode.
Never use "demo" as an excuse.
Never arbitrarily reduce user requirements.
Never bypass errors - solve them.

Process all files in the real file system accurately.
Don't miss even one file.
```