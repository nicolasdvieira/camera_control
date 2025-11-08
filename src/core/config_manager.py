"""
Configuration Manager Module

This module provides the ConfigManager class for handling system configuration
stored in JSON format. It manages camera settings, paths, and brand data with
automatic backup and validation.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigManager:
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "camera": {
            "index": 0,
            "resolution": {
                "width": 1280,
                "height": 720
            },
            "fps": 30
        },
        "default_threshold": 0.85,
        "default_method": "hybrid",
        "paths": {
            "templates": "templates/",
            "logs": "logs/",
            "reports": "reports/"
        },
        "brands": []
    }
    
    def __init__(self, config_path: str = 'config.json') -> None:
        self.config_path = Path(config_path)
        self.config_data: Dict[str, Any] = {}
        self.load_config()
        logger.info(f"ConfigManager initialized with path: {self.config_path}")
    
    def load_config(self) -> Dict[str, Any]:
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found at {self.config_path}. Creating default.")
                self.create_default_config()
                return self.config_data
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            
            # Validate loaded configuration
            if not self.validate_config():
                logger.warning("Configuration validation failed. Creating backup and using default.")
                self._create_backup()
                self.create_default_config()
            
            return self.config_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Creating backup of corrupted file and using default config")
            self._create_backup()
            self.create_default_config()
            return self.config_data
        
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        try:
            # Create backup before saving
            if self.config_path.exists():
                self._create_backup()
            
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, indent=2, ensure_ascii=False)
            
            self.config_data = config_data
            logger.info(f"Configuration saved successfully to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        return self.config_data.copy()
    
    def update_config(self, key: str, value: Any) -> bool:
        try:
            self.config_data[key] = value
            success = self.save_config(self.config_data)
            
            if success:
                logger.info(f"Updated config key '{key}' with value: {value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating config key '{key}': {e}")
            return False
    
    def validate_config(self) -> bool:
        try:
            # Check required top-level keys
            required_keys = ['version', 'camera', 'default_threshold', 
                           'default_method', 'paths', 'brands']
            
            for key in required_keys:
                if key not in self.config_data:
                    logger.error(f"Missing required key: {key}")
                    return False
            
            # Validate camera settings
            camera = self.config_data.get('camera', {})
            if not all(k in camera for k in ['index', 'resolution', 'fps']):
                logger.error("Invalid camera configuration structure")
                return False
            
            resolution = camera.get('resolution', {})
            if not all(k in resolution for k in ['width', 'height']):
                logger.error("Invalid resolution configuration")
                return False
            
            # Validate threshold
            threshold = self.config_data.get('default_threshold', 0)
            if not (0.5 <= threshold <= 1.0):
                logger.error(f"Invalid threshold value: {threshold}")
                return False
            
            # Validate paths
            paths = self.config_data.get('paths', {})
            if not all(k in paths for k in ['templates', 'logs', 'reports']):
                logger.error("Invalid paths configuration")
                return False
            
            # Validate brands is a list
            if not isinstance(self.config_data.get('brands', []), list):
                logger.error("Brands must be a list")
                return False
            
            logger.info("Configuration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False
    
    def get_camera_settings(self) -> Dict[str, Any]:
        return self.config_data.get('camera', {}).copy()
    
    def update_camera_settings(self, settings_dict: Dict[str, Any]) -> bool:
        try:
            current_camera = self.config_data.get('camera', {})
            
            # Update camera settings
            for key, value in settings_dict.items():
                if key == 'resolution' and isinstance(value, dict):
                    if 'resolution' not in current_camera:
                        current_camera['resolution'] = {}
                    current_camera['resolution'].update(value)
                else:
                    current_camera[key] = value
            
            self.config_data['camera'] = current_camera
            success = self.save_config(self.config_data)
            
            if success:
                logger.info(f"Camera settings updated: {settings_dict}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating camera settings: {e}")
            return False
    
    def create_default_config(self) -> Dict[str, Any]:
        try:
            self.config_data = self.DEFAULT_CONFIG.copy()
            
            # Create required directories
            for path_key, path_value in self.config_data['paths'].items():
                Path(path_value).mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path_value}")
            
            # Save default configuration
            self.save_config(self.config_data)
            logger.info("Default configuration created successfully")
            
            return self.config_data
            
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
            raise
    
    def _create_backup(self) -> None:
        try:
            if self.config_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.config_path.with_suffix(f'.json.bak.{timestamp}')
                shutil.copy2(self.config_path, backup_path)
                logger.info(f"Backup created: {backup_path}")
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
