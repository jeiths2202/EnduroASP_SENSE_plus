#!/usr/bin/env python3
"""
Migration Script: catalog.json to PostgreSQL

This script migrates the OpenASP catalog from JSON file storage to PostgreSQL.
It includes validation, backup, and rollback capabilities.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dbio.core import DBIOManager
from dbio.migration import MigrationManager
from dbio.exceptions import DBIOException


def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise DBIOException(f"Failed to load config: {e}")


def create_default_config() -> Dict[str, Any]:
    """Create default configuration."""
    return {
        "source": {
            "backend": "json_file",
            "json_file": {
                "file_path": "/home/aspuser/app/config/catalog.json"
            }
        },
        "target": {
            "backend": "postgresql",
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "openasp_catalog",
                "user": "openasp",
                "password": os.getenv("OPENASP_DB_PASSWORD", ""),
                "pool_size": 20
            },
            "cache": {
                "enabled": True,
                "backend": "redis",
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "db": 0
                },
                "ttl": 300
            }
        },
        "migration": {
            "backup_location": "/var/backups/openasp/catalog",
            "validate_after_migration": True,
            "create_backup": True
        }
    }


def validate_prerequisites(config: Dict[str, Any]) -> List[str]:
    """Validate migration prerequisites."""
    issues = []
    
    # Check source file exists
    source_config = config.get('source', {}).get('json_file', {})
    source_path = source_config.get('file_path')
    if source_path and not os.path.exists(source_path):
        issues.append(f"Source catalog file not found: {source_path}")
    
    # Check PostgreSQL connection
    try:
        test_config = config.get('target', {})
        test_manager = DBIOManager(test_config)
        health = test_manager.health_check()
        if health.get('status') != 'healthy':
            issues.append(f"PostgreSQL health check failed: {health.get('error', 'Unknown error')}")
        test_manager.close()
    except Exception as e:
        issues.append(f"PostgreSQL connection test failed: {str(e)}")
    
    # Check backup directory
    backup_location = config.get('migration', {}).get('backup_location')
    if backup_location:
        try:
            os.makedirs(backup_location, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create backup directory: {str(e)}")
    
    return issues


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description="Migrate OpenASP catalog to PostgreSQL")
    parser.add_argument('--config', '-c', 
                       help='Configuration file path',
                       default='config/migration.json')
    parser.add_argument('--dry-run', '-d', 
                       action='store_true',
                       help='Perform dry run without actual migration')
    parser.add_argument('--no-backup', 
                       action='store_true',
                       help='Skip backup creation')
    parser.add_argument('--no-validation', 
                       action='store_true',
                       help='Skip post-migration validation')
    parser.add_argument('--log-level', '-l',
                       default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level')
    parser.add_argument('--create-config', 
                       action='store_true',
                       help='Create default configuration file and exit')
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create default config if requested
    if args.create_config:
        config = create_default_config()
        with open(args.config, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Default configuration created: {args.config}")
        print("Please review and update the configuration before running migration.")
        return 0
    
    try:
        # Load configuration
        if not os.path.exists(args.config):
            logger.error(f"Configuration file not found: {args.config}")
            logger.info("Use --create-config to generate a default configuration file")
            return 1
        
        config = load_config(args.config)
        logger.info(f"Configuration loaded from: {args.config}")
        
        # Validate prerequisites
        issues = validate_prerequisites(config)
        if issues:
            logger.error("Prerequisites validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return 1
        
        logger.info("Prerequisites validation passed")
        
        # Initialize migration manager
        migration_manager = MigrationManager(
            config['source'],
            config['target']
        )
        
        # Perform migration
        logger.info("Starting catalog migration...")
        
        migration_config = config.get('migration', {})
        create_backup = migration_config.get('create_backup', True) and not args.no_backup
        validate_after = migration_config.get('validate_after_migration', True) and not args.no_validation
        
        stats = migration_manager.migrate_catalog(
            backup_before=create_backup,
            validate_after=validate_after,
            dry_run=args.dry_run
        )
        
        # Print results
        print("\n" + "="*60)
        print("MIGRATION RESULTS")
        print("="*60)
        print(f"Migration ID: {stats['migration_id']}")
        print(f"Started: {stats['started_at']}")
        print(f"Completed: {stats.get('completed_at', 'N/A')}")
        print(f"Dry Run: {stats['dry_run']}")
        print(f"Backup Created: {stats.get('backup_created', False)}")
        
        if stats.get('backup_path'):
            print(f"Backup Location: {stats['backup_path']}")
        
        print(f"Source Objects: {stats['source_objects']}")
        
        if not args.dry_run:
            print(f"Volumes: {stats.get('volumes', 0)}")
            print(f"Libraries: {stats.get('libraries', 0)}")
            print(f"Objects: {stats.get('objects', 0)}")
            
            if stats.get('validation'):
                validation = stats['validation']
                print(f"Validation: {'PASSED' if validation['success'] else 'FAILED'}")
                if validation.get('differences'):
                    print("Differences found:")
                    for diff in validation['differences']:
                        print(f"  - {diff}")
        
        if stats.get('errors'):
            print("Errors:")
            for error in stats['errors']:
                print(f"  - {error}")
        
        if stats.get('warnings'):
            print("Warnings:")
            for warning in stats['warnings']:
                print(f"  - {warning}")
        
        print("="*60)
        
        success = stats.get('success', True) and not stats.get('errors')
        
        if success:
            logger.info("Migration completed successfully!")
            return 0
        else:
            logger.error("Migration completed with errors")
            return 1
    
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())