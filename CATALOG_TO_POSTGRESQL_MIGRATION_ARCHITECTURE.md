# Catalog.json to PostgreSQL Migration Architecture

## Executive Summary

This document outlines a comprehensive architecture for migrating the OpenASP system from file-based catalog.json storage to a PostgreSQL database. The migration is designed to be non-disruptive, scalable, and maintain backward compatibility.

## Current State Analysis

### Catalog.json Usage Patterns

Based on the codebase analysis, catalog.json is used in the following ways:

1. **Hierarchical Data Structure**
   - Volume → Library → Object (Dataset/Program/Map/Job)
   - Each object has type-specific attributes

2. **Primary Usage Points**
   - `asp_commands.py`: Core CRUD operations via `get_catalog_info()` and `update_catalog_info()`
   - `api_server.py`: REST endpoints for catalog access
   - Command functions: `crtfile.py`, `dltfile.py`, `dspfd.py`, etc.
   - Java interface: `dslock_java_interface.py`

3. **Data Types Stored**
   - **DATASET**: File metadata (RECTYPE, RECLEN, ENCODING)
   - **PGM**: Program metadata (PGMTYPE, VERSION, CLASSFILE)
   - **MAP**: Screen/form definitions (MAPTYPE, ROWS, COLS)
   - **JOB**: Batch job definitions (JOBTYPE, SCHEDULE)
   - **COPYBOOK**: COBOL copybook definitions
   - **LAYOUT**: Record layout definitions

## PostgreSQL Database Schema Design

### Core Tables

```sql
-- Volumes table
CREATE TABLE volumes (
    volume_id SERIAL PRIMARY KEY,
    volume_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Libraries table
CREATE TABLE libraries (
    library_id SERIAL PRIMARY KEY,
    volume_id INTEGER REFERENCES volumes(volume_id) ON DELETE CASCADE,
    library_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(volume_id, library_name)
);

-- Objects table (base table for all object types)
CREATE TABLE objects (
    object_id SERIAL PRIMARY KEY,
    library_id INTEGER REFERENCES libraries(library_id) ON DELETE CASCADE,
    object_name VARCHAR(255) NOT NULL,
    object_type VARCHAR(20) NOT NULL CHECK (object_type IN ('DATASET', 'PGM', 'MAP', 'JOB', 'COPYBOOK', 'LAYOUT')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(library_id, object_name)
);

-- Dataset-specific attributes
CREATE TABLE dataset_attributes (
    object_id INTEGER PRIMARY KEY REFERENCES objects(object_id) ON DELETE CASCADE,
    rectype VARCHAR(10) DEFAULT 'FB',
    reclen INTEGER DEFAULT 80,
    encoding VARCHAR(50) DEFAULT 'utf-8',
    recfm VARCHAR(10),
    lrecl INTEGER,
    records_count INTEGER,
    conversion_info JSONB
);

-- Program-specific attributes
CREATE TABLE program_attributes (
    object_id INTEGER PRIMARY KEY REFERENCES objects(object_id) ON DELETE CASCADE,
    pgmtype VARCHAR(20) NOT NULL,
    pgmname VARCHAR(255),
    version VARCHAR(20) DEFAULT '1.0',
    classfile VARCHAR(500),
    jarfile VARCHAR(500),
    sourcefile VARCHAR(500),
    shellfile VARCHAR(500),
    main_method BOOLEAN DEFAULT FALSE,
    dependencies TEXT,
    execution_mode VARCHAR(50),
    original_source VARCHAR(500),
    naming_convention VARCHAR(20),
    japanese_support BOOLEAN DEFAULT FALSE,
    asp_ready BOOLEAN DEFAULT TRUE
);

-- Map-specific attributes
CREATE TABLE map_attributes (
    object_id INTEGER PRIMARY KEY REFERENCES objects(object_id) ON DELETE CASCADE,
    maptype VARCHAR(20) DEFAULT 'SMED',
    mapfile VARCHAR(500),
    rows INTEGER DEFAULT 24,
    cols INTEGER DEFAULT 80,
    responsive BOOLEAN DEFAULT FALSE
);

-- Job-specific attributes
CREATE TABLE job_attributes (
    object_id INTEGER PRIMARY KEY REFERENCES objects(object_id) ON DELETE CASCADE,
    jobtype VARCHAR(20) DEFAULT 'BATCH',
    schedule VARCHAR(50) DEFAULT 'MANUAL',
    command VARCHAR(500)
);

-- Generic attributes (for extensibility)
CREATE TABLE object_attributes (
    attribute_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES objects(object_id) ON DELETE CASCADE,
    attribute_key VARCHAR(100) NOT NULL,
    attribute_value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    UNIQUE(object_id, attribute_key)
);

-- Indexes for performance
CREATE INDEX idx_objects_type ON objects(object_type);
CREATE INDEX idx_objects_updated ON objects(updated_at DESC);
CREATE INDEX idx_object_attributes_key ON object_attributes(attribute_key);

-- Full-text search support
CREATE INDEX idx_objects_search ON objects USING gin(to_tsvector('english', object_name || ' ' || COALESCE(description, '')));
```

