# OpenASP Catalog Migration Plan: JSON to PostgreSQL

## Overview

This document outlines the comprehensive migration strategy for transitioning from `catalog.json` file-based storage to PostgreSQL database backend while maintaining 100% backward compatibility and zero service disruption.

## Current State Analysis

### Existing Catalog Structure
- **Format**: Hierarchical JSON structure (Volume → Library → Object)
- **Size**: ~1,300 objects across multiple volumes (DISK01, DISK02, TEST, etc.)
- **Object Types**: DATASET, PGM, MAP, JOB, COPYBOOK, LAYOUT
- **Encoding**: UTF-8 with Japanese (Shift_JIS) support

### Key Usage Patterns
```python
# Core functions used throughout codebase
get_catalog_info()                    # Returns complete catalog as dict
update_catalog_info(vol, lib, obj, type, **kwargs)  # Updates/creates entries
get_object_info(volume, library, name)              # Gets specific object
get_file_info(volume, filename)                     # Legacy compatibility
```

### Files Using Catalog Functions
- `/home/aspuser/app/server/system-cmds/functions/call.py` - Program execution
- `/home/aspuser/app/server/system-cmds/functions/crtfile.py` - File creation
- `/home/aspuser/app/server/system-cmds/functions/dltfile.py` - File deletion
- `/home/aspuser/app/server/system-cmds/functions/edtfile.py` - File editing
- `/home/aspuser/app/server/api_server.py` - Main API server
- 10+ other system command functions

## Migration Architecture

### DBIO Backend System
- **Core Manager**: `/home/aspuser/app/dbio/core.py`
- **PostgreSQL Backend**: `/home/aspuser/app/dbio/backends/postgresql.py`
- **JSON Backend**: `/home/aspuser/app/dbio/backends/json_file.py`
- **Migration Tools**: `/home/aspuser/app/dbio/migration.py`

### Database Schema
- **Tables**: volumes, libraries, objects, *_attributes tables
- **Views**: catalog_view (flat), catalog_json_view (hierarchical JSON)
- **Functions**: update_catalog_entry(), get_or_create_volume(), etc.
- **Indexes**: Full-text search, trigram fuzzy matching, performance indexes

### Backward Compatibility Layer
- **Enhanced Functions**: Modified `asp_commands.py` functions
- **Automatic Fallback**: JSON fallback if DBIO fails
- **Transparent Operation**: Existing code continues to work unchanged

## Migration Phases

### Phase 1: Preparation and Setup ⚙️
**Duration**: 1-2 days  
**Risk**: Low  
**Rollback**: Simple

#### Tasks:
1. **Database Setup**
   ```bash
   # Initialize PostgreSQL database
   python server/system-cmds/functions/setup_catalog_database.py init
   
   # Verify setup
   python server/system-cmds/functions/setup_catalog_database.py test
   ```

2. **Configuration Deployment**
   - Backend configuration system is ready at `/home/aspuser/app/config/catalog_backend_config.py`
   - Default configuration uses JSON backend (no change to current behavior)

3. **Code Integration**
   - Enhanced `asp_commands.py` functions are backward compatible
   - DBIO components are available but not active yet

#### Verification:
- All existing functionality works unchanged
- New configuration system is accessible
- Database schema is properly created
- Connection tests pass

### Phase 2: Dual-Write Migration Mode 🔄
**Duration**: 1-3 days  
**Risk**: Low-Medium  
**Rollback**: Disable migration mode

#### Tasks:
1. **Enable Migration Mode**
   ```bash
   # Enable dual-write mode
   python server/system-cmds/functions/catalog_migration.py enable-migration
   
   # Verify status
   python server/system-cmds/functions/catalog_migration.py status
   ```

2. **Initial Data Migration**
   ```bash
   # Dry run first
   python server/system-cmds/functions/catalog_migration.py migrate --dry-run
   
   # Actual migration with backup
   python server/system-cmds/functions/catalog_migration.py migrate
   ```

3. **Dual-Write Operation**
   - Reads continue from JSON (reliable)
   - Writes go to both JSON and PostgreSQL
   - Real-time synchronization of all catalog changes

#### Monitoring:
- Monitor write error logs
- Validate data consistency: `python server/system-cmds/functions/catalog_migration.py validate`
- Track performance impact (should be minimal)

#### Verification:
- All catalog operations continue normally
- PostgreSQL receives all new updates
- Data consistency validation passes
- No service disruption

### Phase 3: PostgreSQL Read-Write Mode 🚀
**Duration**: 1 day  
**Risk**: Medium  
**Rollback**: Switch back to JSON mode

#### Tasks:
1. **Final Synchronization**
   ```bash
   # Ensure PostgreSQL is fully up-to-date
   python server/system-cmds/functions/catalog_migration.py sync json_to_postgresql
   
   # Final validation
   python server/system-cmds/functions/catalog_migration.py validate
   ```

2. **Switch to PostgreSQL**
   ```bash
   # Switch primary backend to PostgreSQL
   python server/system-cmds/functions/catalog_migration.py switch-to-postgresql
   
   # Disable migration mode
   python server/system-cmds/functions/catalog_migration.py disable-migration
   ```

3. **Performance Optimization**
   - Enable caching (already configured)
   - Monitor query performance
   - Fine-tune connection pool settings

