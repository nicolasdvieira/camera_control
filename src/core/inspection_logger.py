"""
Inspection Logger Module

This module provides the InspectionLogger class for logging and managing
inspection results with support for filtering, statistics, and export.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class InspectionLogger:
    """
    Manages logging of inspection results.
    
    This class handles recording inspection events, filtering logs, generating
    statistics, and exporting data to various formats.
    
    Attributes:
        log_file: Path to the log file
        max_log_size: Maximum log file size before rotation (in bytes)
    """
    
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
    
    def __init__(self, log_file: str = 'logs/inspections.log') -> None:
        self.log_file = Path(log_file)
        self.max_log_size = self.MAX_LOG_SIZE
        
        # Create logs directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.touch()
        
        logger.info(f"InspectionLogger initialized with log file: {self.log_file}")
    
    def log_inspection(self, brand_name: str, result: str, score: float,
                      method: str, confidence: str = 'MEDIUM',
                      details: Optional[Dict[str, Any]] = None) -> bool:
        try:
            # Validate parameters
            if result not in ['OK', 'NOK']:
                raise ValueError(f"Result must be 'OK' or 'NOK', got '{result}'")
            
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Score must be between 0.0 and 1.0, got {score}")
            
            valid_methods = ['template_matching', 'feature_matching', 'hybrid', 'adaptive']
            if method not in valid_methods:
                raise ValueError(f"Invalid method. Must be one of: {valid_methods}")
            
            valid_confidence = ['LOW', 'MEDIUM', 'HIGH']
            if confidence not in valid_confidence:
                raise ValueError(f"Invalid confidence. Must be one of: {valid_confidence}")
            
            # Check if log rotation is needed
            self._check_log_rotation()
            
            # Create log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'brand': brand_name,
                'result': result,
                'score': round(score, 4),
                'method': method,
                'confidence': confidence
            }
            
            # Add optional details
            if details:
                log_entry['details'] = details
            
            # Write to log file (JSON Lines format - one JSON per line)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')
            
            logger.debug(f"Logged inspection: {brand_name} - {result} ({score})")
            return True
            
        except Exception as e:
            logger.error(f"Error logging inspection: {e}")
            return False
    
    def get_logs(self, start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None,
                result_filter: Optional[str] = None,
                brand_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            logs = self.get_all_logs()
            filtered_logs = []
            
            for log_entry in logs:
                # Apply date filters
                if start_date:
                    entry_date = datetime.fromisoformat(log_entry['timestamp'])
                    if entry_date < start_date:
                        continue
                
                if end_date:
                    entry_date = datetime.fromisoformat(log_entry['timestamp'])
                    if entry_date > end_date:
                        continue
                
                # Apply result filter
                if result_filter and log_entry.get('result') != result_filter:
                    continue
                
                # Apply brand filter
                if brand_filter and log_entry.get('brand') != brand_filter:
                    continue
                
                filtered_logs.append(log_entry)
            
            logger.debug(f"Retrieved {len(filtered_logs)} filtered logs")
            return filtered_logs
            
        except Exception as e:
            logger.error(f"Error getting filtered logs: {e}")
            return []
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        try:
            logs = []
            
            if not self.log_file.exists():
                return logs
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping malformed log line: {line[:50]}...")
            
            logger.debug(f"Retrieved {len(logs)} total logs")
            return logs
            
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
    
    def clear_logs(self, confirm: bool = False) -> bool:
        try:
            if not confirm:
                logger.warning("clear_logs() called without confirmation")
                return False
            
            # Create backup before clearing
            if self.log_file.exists() and self.log_file.stat().st_size > 0:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.log_file.with_suffix(f'.log.backup.{timestamp}')
                self.log_file.rename(backup_path)
                logger.info(f"Backup created: {backup_path}")
            
            # Create new empty log file
            self.log_file.touch()
            logger.info("Logs cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
            return False
    
    def export_logs_to_csv(self, filepath: str) -> bool:
        try:
            logs = self.get_all_logs()
            
            if not logs:
                logger.warning("No logs to export")
                return False
            
            output_path = Path(filepath)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get all unique keys from logs (for CSV columns)
            all_keys = set()
            for log in logs:
                all_keys.update(log.keys())
                # Flatten details if present
                if 'details' in log and isinstance(log['details'], dict):
                    all_keys.update(f"details_{k}" for k in log['details'].keys())
            
            # Remove 'details' from keys as we'll flatten it
            all_keys.discard('details')
            fieldnames = sorted(all_keys)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for log in logs:
                    row = {}
                    for key, value in log.items():
                        if key == 'details' and isinstance(value, dict):
                            # Flatten details
                            for detail_key, detail_value in value.items():
                                row[f'details_{detail_key}'] = detail_value
                        else:
                            row[key] = value
                    writer.writerow(row)
            
            logger.info(f"Exported {len(logs)} logs to CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting logs to CSV: {e}")
            return False
    
    def export_logs_to_json(self, filepath: str) -> bool:
        try:
            logs = self.get_all_logs()
            
            if not logs:
                logger.warning("No logs to export")
                return False
            
            output_path = Path(filepath)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(logs)} logs to JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting logs to JSON: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics from inspection logs.
        
        Returns:
            Dictionary containing statistics:
                - total: Total number of inspections
                - ok_count: Number of OK results
                - nok_count: Number of NOK results
                - ok_percentage: Percentage of OK results
                - nok_percentage: Percentage of NOK results
                - average_score: Average inspection score
                - average_ok_score: Average score for OK results
                - average_nok_score: Average score for NOK results
                - methods_used: Dictionary with count per method
                - brands_inspected: Dictionary with count per brand
        
        Example:
            >>> stats = logger.get_statistics()
            >>> print(f"Success rate: {stats['ok_percentage']:.2f}%")
        """
        try:
            logs = self.get_all_logs()
            
            if not logs:
                return {
                    'total': 0,
                    'ok_count': 0,
                    'nok_count': 0,
                    'ok_percentage': 0.0,
                    'nok_percentage': 0.0,
                    'average_score': 0.0,
                    'average_ok_score': 0.0,
                    'average_nok_score': 0.0,
                    'methods_used': {},
                    'brands_inspected': {}
                }
            
            total = len(logs)
            ok_logs = [log for log in logs if log.get('result') == 'OK']
            nok_logs = [log for log in logs if log.get('result') == 'NOK']
            
            ok_count = len(ok_logs)
            nok_count = len(nok_logs)
            
            # Calculate percentages
            ok_percentage = (ok_count / total * 100) if total > 0 else 0
            nok_percentage = (nok_count / total * 100) if total > 0 else 0
            
            # Calculate average scores
            all_scores = [log.get('score', 0) for log in logs]
            average_score = sum(all_scores) / total if total > 0 else 0
            
            ok_scores = [log.get('score', 0) for log in ok_logs]
            average_ok_score = sum(ok_scores) / ok_count if ok_count > 0 else 0
            
            nok_scores = [log.get('score', 0) for log in nok_logs]
            average_nok_score = sum(nok_scores) / nok_count if nok_count > 0 else 0
            
            # Count methods used
            methods_used: Dict[str, int] = {}
            for log in logs:
                method = log.get('method', 'unknown')
                methods_used[method] = methods_used.get(method, 0) + 1
            
            # Count brands inspected
            brands_inspected: Dict[str, int] = {}
            for log in logs:
                brand = log.get('brand', 'unknown')
                brands_inspected[brand] = brands_inspected.get(brand, 0) + 1
            
            stats = {
                'total': total,
                'ok_count': ok_count,
                'nok_count': nok_count,
                'ok_percentage': round(ok_percentage, 2),
                'nok_percentage': round(nok_percentage, 2),
                'average_score': round(average_score, 4),
                'average_ok_score': round(average_ok_score, 4),
                'average_nok_score': round(average_nok_score, 4),
                'methods_used': methods_used,
                'brands_inspected': brands_inspected
            }
            
            logger.debug(f"Calculated statistics for {total} logs")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def get_logs_by_brand(self, brand_name: str) -> List[Dict[str, Any]]:
        return self.get_logs(brand_filter=brand_name)
    
    def _format_log_entry(self, entry: Dict[str, Any]) -> str:
        try:
            timestamp = entry.get('timestamp', 'N/A')
            brand = entry.get('brand', 'N/A')
            result = entry.get('result', 'N/A')
            score = entry.get('score', 0)
            method = entry.get('method', 'N/A')
            confidence = entry.get('confidence', 'N/A')
            
            formatted = (
                f"[{timestamp}] {brand}: {result} "
                f"(score: {score:.2f}, method: {method}, confidence: {confidence})"
            )
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting log entry: {e}")
            return str(entry)
    
    def _check_log_rotation(self) -> None:
        try:
            if not self.log_file.exists():
                return
            
            file_size = self.log_file.stat().st_size
            
            if file_size >= self.max_log_size:
                # Rotate log file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                rotated_path = self.log_file.with_suffix(f'.log.{timestamp}')
                self.log_file.rename(rotated_path)
                
                # Create new log file
                self.log_file.touch()
                
                logger.info(f"Log rotated: {rotated_path} (size: {file_size} bytes)")
                
        except Exception as e:
            logger.error(f"Error during log rotation: {e}")