### Views for Compatibility

```sql
-- Create a view that mimics the catalog.json structure
CREATE VIEW catalog_view AS
WITH object_details AS (
    SELECT 
        v.volume_name,
        l.library_name,
        o.object_name,
        o.object_type,
        o.description,
        o.created_at,
        o.updated_at,
        -- Dataset attributes
        da.rectype,
        da.reclen,
        da.encoding,
        da.recfm,
        da.lrecl,
        da.records_count,
        da.conversion_info,
        -- Program attributes
        pa.pgmtype,
        pa.pgmname,
        pa.version,
        pa.classfile,
        pa.jarfile,
        pa.sourcefile,
        pa.shellfile,
        pa.main_method,
        pa.dependencies,
        pa.execution_mode,
        -- Map attributes
        ma.maptype,
        ma.mapfile,
        ma.rows,
        ma.cols,
        ma.responsive,
        -- Job attributes
        ja.jobtype,
        ja.schedule,
        ja.command
    FROM objects o
    JOIN libraries l ON o.library_id = l.library_id
    JOIN volumes v ON l.volume_id = v.volume_id
    LEFT JOIN dataset_attributes da ON o.object_id = da.object_id
    LEFT JOIN program_attributes pa ON o.object_id = pa.object_id
    LEFT JOIN map_attributes ma ON o.object_id = ma.object_id
    LEFT JOIN job_attributes ja ON o.object_id = ja.object_id
)
SELECT 
    volume_name,
    library_name,
    object_name,
    jsonb_strip_nulls(
        jsonb_build_object(
            'TYPE', object_type,
            'CREATED', created_at,
            'UPDATED', updated_at,
            'DESCRIPTION', description,
            -- Dataset fields
            'RECTYPE', rectype,
            'RECLEN', reclen,
            'ENCODING', encoding,
            'RECFM', recfm,
            'LRECL', lrecl,
            'RECORDS_COUNT', records_count,
            'CONVERSION', conversion_info,
            -- Program fields
            'PGMTYPE', pgmtype,
            'PGMNAME', pgmname,
            'VERSION', version,
            'CLASSFILE', classfile,
            'JARFILE', jarfile,
            'SOURCEFILE', sourcefile,
            'SHELLFILE', shellfile,
            'MAIN_METHOD', main_method,
            'DEPENDENCIES', dependencies,
            'EXECUTION_MODE', execution_mode,
            -- Map fields
            'MAPTYPE', maptype,
            'MAPFILE', mapfile,
            'ROWS', rows,
            'COLS', cols,
            'RESPONSIVE', responsive,
            -- Job fields
            'JOBTYPE', jobtype,
            'SCHEDULE', schedule,
            'COMMAND', command
        )
    ) as attributes
FROM object_details;
```

## DBIO Module Architecture

### Design Principles

1. **Database Agnostic**: Support multiple database backends
2. **Connection Pooling**: Efficient resource management
3. **Transaction Support**: ACID compliance
4. **Caching Layer**: Redis integration for performance
5. **Backward Compatible**: Maintain existing API signatures

### Module Structure

