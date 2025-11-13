"""
JSON reporter module.
Generates JSON format reports.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONReporter:
    """Generates JSON format reports."""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize the reporter.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, assessment_data: Dict[str, Any], filename: str = None) -> str:
        """
        Generate JSON report.
        
        Args:
            assessment_data: Complete assessment data
            filename: Optional custom filename
            
        Returns:
            Path to generated report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"storage_assessment_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(assessment_data, f, indent=2, default=str)
            
            logger.info(f"JSON report generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise
