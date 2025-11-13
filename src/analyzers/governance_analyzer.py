"""
Governance analyzer module.
Checks compliance with governance policies and best practices.
"""

import logging
from typing import Dict, List
from ..utils.helpers import validate_naming_convention

logger = logging.getLogger(__name__)


class GovernanceAnalyzer:
    """Analyzes governance and compliance aspects."""
    
    def __init__(self):
        """Initialize the analyzer."""
        pass
    
    def analyze_tagging(
        self,
        storage_account: Dict,
        required_tags: List[str]
    ) -> List[Dict]:
        """
        Analyze resource tagging compliance.
        
        Args:
            storage_account: Storage account dictionary
            required_tags: List of required tag names
            
        Returns:
            List of governance findings
        """
        findings = []
        
        if not required_tags:
            return findings
        
        account_tags = storage_account.get('tags', {})
        
        # Check for missing required tags
        missing_tags = [tag for tag in required_tags if tag not in account_tags]
        
        if missing_tags:
            findings.append({
                'type': 'tagging',
                'severity': 'medium',
                'resource': storage_account['name'],
                'finding': f'Missing required tags: {", ".join(missing_tags)}',
                'recommendation': 'Add required tags for cost tracking and governance',
                'remediation': f'Add tags: {", ".join(missing_tags)}'
            })
        
        # Check for empty tag values
        empty_tags = [tag for tag, value in account_tags.items() if not value]
        if empty_tags:
            findings.append({
                'type': 'tagging',
                'severity': 'low',
                'resource': storage_account['name'],
                'finding': f'Tags with empty values: {", ".join(empty_tags)}',
                'recommendation': 'Populate tag values',
                'remediation': f'Set values for tags: {", ".join(empty_tags)}'
            })
        
        return findings
    
    def analyze_naming_convention(
        self,
        storage_account: Dict,
        naming_pattern: str
    ) -> List[Dict]:
        """
        Analyze naming convention compliance.
        
        Args:
            storage_account: Storage account dictionary
            naming_pattern: Regex pattern for naming convention
            
        Returns:
            List of governance findings
        """
        findings = []
        
        if not naming_pattern:
            return findings
        
        account_name = storage_account['name']
        
        if not validate_naming_convention(account_name, naming_pattern):
            findings.append({
                'type': 'naming_convention',
                'severity': 'low',
                'resource': account_name,
                'finding': f'Storage account name does not match naming convention pattern: {naming_pattern}',
                'recommendation': 'Follow organizational naming conventions for consistency',
                'remediation': f'Rename to match pattern (note: storage account names cannot be changed after creation)'
            })
        
        return findings
    
    def analyze_lifecycle_management(
        self,
        storage_account: Dict
    ) -> List[Dict]:
        """
        Analyze lifecycle management policies.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of governance findings
        """
        findings = []
        
        # This would require additional API call to get management policies
        # For now, we'll flag accounts that should consider lifecycle policies
        
        # If account has blob data, recommend lifecycle policies
        blob_props = storage_account.get('blob_service_properties', {})
        
        # Simple check: if no restore policy, might not have lifecycle management
        restore_policy = blob_props.get('restore_policy', {})
        if not restore_policy.get('enabled'):
            findings.append({
                'type': 'lifecycle_management',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'Lifecycle management policies not detected',
                'recommendation': 'Configure lifecycle management to automatically tier or delete old data',
                'remediation': 'Create lifecycle management policy to optimize costs'
            })
        
        return findings
    
    def analyze_diagnostics(
        self,
        storage_account: Dict
    ) -> List[Dict]:
        """
        Analyze diagnostic settings.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of governance findings
        """
        findings = []
        
        # Check if last access time tracking is enabled
        blob_props = storage_account.get('blob_service_properties', {})
        last_access_tracking = blob_props.get('last_access_time_tracking_policy', {})
        
        if not last_access_tracking.get('enabled', False):
            findings.append({
                'type': 'diagnostics',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'Last access time tracking is not enabled',
                'recommendation': 'Enable last access time tracking for better lifecycle management',
                'remediation': 'Enable last access time tracking in blob service properties'
            })
        
        return findings
    
    def analyze_redundancy(
        self,
        storage_account: Dict
    ) -> List[Dict]:
        """
        Analyze storage redundancy configuration.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of governance findings
        """
        findings = []
        
        sku = storage_account.get('sku', 'Unknown')
        
        # Check if using LRS in production (might need higher redundancy)
        if 'LRS' in sku:
            findings.append({
                'type': 'redundancy',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'Using Locally Redundant Storage (LRS)',
                'recommendation': 'Consider using ZRS or GRS for production workloads requiring higher availability',
                'remediation': 'Evaluate if Zone-Redundant Storage (ZRS) or Geo-Redundant Storage (GRS) is needed'
            })
        
        # Check secondary location for GRS/RAGRS
        if 'GRS' in sku or 'RAGRS' in sku:
            secondary_location = storage_account.get('secondary_location')
            if not secondary_location:
                findings.append({
                    'type': 'redundancy',
                    'severity': 'medium',
                    'resource': storage_account['name'],
                    'finding': 'Geo-redundant storage configured but secondary location not available',
                    'recommendation': 'Verify geo-redundancy configuration',
                    'remediation': 'Check storage account replication status'
                })
        
        return findings
    
    def analyze_orphaned_resources(
        self,
        storage_account: Dict,
        containers: List[Dict],
        metrics: Dict
    ) -> List[Dict]:
        """
        Identify potentially orphaned or unused resources.
        
        Args:
            storage_account: Storage account dictionary
            containers: List of container dictionaries
            metrics: Metrics data
            
        Returns:
            List of governance findings
        """
        findings = []
        
        # Check for empty storage account
        total_blobs = sum(c.get('blob_count', 0) for c in containers)
        
        if total_blobs == 0:
            findings.append({
                'type': 'orphaned_resource',
                'severity': 'low',
                'resource': storage_account['name'],
                'finding': 'Storage account contains no blobs',
                'recommendation': 'Consider deleting if no longer needed',
                'remediation': 'Verify if storage account is still required, delete if not'
            })
        
        # Check for no activity
        stats = metrics.get('statistics', {})
        has_activity = stats.get('has_activity', False)
        
        if not has_activity and total_blobs > 0:
            findings.append({
                'type': 'orphaned_resource',
                'severity': 'low',
                'resource': storage_account['name'],
                'finding': 'Storage account has no transaction activity in monitoring period',
                'recommendation': 'Verify if storage account is actively used',
                'remediation': 'Review usage and consider archiving or deleting if unused'
            })
        
        # Check for empty containers
        empty_containers = [c for c in containers if c.get('blob_count', 0) == 0]
        if empty_containers:
            findings.append({
                'type': 'orphaned_resource',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': f'{len(empty_containers)} empty container(s) found',
                'recommendation': 'Clean up empty containers',
                'remediation': f'Delete empty containers: {", ".join([c["name"] for c in empty_containers[:5]])}'
            })
        
        return findings
    
    def analyze_governance(
        self,
        storage_account: Dict,
        containers: List[Dict],
        metrics: Dict,
        config: Dict
    ) -> Dict:
        """
        Comprehensive governance analysis.
        
        Args:
            storage_account: Storage account dictionary
            config: Configuration dictionary
            containers: List of container dictionaries
            metrics: Metrics data
            
        Returns:
            Dictionary with governance analysis results
        """
        governance_config = config.get('governance', {})
        all_findings = []
        
        # Tagging analysis
        required_tags = governance_config.get('required_tags', [])
        all_findings.extend(self.analyze_tagging(storage_account, required_tags))
        
        # Naming convention analysis
        naming_pattern = governance_config.get('naming_pattern')
        all_findings.extend(self.analyze_naming_convention(storage_account, naming_pattern))
        
        # Lifecycle management
        if governance_config.get('check_lifecycle_policies', True):
            all_findings.extend(self.analyze_lifecycle_management(storage_account))
        
        # Diagnostics
        if governance_config.get('check_diagnostics', True):
            all_findings.extend(self.analyze_diagnostics(storage_account))
        
        # Redundancy
        all_findings.extend(self.analyze_redundancy(storage_account))
        
        # Orphaned resources
        all_findings.extend(self.analyze_orphaned_resources(storage_account, containers, metrics))
        
        # Categorize by severity
        findings_by_severity = {
            'critical': [f for f in all_findings if f.get('severity') == 'critical'],
            'high': [f for f in all_findings if f.get('severity') == 'high'],
            'medium': [f for f in all_findings if f.get('severity') == 'medium'],
            'low': [f for f in all_findings if f.get('severity') == 'low'],
            'info': [f for f in all_findings if f.get('severity') == 'info']
        }
        
        return {
            'storage_account': storage_account['name'],
            'total_findings': len(all_findings),
            'findings_by_severity': findings_by_severity,
            'all_findings': all_findings
        }
