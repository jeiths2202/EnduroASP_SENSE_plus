#!/usr/bin/env python3
"""
OpenASP AX DSLock Suite Monitor
Checks dslock_suite status and lock database health
Author: Claude Code Assistant
Created: 2025-08-21
Complies with: CODING_RULES.md (No hardcoding, <200 lines)
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


def load_config():
    """Load dslock configuration from environment variables"""
    return {
        'dslock_db': os.environ.get('DSLOCK_DB', '/tmp/dslock.jsonl'),
        'dslock_bin': os.environ.get('DSLOCK_BIN', 
                                   '/home/aspuser/app/ofasp-refactor/dslock_suite/build/dslockctl'),
        'catalog_json': os.environ.get('CATALOG_JSON', 
                                     '/home/aspuser/app/config/catalog.json'),
        'volume_dir': os.environ.get('VOLUME_DIR', '/home/aspuser/app/volume'),
        'timeout': int(os.environ.get('DSLOCK_TIMEOUT', 10))
    }


def check_dslock_binary():
    """Check if dslockctl binary exists and is executable"""
    config = load_config()
    dslock_bin = Path(config['dslock_bin'])
    return {
        'exists': dslock_bin.exists(),
        'executable': dslock_bin.is_file() and os.access(dslock_bin, os.X_OK),
        'path': str(dslock_bin)
    }


def get_dslock_locks():
    """Get current locks using dslockctl query"""
    config = load_config()
    try:
        cmd = [config['dslock_bin'], 'query']
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              timeout=config['timeout'])
        
        if result.returncode == 0:
            locks_data = json.loads(result.stdout) if result.stdout.strip() else []
            return {
                'status': 'success',
                'lock_count': len(locks_data),
                'locks': locks_data
            }
        else:
            return {
                'status': 'error',
                'error': result.stderr,
                'lock_count': 0
            }
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'lock_count': 0}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'lock_count': 0}


def check_dslock_database():
    """Check dslock database file status"""
    config = load_config()
    db_path = Path(config['dslock_db'])
    
    if not db_path.exists():
        return {
            'exists': False,
            'size': 0,
            'readable': False,
            'line_count': 0
        }
    
    try:
        stat_info = db_path.stat()
        with open(db_path, 'r') as f:
            lines = f.readlines()
        
        return {
            'exists': True,
            'size': stat_info.st_size,
            'readable': True,
            'line_count': len(lines),
            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        }
    except Exception as e:
        return {
            'exists': True,
            'size': 0,
            'readable': False,
            'error': str(e),
            'line_count': 0
        }


def check_catalog_json():
    """Check catalog.json accessibility"""
    config = load_config()
    catalog_path = Path(config['catalog_json'])
    
    if not catalog_path.exists():
        return {'exists': False, 'readable': False}
    
    try:
        with open(catalog_path, 'r') as f:
            catalog_data = json.load(f)
        
        dataset_count = 0
        for volume in catalog_data.values():
            if isinstance(volume, dict):
                for library in volume.values():
                    if isinstance(library, dict):
                        dataset_count += len([item for item in library.values() 
                                            if isinstance(item, dict) and 
                                               item.get('TYPE') == 'DATASET'])
        
        return {
            'exists': True,
            'readable': True,
            'dataset_count': dataset_count,
            'volume_count': len(catalog_data)
        }
    except Exception as e:
        return {
            'exists': True,
            'readable': False,
            'error': str(e)
        }


def main():
    """Main dslock monitoring function"""
    timestamp = datetime.now().isoformat()
    
    # Check all dslock components
    binary_status = check_dslock_binary()
    lock_status = get_dslock_locks()
    db_status = check_dslock_database()
    catalog_status = check_catalog_json()
    
    results = {
        'timestamp': timestamp,
        'dslock_binary': binary_status,
        'active_locks': lock_status,
        'lock_database': db_status,
        'catalog_json': catalog_status,
        'overall_status': 1 if (binary_status['executable'] and 
                               lock_status['status'] in ['success', 'timeout'] and
                               db_status['readable'] and 
                               catalog_status['readable']) else 0
    }
    
    # Output format based on arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print(json.dumps(results, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == '--locks':
        print(lock_status['lock_count'])
    else:
        # Default: overall status for Zabbix
        print(results['overall_status'])
    
    return 0 if results['overall_status'] else 1


if __name__ == '__main__':
    sys.exit(main())