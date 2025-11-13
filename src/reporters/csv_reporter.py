"""
CSV reporter module.
Generates CSV format reports.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from ..utils.helpers import format_bytes, format_currency

logger = logging.getLogger(__name__)


class CSVReporter:
    """Generates CSV format reports."""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize the reporter.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_storage_accounts_csv(
        self,
        storage_accounts: List[Dict],
        filename: str = None
    ) -> str:
        """
        Generate CSV report for storage accounts.
        
        Args:
            storage_accounts: List of storage account assessment data
            filename: Optional custom filename
            
        Returns:
            Path to generated CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"storage_accounts_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Subscription ID',
                    'Resource Group',
                    'Storage Account Name',
                    'Location',
                    'SKU',
                    'Kind',
                    'Creation Time',
                    'Total Containers',
                    'Total File Shares',
                    'Total Blobs',
                    'Total Size (GB)',
                    'Stale Blobs',
                    'Stale Size (GB)',
                    'Public Access Allowed',
                    'HTTPS Only',
                    'Min TLS Version',
                    'Soft Delete Enabled',
                    'Versioning Enabled',
                    'Security Score',
                    'Security Findings',
                    'Estimated Monthly Cost',
                    'Potential Monthly Savings',
                    'Tags'
                ])
                
                # Data rows
                for account in storage_accounts:
                    storage_account = account.get('storage_account', {})
                    containers = account.get('containers', [])
                    file_shares = account.get('file_shares', [])
                    cost_analysis = account.get('cost_analysis', {})
                    security_analysis = account.get('security_analysis', {})
                    
                    total_blobs = sum(c.get('blob_count', 0) for c in containers)
                    total_size_gb = sum(c.get('total_size_bytes', 0) for c in containers) / (1024 ** 3)
                    total_size_gb += sum(s.get('usage_bytes', 0) for s in file_shares) / (1024 ** 3)
                    stale_blobs = sum(c.get('stale_blob_count', 0) for c in containers)
                    stale_size_gb = sum(c.get('stale_size_bytes', 0) for c in containers) / (1024 ** 3)
                    
                    blob_props = storage_account.get('blob_service_properties', {})
                    
                    writer.writerow([
                        storage_account.get('subscription_id', ''),
                        storage_account.get('resource_group', ''),
                        storage_account.get('name', ''),
                        storage_account.get('location', ''),
                        storage_account.get('sku', ''),
                        storage_account.get('kind', ''),
                        storage_account.get('creation_time', ''),
                        len(containers),
                        len(file_shares),
                        total_blobs,
                        f"{total_size_gb:.2f}",
                        stale_blobs,
                        f"{stale_size_gb:.2f}",
                        storage_account.get('allow_blob_public_access', ''),
                        storage_account.get('https_only', ''),
                        storage_account.get('min_tls_version', ''),
                        blob_props.get('delete_retention_policy', {}).get('enabled', False),
                        blob_props.get('is_versioning_enabled', False),
                        security_analysis.get('security_score', 0),
                        security_analysis.get('total_findings', 0),
                        f"{cost_analysis.get('total_monthly_cost', 0):.2f}",
                        f"{cost_analysis.get('total_monthly_savings', 0):.2f}",
                        '; '.join([f"{k}={v}" for k, v in storage_account.get('tags', {}).items()])
                    ])
            
            logger.info(f"CSV report generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate CSV report: {e}")
            raise
    
    def generate_findings_csv(
        self,
        all_findings: List[Dict],
        filename: str = None
    ) -> str:
        """
        Generate CSV report for all findings.
        
        Args:
            all_findings: List of all security/governance findings
            filename: Optional custom filename
            
        Returns:
            Path to generated CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"findings_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Storage Account',
                    'Type',
                    'Severity',
                    'Finding',
                    'Recommendation',
                    'Remediation'
                ])
                
                # Data rows
                for finding in all_findings:
                    writer.writerow([
                        finding.get('storage_account', ''),
                        finding.get('type', ''),
                        finding.get('severity', ''),
                        finding.get('finding', ''),
                        finding.get('recommendation', ''),
                        finding.get('remediation', '')
                    ])
            
            logger.info(f"Findings CSV generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate findings CSV: {e}")
            raise
    
    def generate_cost_optimization_csv(
        self,
        cost_recommendations: List[Dict],
        filename: str = None
    ) -> str:
        """
        Generate CSV report for cost optimization recommendations.
        
        Args:
            cost_recommendations: List of cost optimization recommendations
            filename: Optional custom filename
            
        Returns:
            Path to generated CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cost_optimization_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Storage Account',
                    'Container',
                    'Type',
                    'Current Tier',
                    'Recommended Tier',
                    'Affected Size (GB)',
                    'Affected Blob Count',
                    'Monthly Savings',
                    'Annual Savings',
                    'Reason'
                ])
                
                # Data rows
                for rec in cost_recommendations:
                    savings = rec.get('estimated_savings', {})
                    writer.writerow([
                        rec.get('storage_account', ''),
                        rec.get('container', ''),
                        rec.get('type', ''),
                        rec.get('current_tier', ''),
                        rec.get('recommended_tier', ''),
                        f"{rec.get('affected_size_bytes', 0) / (1024**3):.2f}",
                        rec.get('affected_blob_count', 0),
                        f"{savings.get('monthly_savings', 0):.2f}",
                        f"{savings.get('annual_savings', 0):.2f}",
                        rec.get('reason', '')
                    ])
            
            logger.info(f"Cost optimization CSV generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to generate cost optimization CSV: {e}")
            raise
