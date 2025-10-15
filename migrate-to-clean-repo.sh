#!/bin/bash

# OpenASP AX Clean Repository Migration Script
# Author: shin.jeiths@gmail.com
# Date: 2025-01-17

set -e

echo "[START] OpenASP AX Repository Migration"
echo "========================================="

# Configuration
SOURCE_DIR="/home/aspuser/app"
TARGET_DIR="/tmp/openasp-ax-clean"
AUTHOR_NAME="Shin Jeiths"
AUTHOR_EMAIL="shin.jeiths@gmail.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create target directory
echo -e "${GREEN}[1/6] Creating clean repository structure${NC}"
rm -rf $TARGET_DIR
mkdir -p $TARGET_DIR

# Copy essential source code only
echo -e "${GREEN}[2/6] Copying essential source code${NC}"

# Core application directories
mkdir -p $TARGET_DIR/ofasp-refactor
cp -r $SOURCE_DIR/ofasp-refactor/src $TARGET_DIR/ofasp-refactor/
cp -r $SOURCE_DIR/ofasp-refactor/public $TARGET_DIR/ofasp-refactor/
cp -r $SOURCE_DIR/ofasp-refactor/python-service $TARGET_DIR/ofasp-refactor/
cp -r $SOURCE_DIR/ofasp-refactor/server $TARGET_DIR/ofasp-refactor/
cp -r $SOURCE_DIR/ofasp-refactor/dslock_suite $TARGET_DIR/ofasp-refactor/
cp $SOURCE_DIR/ofasp-refactor/package.json $TARGET_DIR/ofasp-refactor/
cp $SOURCE_DIR/ofasp-refactor/tsconfig.json $TARGET_DIR/ofasp-refactor/ 2>/dev/null || true

mkdir -p $TARGET_DIR/asp-manager
cp -r $SOURCE_DIR/asp-manager/src $TARGET_DIR/asp-manager/
cp -r $SOURCE_DIR/asp-manager/public $TARGET_DIR/asp-manager/
cp $SOURCE_DIR/asp-manager/package.json $TARGET_DIR/asp-manager/
cp $SOURCE_DIR/asp-manager/tsconfig.json $TARGET_DIR/asp-manager/ 2>/dev/null || true

mkdir -p $TARGET_DIR/ofasp-devops
cp -r $SOURCE_DIR/ofasp-devops/src $TARGET_DIR/ofasp-devops/ 2>/dev/null || true
cp -r $SOURCE_DIR/ofasp-devops/pages $TARGET_DIR/ofasp-devops/ 2>/dev/null || true
cp $SOURCE_DIR/ofasp-devops/package.json $TARGET_DIR/ofasp-devops/ 2>/dev/null || true
cp $SOURCE_DIR/ofasp-devops/next.config.js $TARGET_DIR/ofasp-devops/ 2>/dev/null || true

mkdir -p $TARGET_DIR/server
cp -r $SOURCE_DIR/server/*.py $TARGET_DIR/server/
cp -r $SOURCE_DIR/server/system-cmds $TARGET_DIR/server/
cp -r $SOURCE_DIR/server/aspmgr $TARGET_DIR/server/ 2>/dev/null || true

mkdir -p $TARGET_DIR/dbio
cp -r $SOURCE_DIR/dbio/*.py $TARGET_DIR/dbio/ 2>/dev/null || true
cp -r $SOURCE_DIR/dbio/backends $TARGET_DIR/dbio/ 2>/dev/null || true

# Configuration files
mkdir -p $TARGET_DIR/config
cp $SOURCE_DIR/config/asp.conf $TARGET_DIR/config/
cp $SOURCE_DIR/config/catalog.json $TARGET_DIR/config/

# Database schemas
mkdir -p $TARGET_DIR/database
cp $SOURCE_DIR/database/*.sql $TARGET_DIR/database/ 2>/dev/null || true

# Scripts
mkdir -p $TARGET_DIR/scripts
cp $SOURCE_DIR/scripts/*.sh $TARGET_DIR/scripts/ 2>/dev/null || true

# Volume structure (empty directories)
mkdir -p $TARGET_DIR/volume/DISK01/{TESTLIB,PRODLIB,XMLLIB,JAVA,COB,CL,SMED,LAYOUT}

# Documentation
cp $SOURCE_DIR/README.md $TARGET_DIR/
cp $SOURCE_DIR/.gitignore $TARGET_DIR/
cp $SOURCE_DIR/.env.example $TARGET_DIR/

# Create essential documentation
echo -e "${GREEN}[3/6] Creating project documentation${NC}"

cat > $TARGET_DIR/ARCHITECTURE.md << 'EOF'
# OpenASP AX Architecture

## System Overview
OpenASP AX is a comprehensive platform for migrating legacy ASP systems to modern open-source technologies.

## Core Services
- **Port 3000**: SMED Map Viewer
- **Port 3003**: Python EBCDIC Conversion Service
- **Port 3005**: OpenASP Refactor Main
- **Port 3007**: ASP Manager
- **Port 8000**: API Server

## Technology Stack
- Frontend: React 19, TypeScript, Tailwind CSS
- Backend: Python Flask, Java Spring, Node.js
- Database: PostgreSQL 15
- Message Queue: WebSocket, Socket.IO
EOF

cat > $TARGET_DIR/CONTRIBUTING.md << 'EOF'
# Contributing to OpenASP AX

## Development Setup
1. Copy `.env.example` to `.env`
2. Update database credentials
3. Install dependencies
4. Run migration scripts

## Code Style
- Follow CODING_RULES.md
- No hardcoding allowed
- All data must be loaded dynamically

## Pull Request Process
1. Create feature branch
2. Write tests
3. Update documentation
4. Submit PR for review
EOF

# Initialize git repository
echo -e "${GREEN}[4/6] Initializing new git repository${NC}"
cd $TARGET_DIR
git init
git config user.name "$AUTHOR_NAME"
git config user.email "$AUTHOR_EMAIL"

# Create initial commit
echo -e "${GREEN}[5/6] Creating initial commit${NC}"
git add .
git commit -m "Initial commit: OpenASP AX - Legacy Migration Platform

- Core services and APIs
- COBOL/CL conversion engines
- EBCDIC dataset converters
- SMED map viewer
- AI-powered management interface
- dslock_suite for file I/O
- PostgreSQL catalog system

Author: $AUTHOR_NAME <$AUTHOR_EMAIL>"

# Summary
echo -e "${GREEN}[6/6] Migration completed successfully!${NC}"
echo "========================================="
echo -e "${YELLOW}Clean repository created at: $TARGET_DIR${NC}"
echo ""
echo "Repository Statistics:"
du -sh $TARGET_DIR | awk '{print "Total Size: " $1}'
find $TARGET_DIR -type f -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.py" -o -name "*.java" | wc -l | awk '{print "Source Files: " $1}'
git -C $TARGET_DIR log --oneline | wc -l | awk '{print "Commits: " $1}'
echo ""
echo "Next Steps:"
echo "1. cd $TARGET_DIR"
echo "2. git remote add origin <your-new-repo-url>"
echo "3. git push -u origin main"
echo ""
echo "[COMPLETE] Repository is ready for upload to GitHub/GitLab"