```python
# dbio/__init__.py
from .core import DBIOManager
from .backends import PostgreSQLBackend, MySQLBackend, SQLiteBackend, JSONFileBackend
from .cache import CacheManager
from .migration import MigrationManager

# dbio/core.py
class DBIOManager:
    """Main database I/O manager with pluggable backends"""
    
    def __init__(self, config):
        self.backend = self._create_backend(config)
        self.cache = CacheManager(config.get('cache'))
        self.config = config
    
    def get_catalog_info(self):
        """Get complete catalog - maintains compatibility"""
        pass
    
    def update_catalog_info(self, volume, library, object_name, object_type="DATASET", **kwargs):
        """Update catalog - maintains compatibility"""
        pass
    
    def query_objects(self, filters=None, sort=None, limit=None):
        """Advanced querying capability"""
        pass
    
    def bulk_operations(self, operations):
        """Batch operations for performance"""
        pass

# dbio/backends/postgresql.py
class PostgreSQLBackend:
    """PostgreSQL implementation of catalog storage"""
    
    def __init__(self, connection_string):
        self.pool = self._create_connection_pool(connection_string)
    
    def get_all_objects(self):
        """Retrieve all objects in catalog.json format"""
        pass
    
    def update_object(self, volume, library, object_name, attributes):
        """Update or create an object"""
        pass
    
    def delete_object(self, volume, library, object_name):
        """Delete an object"""
        pass
    
    def search_objects(self, query):
        """Full-text search across objects"""
        pass

# dbio/cache.py
class CacheManager:
    """Redis-based caching layer"""
    
    def __init__(self, redis_config):
        self.redis_client = self._create_redis_client(redis_config)
        self.ttl = redis_config.get('ttl', 300)  # 5 minutes default
    
    def get(self, key):
        """Get from cache"""
        pass
    
    def set(self, key, value, ttl=None):
        """Set in cache with TTL"""
        pass
    
    def invalidate(self, pattern):
        """Invalidate cache entries matching pattern"""
        pass
```

### Configuration

```yaml
# config/dbio.yaml
dbio:
  backend: postgresql  # Options: postgresql, mysql, sqlite, json_file
  
  postgresql:
    host: localhost
    port: 5432
    database: openasp_catalog
    user: openasp
    password: ${OPENASP_DB_PASSWORD}
    pool_size: 20
    max_overflow: 10
    pool_timeout: 30
    
  cache:
    enabled: true
    backend: redis
    redis:
      host: localhost
      port: 6379
      db: 0
      ttl: 300
      
  migration:
    auto_migrate: true
    backup_before_migrate: true
    backup_location: /var/backups/openasp/catalog/
```

## Migration Strategy

### Phase 1: Preparation (Week 1-2)

1. **Setup PostgreSQL Database**
   - Create database and user
   - Apply schema migrations
   - Setup replication for HA

2. **Implement DBIO Module**
   - Core functionality
   - PostgreSQL backend
   - Unit and integration tests

3. **Create Migration Tools**
   - JSON to PostgreSQL converter
   - Data validation scripts
   - Rollback procedures

### Phase 2: Parallel Run (Week 3-4)

1. **Deploy Hybrid Mode**
   - DBIO module reads from JSON, writes to both
   - Monitor for discrepancies
   - Performance benchmarking

2. **Update Components**
   - Modify asp_commands.py to use DBIO
   - Update api_server.py endpoints
   - Test all command functions

### Phase 3: Cutover (Week 5)

1. **Switch Primary Storage**
   - DBIO reads from PostgreSQL
   - JSON becomes backup/cache
   - Monitor system stability

2. **Performance Optimization**
   - Query optimization
   - Index tuning
   - Cache warming

### Phase 4: Cleanup (Week 6)

1. **Remove JSON Dependencies**
   - Update all direct file access
   - Archive JSON files
   - Update documentation

## Backward Compatibility Layer

### JSON File Sync

```python
class JSONCompatibilityLayer:
    """Maintains catalog.json file for legacy systems"""
    
    def __init__(self, dbio_manager, json_path):
        self.dbio = dbio_manager
        self.json_path = json_path
        self.sync_interval = 60  # seconds
    
    def start_sync(self):
        """Start background sync thread"""
        pass
    
    def sync_to_json(self):
        """Write current database state to JSON"""
        catalog = self.dbio.get_catalog_info()
        with open(self.json_path, 'w') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    def sync_from_json(self):
        """Read JSON changes back to database"""
        pass
```

### API Compatibility

All existing APIs will maintain their signatures:

