"""
Template Manager Module

This module provides the TemplateManager class for managing brands and their
associated templates in the vision inspection system.
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TemplateManager:
   
    VALID_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp']
    
    def __init__(self, config_manager) -> None:
        self.config_manager = config_manager
        logger.info("TemplateManager initialized")
    
    def add_brand(self, name: str, template_path: str, roi: Dict[str, int],
                  threshold: float, method: str = 'hybrid') -> str:
        try:
            # Validate brand name
            if self.brand_exists(name):
                raise ValueError(f"Brand '{name}' already exists")
            
            # Validate template file
            template_file = Path(template_path)
            if not template_file.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")
            
            if template_file.suffix.lower() not in self.VALID_IMAGE_FORMATS:
                raise ValueError(
                    f"Invalid image format. Supported: {self.VALID_IMAGE_FORMATS}"
                )
            
            # Validate ROI
            self._validate_roi(roi)
            
            # Validate threshold
            if not (0.5 <= threshold <= 1.0):
                raise ValueError(f"Threshold must be between 0.5 and 1.0, got {threshold}")
            
            # Validate method
            valid_methods = ['template_matching', 'feature_matching', 'hybrid', 'adaptive']
            if method not in valid_methods:
                raise ValueError(f"Invalid method. Must be one of: {valid_methods}")
            
            # Generate brand ID
            brand_id = self._generate_brand_id()
            
            # Create brand folder
            brand_folder = self._create_brand_folder(name)
            
            # Copy template image
            copied_template_path = self._copy_template_image(template_path, name)
            
            # Create brand data structure
            brand_data = {
                "id": brand_id,
                "name": name,
                "templates": [
                    {
                        "path": str(copied_template_path),
                        "roi": roi,
                        "threshold": threshold
                    }
                ],
                "method": method,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add brand to configuration
            config = self.config_manager.get_config()
            config['brands'].append(brand_data)
            self.config_manager.save_config(config)
            
            logger.info(f"Brand '{name}' added successfully with ID: {brand_id}")
            return brand_id
            
        except Exception as e:
            logger.error(f"Error adding brand '{name}': {e}")
            raise
    
    def delete_brand(self, brand_id: str) -> bool:
        try:
            # Validate UUID format
            self._validate_uuid(brand_id)
            
            # Get brand data
            brand = self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"Brand with ID '{brand_id}' not found")
            
            brand_name = brand['name']
            
            # Remove brand folder and templates
            brand_folder = Path('templates') / brand_name.lower().replace(' ', '_')
            if brand_folder.exists():
                shutil.rmtree(brand_folder)
                logger.info(f"Deleted folder: {brand_folder}")
            
            # Remove from configuration
            config = self.config_manager.get_config()
            config['brands'] = [b for b in config['brands'] if b['id'] != brand_id]
            self.config_manager.save_config(config)
            
            logger.info(f"Brand '{brand_name}' (ID: {brand_id}) deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting brand {brand_id}: {e}")
            return False
    
    def update_brand(self, brand_id: str, **kwargs) -> bool:
        try:
            # Validate UUID format
            self._validate_uuid(brand_id)
            
            # Get current configuration
            config = self.config_manager.get_config()
            brand_found = False
            
            for brand in config['brands']:
                if brand['id'] == brand_id:
                    brand_found = True
                    
                    # Update name
                    if 'name' in kwargs:
                        new_name = kwargs['name']
                        # Check if new name already exists (excluding current brand)
                        if any(b['name'] == new_name and b['id'] != brand_id 
                              for b in config['brands']):
                            raise ValueError(f"Brand name '{new_name}' already exists")
                        brand['name'] = new_name
                    
                    # Update threshold
                    if 'threshold' in kwargs:
                        threshold = kwargs['threshold']
                        if not (0.5 <= threshold <= 1.0):
                            raise ValueError(f"Threshold must be between 0.5 and 1.0")
                        # Update threshold for all templates
                        for template in brand['templates']:
                            template['threshold'] = threshold
                    
                    # Update method
                    if 'method' in kwargs:
                        method = kwargs['method']
                        valid_methods = ['template_matching', 'feature_matching', 
                                       'hybrid', 'adaptive']
                        if method not in valid_methods:
                            raise ValueError(f"Invalid method. Must be one of: {valid_methods}")
                        brand['method'] = method
                    
                    # Update timestamp
                    brand['updated_at'] = datetime.now().isoformat()
                    break
            
            if not brand_found:
                raise ValueError(f"Brand with ID '{brand_id}' not found")
            
            # Save updated configuration
            self.config_manager.save_config(config)
            logger.info(f"Brand {brand_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating brand {brand_id}: {e}")
            return False
    
    def get_brand(self, brand_id: str) -> Optional[Dict[str, Any]]:
        try:
            self._validate_uuid(brand_id)
            config = self.config_manager.get_config()
            
            for brand in config['brands']:
                if brand['id'] == brand_id:
                    return brand.copy()
            
            logger.warning(f"Brand with ID '{brand_id}' not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting brand {brand_id}: {e}")
            return None
    
    def get_brand_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            config = self.config_manager.get_config()
            
            for brand in config['brands']:
                if brand['name'] == name:
                    return brand.copy()
            
            logger.warning(f"Brand with name '{name}' not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting brand by name '{name}': {e}")
            return None
    
    def list_brands(self) -> List[Dict[str, Any]]:
        try:
            config = self.config_manager.get_config()
            return config.get('brands', []).copy()
            
        except Exception as e:
            logger.error(f"Error listing brands: {e}")
            return []
    
    def brand_exists(self, name: str) -> bool:
        return self.get_brand_by_name(name) is not None
    
    def add_template_to_brand(self, brand_id: str, template_path: str,
                            roi: Dict[str, int], threshold: float) -> bool:
        try:
            # Validate UUID
            self._validate_uuid(brand_id)
            
            # Validate template file
            template_file = Path(template_path)
            if not template_file.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")
            
            if template_file.suffix.lower() not in self.VALID_IMAGE_FORMATS:
                raise ValueError(f"Invalid image format. Supported: {self.VALID_IMAGE_FORMATS}")
            
            # Validate ROI and threshold
            self._validate_roi(roi)
            if not (0.5 <= threshold <= 1.0):
                raise ValueError(f"Threshold must be between 0.5 and 1.0")
            
            # Get brand
            config = self.config_manager.get_config()
            brand_found = False
            
            for brand in config['brands']:
                if brand['id'] == brand_id:
                    brand_found = True
                    brand_name = brand['name']
                    
                    # Copy template image
                    copied_path = self._copy_template_image(template_path, brand_name)
                    
                    # Add template to brand
                    new_template = {
                        "path": str(copied_path),
                        "roi": roi,
                        "threshold": threshold
                    }
                    brand['templates'].append(new_template)
                    brand['updated_at'] = datetime.now().isoformat()
                    break
            
            if not brand_found:
                raise ValueError(f"Brand with ID '{brand_id}' not found")
            
            # Save configuration
            self.config_manager.save_config(config)
            logger.info(f"Template added to brand {brand_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding template to brand {brand_id}: {e}")
            return False
    
    def remove_template_from_brand(self, brand_id: str, template_index: int) -> bool:
        try:
            # Validate UUID
            self._validate_uuid(brand_id)
            
            # Get configuration
            config = self.config_manager.get_config()
            brand_found = False
            
            for brand in config['brands']:
                if brand['id'] == brand_id:
                    brand_found = True
                    
                    # Validate template index
                    if template_index < 0 or template_index >= len(brand['templates']):
                        raise ValueError(
                            f"Template index {template_index} out of range. "
                            f"Brand has {len(brand['templates'])} templates."
                        )
                    
                    # Don't allow removing the last template
                    if len(brand['templates']) == 1:
                        raise ValueError("Cannot remove the last template from a brand")
                    
                    # Get template path and remove file
                    template_path = Path(brand['templates'][template_index]['path'])
                    if template_path.exists():
                        template_path.unlink()
                        logger.info(f"Deleted template file: {template_path}")
                    
                    # Remove from list
                    brand['templates'].pop(template_index)
                    brand['updated_at'] = datetime.now().isoformat()
                    break
            
            if not brand_found:
                raise ValueError(f"Brand with ID '{brand_id}' not found")
            
            # Save configuration
            self.config_manager.save_config(config)
            logger.info(f"Template {template_index} removed from brand {brand_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing template from brand {brand_id}: {e}")
            return False
    
    def get_brand_templates(self, brand_id: str) -> List[Dict[str, Any]]:
        try:
            brand = self.get_brand(brand_id)
            if brand:
                return brand.get('templates', []).copy()
            return []
            
        except Exception as e:
            logger.error(f"Error getting templates for brand {brand_id}: {e}")
            return []
    
    def _copy_template_image(self, source_path: str, brand_name: str) -> Path:
        try:
            source = Path(source_path)
            brand_folder = self._create_brand_folder(brand_name)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"template_{timestamp}{source.suffix}"
            destination = brand_folder / filename
            
            # Copy file
            shutil.copy2(source, destination)
            logger.info(f"Template copied: {source} -> {destination}")
            
            return destination
            
        except Exception as e:
            logger.error(f"Error copying template image: {e}")
            raise IOError(f"Failed to copy template: {e}")
    
    def _create_brand_folder(self, brand_name: str) -> Path:
        try:
            # Sanitize brand name for folder
            folder_name = brand_name.lower().replace(' ', '_')
            folder_path = Path('templates') / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            
            return folder_path
            
        except Exception as e:
            logger.error(f"Error creating brand folder: {e}")
            raise
    
    def _generate_brand_id(self) -> str:
        return str(uuid.uuid4())
    
    def _validate_roi(self, roi: Dict[str, int]) -> None:
        required_keys = ['x', 'y', 'width', 'height']
        
        # Check all keys present
        if not all(key in roi for key in required_keys):
            raise ValueError(f"ROI must contain keys: {required_keys}")
        
        # Check all values are positive
        for key, value in roi.items():
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"ROI {key} must be a positive integer, got {value}")
    
    def _validate_uuid(self, brand_id: str) -> None:
        try:
            uuid.UUID(brand_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {brand_id}")
