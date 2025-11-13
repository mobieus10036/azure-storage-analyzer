"""
Configuration management utilities.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "config.yaml"


class Config:
    """Configuration manager for the assessment toolkit."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to YAML configuration file. If None, uses default.
        """
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dictionary containing configuration data
        """
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config_data or {}
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            'scope': {
                'subscriptions': [],
                'resource_groups': [],
                'locations': [],
                'required_tags': {}
            },
            'stale_data': {
                'threshold_days': 90,
                'check_last_access': True,
                'sample_size': 10000,
                'max_container_size': 1000000
            },
            'cost_analysis': {
                'enabled': True,
                'pricing_region': 'eastus',
                'calculate_savings': True,
                'tier_recommendations': {
                    'cool_tier_days': 30,
                    'archive_tier_days': 180,
                    'min_size_gb': 1
                }
            },
            'security': {
                'check_public_access': True,
                'check_encryption': True,
                'check_network_rules': True,
                'check_auth_methods': True,
                'check_soft_delete': True,
                'check_versioning': True,
                'check_defender': True,
                'check_https_only': True,
                'minimum_tls_version': 'TLS1_2'
            },
            'output': {
                'directory': './reports',
                'formats': ['json', 'csv', 'markdown'],
                'include_details': True,
                'include_recommendations': True,
                'sanitize_output': False,
                'compress': False
            },
            'execution': {
                'quick_mode': False,
                'parallel': {
                    'enabled': True,
                    'max_workers': 5
                },
                'rate_limit': 10,
                'retries': {
                    'max_attempts': 3,
                    'backoff_factor': 2
                },
                'timeout': 30,
                'verbose': False
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'stale_data.threshold_days')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value
            value: Value to set
        """
        keys = key_path.split('.')
        data = self.data
        
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        
        data[keys[-1]] = value
    
    def save(self, output_file: Optional[str] = None) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            output_file: Output file path. If None, uses original config file.
        """
        output_path = output_file or self.config_file
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Saved configuration to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
            raise