```python
# Existing function signatures preserved
def get_catalog_info():
    return dbio_manager.get_catalog_info()

def update_catalog_info(volume, library, object_name, object_type="DATASET", **kwargs):
    return dbio_manager.update_catalog_info(volume, library, object_name, object_type, **kwargs)
```

## Performance Considerations

### Caching Strategy

1. **Read-Through Cache**
   - Cache catalog queries
   - TTL based on update frequency
   - Invalidate on writes

2. **Write-Behind Cache**
   - Queue writes for batch processing
   - Reduce database load
   - Maintain consistency

### Database Optimizations

1. **Connection Pooling**
   - Reuse connections
   - Configure pool size based on load
   - Monitor pool metrics

2. **Query Optimization**
   - Use prepared statements
   - Batch similar operations
   - Optimize indexes

3. **Partitioning**
   - Partition by volume for large installations
   - Archive old data
   - Maintain query performance

## Monitoring and Observability

### Metrics to Track

1. **Performance Metrics**
   - Query response times
   - Cache hit rates
   - Connection pool utilization

2. **Business Metrics**
   - Objects created/updated/deleted
   - Most accessed objects
   - Storage growth trends

3. **Health Metrics**
   - Database availability
   - Replication lag
   - Error rates

### Logging

```python
# Structured logging for all operations
logger.info("catalog_operation", {
    "operation": "update",
    "volume": volume,
    "library": library,
    "object": object_name,
    "type": object_type,
    "duration_ms": duration,
    "cache_hit": cache_hit
})
```

## Security Considerations

1. **Access Control**
   - Row-level security in PostgreSQL
   - API authentication/authorization
   - Audit logging

2. **Data Protection**
   - Encryption at rest
   - SSL/TLS for connections
   - Sensitive data masking

3. **Backup and Recovery**
   - Automated backups
   - Point-in-time recovery
   - Disaster recovery procedures

## Technology Recommendations

### Core Technologies

1. **PostgreSQL 15+**
   - JSON/JSONB support
   - Full-text search
   - Row-level security
   - Excellent performance

2. **Redis 7+**
   - Caching layer
   - Pub/sub for invalidation
   - Persistence options

3. **SQLAlchemy 2.0+**
   - ORM for Python
   - Connection pooling
   - Migration support

### Supporting Tools

1. **Alembic**
   - Database migrations
   - Version control
   - Rollback support

2. **pgBouncer**
   - Connection pooling
   - Transaction pooling
   - Load balancing

3. **Prometheus + Grafana**
   - Metrics collection
   - Visualization
   - Alerting

## Potential Bottlenecks and Mitigations

### Bottleneck 1: High Write Volume

**Issue**: Frequent catalog updates could overwhelm database

**Mitigation**:
- Batch writes in transactions
- Use write-behind caching
- Consider read replicas

### Bottleneck 2: Large Catalog Size

**Issue**: Performance degradation with millions of objects

**Mitigation**:
- Implement partitioning
- Use materialized views
- Archive inactive objects

### Bottleneck 3: Network Latency

**Issue**: Database server network latency

**Mitigation**:
- Deploy database close to application
- Use connection pooling
- Implement aggressive caching

## Implementation Roadmap

### Milestone 1: Foundation (2 weeks)
- [ ] Setup PostgreSQL database
- [ ] Create schema and migrations
- [ ] Implement basic DBIO module
- [ ] Unit tests for DBIO

### Milestone 2: Integration (2 weeks)
- [ ] Integrate DBIO with asp_commands.py
- [ ] Update API endpoints
- [ ] Implement caching layer
- [ ] Integration tests

### Milestone 3: Migration (1 week)
- [ ] Create migration scripts
- [ ] Test migration with production data
- [ ] Implement rollback procedures
- [ ] Performance testing

### Milestone 4: Deployment (1 week)
- [ ] Deploy in parallel mode
- [ ] Monitor and tune
- [ ] Cutover to PostgreSQL
- [ ] Documentation and training

## Conclusion

This architecture provides a robust, scalable solution for migrating from catalog.json to PostgreSQL while maintaining system stability and performance. The phased approach ensures minimal disruption, and the backward compatibility layer provides a safety net during transition.

The flexible DBIO module design allows for future expansion to other database systems and provides advanced features like caching, full-text search, and batch operations that weren't possible with the JSON file approach.