#### Verification:
- All reads come from PostgreSQL
- All writes go to PostgreSQL
- Performance is improved (caching enabled)
- JSON file remains as backup

### Phase 4: Cleanup and Optimization 🧹
**Duration**: 1 day  
**Risk**: Low  
**Rollback**: N/A (non-destructive)

#### Tasks:
1. **Performance Monitoring**
   - Monitor database performance
   - Analyze slow queries
   - Optimize indexes if needed

2. **Optional JSON Retirement**
   - Keep JSON file as backup (recommended)
   - Or remove JSON dependency after 30+ days of stable operation

3. **Documentation Update**
   - Update configuration documentation
   - Document new migration procedures
   - Create operational runbooks

## Rollback Strategies

### Emergency Rollback (Any Phase)
```bash
# Immediate switch back to JSON
python server/system-cmds/functions/catalog_migration.py switch-to-json

# Restore from backup if needed
python server/system-cmds/functions/catalog_migration.py rollback /path/to/backup.json
```

### Phase-Specific Rollbacks

#### Phase 1 Rollback:
- Simply don't proceed to Phase 2
- Remove DBIO integration if desired (optional)

#### Phase 2 Rollback:
```bash
# Disable migration mode
python server/system-cmds/functions/catalog_migration.py disable-migration

# Ensure JSON is current
python server/system-cmds/functions/catalog_migration.py sync postgresql_to_json
```

#### Phase 3 Rollback:
```bash
# Switch back to JSON
python server/system-cmds/functions/catalog_migration.py switch-to-json

# Re-enable migration mode if needed
python server/system-cmds/functions/catalog_migration.py enable-migration
```

## Risk Assessment

### Low Risk Items ✅
- Configuration system (no behavioral changes)
- Database setup (isolated)
- Dual-write mode (reads still from JSON)
- All phases have immediate rollback

### Medium Risk Items ⚠️
- PostgreSQL read mode (new read path)
- Connection pool management
- Performance impact of database operations

### Mitigation Strategies
1. **Comprehensive Testing**: Each phase includes validation steps
2. **Gradual Transition**: Phased approach allows early detection of issues
3. **Automatic Fallbacks**: Built-in JSON fallback in all functions
4. **Monitoring**: Real-time status monitoring and error logging
5. **Quick Rollback**: One-command rollback at any stage

## Success Criteria

### Phase 1 Success:
- [ ] Database connection tests pass
- [ ] Schema creation successful
- [ ] All existing functionality unchanged
- [ ] No service interruption

### Phase 2 Success:
- [ ] Migration mode enabled successfully
- [ ] Data migration completes without errors
- [ ] Validation shows 100% consistency
- [ ] All catalog operations work normally
- [ ] Write errors are zero or minimal

### Phase 3 Success:
- [ ] PostgreSQL read operations work correctly
- [ ] Performance is equal or better than JSON
- [ ] All existing functionality preserved
- [ ] Monitoring shows stable operation

### Final Success:
- [ ] 100% catalog operations via PostgreSQL
- [ ] Improved performance with caching
- [ ] Enhanced query capabilities available
- [ ] Full audit trail of all changes
- [ ] Scalable for future growth

## Implementation Commands

### Quick Start Migration (Recommended):
```bash
# Phase 1: Setup
cd /home/aspuser/app
python server/system-cmds/functions/setup_catalog_database.py init

# Phase 2: Dual-write migration
python server/system-cmds/functions/catalog_migration.py enable-migration
python server/system-cmds/functions/catalog_migration.py migrate

# Verify for 24+ hours, then Phase 3: Switch
python server/system-cmds/functions/catalog_migration.py validate
python server/system-cmds/functions/catalog_migration.py switch-to-postgresql
python server/system-cmds/functions/catalog_migration.py disable-migration
```

### Status Monitoring:
```bash
# Check migration status anytime
python server/system-cmds/functions/catalog_migration.py status

# Validate data consistency
python server/system-cmds/functions/catalog_migration.py validate

# Emergency rollback
python server/system-cmds/functions/catalog_migration.py switch-to-json
```

## Benefits After Migration

### Immediate Benefits:
- **Performance**: Database indexing and caching
- **Reliability**: ACID transactions and connection pooling
- **Monitoring**: Built-in health checks and statistics

### Future Capabilities:
- **Advanced Queries**: Full-text search, complex filtering
- **Audit Trail**: Complete change history
- **Scalability**: Handle much larger catalogs
- **Integration**: Easy integration with other database tools
- **Backup/Recovery**: Standard database backup procedures

## Support and Troubleshooting

### Common Issues:
1. **PostgreSQL Not Running**: Check `systemctl status postgresql`
2. **Connection Failures**: Verify database credentials in environment variables
3. **Permission Errors**: Ensure database user has proper permissions
4. **Migration Validation Fails**: Check for data corruption, re-run migration

### Log Locations:
- Application logs: `/home/aspuser/app/logs/`
- PostgreSQL logs: Check system PostgreSQL log location
- Migration logs: Captured in application logs with `[MIGRATION]` prefix

### Emergency Contacts:
- Database issues: Check PostgreSQL system status
- Application issues: Review application logs
- Data consistency: Use validation commands

---

**Note**: This migration maintains 100% backward compatibility. All existing code continues to work exactly as before, with enhanced capabilities available for future development.