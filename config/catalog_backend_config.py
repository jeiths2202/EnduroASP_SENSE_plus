"""
Catalog Backend Configuration System
Provides flexible switching between JSON and PostgreSQL backends with backward compatibility.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration file paths
CONFIG_DIR = "/home/aspuser/app/config"
BACKEND_CONFIG_FILE = os.path.join(CONFIG_DIR, "catalog_backend.json")
DEFAULT_CATALOG_JSON = os.path.join(CONFIG_DIR, "catalog.json")

# Default configurations
DEFAULT_CONFIGS = {
    "json_file": {
        "backend": "json_file",
        "json_file": {
            "file_path": DEFAULT_CATALOG_JSON,
            "backup_path": DEFAULT_CATALOG_JSON + ".backup"
        },
        "cache": {
            "enabled": False
        }
    },
    "postgresql": {
        "backend": "postgresql",
        "postgresql": {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "openasp_catalog"),
            "user": os.getenv("POSTGRES_USER", "openasp"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "pool_size": 20,
            "max_overflow": 10
        },
        "cache": {
            "enabled": True,
            "type": "memory",
            "max_size": 1000,
            "default_ttl": 300
        }
    },
    "hybrid": {
        "mode": "hybrid",
        "read_backend": "json_file",
        "write_backends": ["json_file", "postgresql"],
        "failover_enabled": True
    }
}


class CatalogBackendConfig:
    """Manages catalog backend configuration and provides factory methods."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize backend configuration.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or BACKEND_CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"Loaded catalog backend config: {config.get('active_backend', 'json_file')}")
                    return config
            except Exception as e:
                logger.warning(f"Error loading config file {self.config_file}: {e}")
        
        # Return default configuration
        default_config = {
            "active_backend": "json_file",
            "migration_mode": False,
            "failover_enabled": True,
            "backends": DEFAULT_CONFIGS
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved catalog backend config to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_active_backend_config(self) -> Dict[str, Any]:
        """Get configuration for the currently active backend."""
        active_backend = self.config.get("active_backend", "json_file")
        backend_config = self.config.get("backends", {}).get(active_backend)
        
        if not backend_config:
            logger.warning(f"No config found for backend {active_backend}, using json_file")
            return DEFAULT_CONFIGS["json_file"]
        
        return backend_config
    
    def get_backend_config(self, backend_name: str) -> Dict[str, Any]:
        """Get configuration for a specific backend."""
        return self.config.get("backends", {}).get(backend_name, DEFAULT_CONFIGS.get(backend_name, {}))
    
    def set_active_backend(self, backend_name: str) -> bool:
        """
        Switch to a different backend.
        
        Args:
            backend_name: Name of backend to activate
            
        Returns:
            True if successful
        """
        if backend_name not in DEFAULT_CONFIGS:
            logger.error(f"Unknown backend: {backend_name}")
            return False
        
        self.config["active_backend"] = backend_name
        return self._save_config(self.config)
    
    def enable_migration_mode(self, read_backend: str = "json_file", 
                            write_backends: Optional[list] = None) -> bool:
        """
        Enable migration mode for dual-write operations.
        
        Args:
            read_backend: Backend to read from during migration
            write_backends: List of backends to write to (defaults to current + postgresql)
            
        Returns:
            True if successful
        """
        if write_backends is None:
            current_backend = self.config.get("active_backend", "json_file")
            write_backends = [current_backend, "postgresql"] if current_backend != "postgresql" else ["postgresql"]
        
        self.config["migration_mode"] = True
        self.config["migration_config"] = {
            "read_backend": read_backend,
            "write_backends": write_backends,
            "started_at": datetime.now().isoformat()
        }
        
        return self._save_config(self.config)
    
    def disable_migration_mode(self) -> bool:
        """Disable migration mode."""
        self.config["migration_mode"] = False
        if "migration_config" in self.config:
            del self.config["migration_config"]
        
        return self._save_config(self.config)
    
    def is_migration_mode(self) -> bool:
        """Check if migration mode is active."""
        return self.config.get("migration_mode", False)
    
    def get_migration_config(self) -> Optional[Dict[str, Any]]:
        """Get migration configuration if active."""
        return self.config.get("migration_config") if self.is_migration_mode() else None
    
    def validate_backend_connection(self, backend_name: str) -> Dict[str, Any]:
        """
        Test connection to a specific backend.
        
        Args:
            backend_name: Name of backend to test
            
        Returns:
            Health check results
        """
        try:
            from dbio.core import DBIOManager
            
            backend_config = self.get_backend_config(backend_name)
            if not backend_config:
                return {
                    "status": "error",
                    "error": f"No configuration found for backend: {backend_name}"
                }
            
            # Test backend connection
            manager = DBIOManager(backend_config)
            health = manager.health_check()
            manager.close()
            
            return health
            
        except Exception as e:
            return {
                "status": "error",
                "backend": backend_name,
                "error": str(e)
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and statistics."""
        status = {
            "migration_mode": self.is_migration_mode(),
            "active_backend": self.config.get("active_backend"),
            "available_backends": list(DEFAULT_CONFIGS.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.is_migration_mode():
            status["migration_config"] = self.get_migration_config()
        
        # Test backend connectivity
        backend_health = {}
        for backend_name in ["json_file", "postgresql"]:
            backend_health[backend_name] = self.validate_backend_connection(backend_name)
        
        status["backend_health"] = backend_health
        
        return status


# Global configuration instance
_config_instance: Optional[CatalogBackendConfig] = None


def get_catalog_backend_config() -> CatalogBackendConfig:
    """Get global catalog backend configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = CatalogBackendConfig()
    return _config_instance


def get_active_dbio_manager():
    """
    Factory function to get the appropriate DBIO manager based on current configuration.
    
    Returns:
        DBIOManager instance configured for the active backend
    """
    try:
        from dbio.core import DBIOManager
        
        config = get_catalog_backend_config()
        backend_config = config.get_active_backend_config()
        
        return DBIOManager(backend_config)
        
    except Exception as e:
        logger.error(f"Error creating DBIO manager: {e}")
        # Fallback to JSON file backend
        return DBIOManager(DEFAULT_CONFIGS["json_file"])


def create_hybrid_manager():
    """
    Create a hybrid manager for migration periods.
    
    Returns:
        HybridBackend instance for dual-write operations
    """
    try:
        from dbio.migration import HybridBackend
        from dbio.core import DBIOManager
        
        config = get_catalog_backend_config()
        migration_config = config.get_migration_config()
        
        if not migration_config:
            raise ValueError("Migration mode not enabled")
        
        # Create read backend
        read_backend_name = migration_config["read_backend"]
        read_config = config.get_backend_config(read_backend_name)
        read_manager = DBIOManager(read_config)
        
        # Create write backends
        write_managers = []
        for backend_name in migration_config["write_backends"]:
            write_config = config.get_backend_config(backend_name)
            write_manager = DBIOManager(write_config)
            write_managers.append(write_manager)
        
        return HybridBackend(read_manager, write_managers)
        
    except Exception as e:
        logger.error(f"Error creating hybrid manager: {e}")
        raise


# Convenience functions for common operations
def switch_to_postgresql() -> bool:
    """Switch to PostgreSQL backend."""
    config = get_catalog_backend_config()
    return config.set_active_backend("postgresql")


def switch_to_json() -> bool:
    """Switch to JSON file backend."""
    config = get_catalog_backend_config()
    return config.set_active_backend("json_file")


def enable_dual_write_migration() -> bool:
    """Enable dual-write migration mode (JSON -> PostgreSQL)."""
    config = get_catalog_backend_config()
    return config.enable_migration_mode("json_file", ["json_file", "postgresql"])


def disable_migration() -> bool:
    """Disable migration mode."""
    config = get_catalog_backend_config()
    return config.disable_migration_mode()


def get_migration_status() -> Dict[str, Any]:
    """Get current migration status."""
    config = get_catalog_backend_config()
    return config.get_migration_status()