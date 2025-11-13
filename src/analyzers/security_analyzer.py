"""
Security analyzer module.
Analyzes security configurations and identifies risks.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """Analyzes storage account security configurations."""
    
    def __init__(self):
        """Initialize the analyzer."""
        pass
    
    def analyze_public_access(self, storage_account: Dict) -> List[Dict]:
        """
        Analyze public access configuration.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of security findings
        """
        findings = []
        
        # Check if public blob access is allowed at account level
        allow_public_access = storage_account.get('allow_blob_public_access')
        
        if allow_public_access is True:
            findings.append({
                'type': 'public_access',
                'severity': 'high',
                'resource': storage_account['name'],
                'finding': 'Public blob access is enabled at storage account level',
                'recommendation': 'Disable public blob access unless specifically required',
                'remediation': 'Set allowBlobPublicAccess to false'
            })
        
        return findings
    
    def analyze_encryption(self, storage_account: Dict) -> List[Dict]:
        """
        Analyze encryption configuration.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of security findings
        """
        findings = []
        
        # Check HTTPS-only
        https_only = storage_account.get('https_only')
        if not https_only:
            findings.append({
                'type': 'encryption_in_transit',
                'severity': 'high',
                'resource': storage_account['name'],
                'finding': 'HTTPS-only traffic is not enforced',
                'recommendation': 'Enable HTTPS-only traffic to protect data in transit',
                'remediation': 'Set supportsHttpsTrafficOnly to true'
            })
        
        # Check TLS version
        min_tls = storage_account.get('min_tls_version')
        if min_tls and min_tls not in ['TLS1_2', 'TLS1_3']:
            findings.append({
                'type': 'tls_version',
                'severity': 'medium',
                'resource': storage_account['name'],
                'finding': f'Minimum TLS version is {min_tls}, should be TLS 1.2 or higher',
                'recommendation': 'Set minimum TLS version to TLS 1.2',
                'remediation': 'Set minimumTlsVersion to TLS1_2'
            })
        
        # Check encryption at rest
        encryption_services = storage_account.get('encryption_services', {})
        
        for service in ['blob', 'file', 'queue', 'table']:
            service_encryption = encryption_services.get(service, {})
            if not service_encryption.get('enabled', False):
                findings.append({
                    'type': 'encryption_at_rest',
                    'severity': 'high',
                    'resource': storage_account['name'],
                    'finding': f'{service.capitalize()} service encryption is not enabled',
                    'recommendation': f'Enable encryption for {service} service',
                    'remediation': f'Enable encryption.services.{service}.enabled'
                })
        
        # Check if using customer-managed keys
        key_source = storage_account.get('encryption_key_source')
        if key_source == 'Microsoft.Storage':
            findings.append({
                'type': 'encryption_key_management',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'Using Microsoft-managed encryption keys',
                'recommendation': 'Consider using customer-managed keys for enhanced control',
                'remediation': 'Configure customer-managed keys in Azure Key Vault'
            })
        
        return findings
    
    def analyze_network_access(self, storage_account: Dict) -> List[Dict]:
        """
        Analyze network access configuration.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of security findings
        """
        findings = []
        
        network_rules = storage_account.get('network_rule_set', {})
        default_action = network_rules.get('default_action')
        
        # Check if network access is unrestricted
        if default_action == 'Allow':
            findings.append({
                'type': 'network_access',
                'severity': 'high',
                'resource': storage_account['name'],
                'finding': 'Storage account allows access from all networks',
                'recommendation': 'Restrict network access to specific virtual networks or IP ranges',
                'remediation': 'Configure firewall rules and set default action to Deny'
            })
        
        # Check for IP rules
        ip_rules = network_rules.get('ip_rules', [])
        if ip_rules:
            # Check for overly permissive rules
            for rule in ip_rules:
                ip_range = rule.get('value', '')
                # Check for 0.0.0.0 or very broad ranges
                if ip_range.startswith('0.0.0.0') or ip_range == '*':
                    findings.append({
                        'type': 'network_access',
                        'severity': 'high',
                        'resource': storage_account['name'],
                        'finding': f'Overly permissive IP rule: {ip_range}',
                        'recommendation': 'Remove overly broad IP rules',
                        'remediation': 'Specify exact IP addresses or narrow CIDR ranges'
                    })
        
        # Check for virtual network rules
        vnet_rules = network_rules.get('virtual_network_rules', [])
        if not vnet_rules and default_action == 'Deny':
            findings.append({
                'type': 'network_access',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'No virtual network rules configured',
                'recommendation': 'Consider using virtual network service endpoints for secure access',
                'remediation': 'Configure virtual network rules or private endpoints'
            })
        
        return findings
    
    def analyze_authentication(self, storage_account: Dict) -> List[Dict]:
        """
        Analyze authentication configuration.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of security findings
        """
        findings = []
        
        # Check if shared key access is allowed
        allow_shared_key = storage_account.get('allow_shared_key_access')
        if allow_shared_key is not False:
            findings.append({
                'type': 'authentication',
                'severity': 'medium',
                'resource': storage_account['name'],
                'finding': 'Shared key (access key) authentication is enabled',
                'recommendation': 'Consider disabling shared key access and use Azure AD authentication only',
                'remediation': 'Set allowSharedKeyAccess to false (after ensuring apps use Azure AD)'
            })
        
        # Check if OAuth is default
        default_to_oauth = storage_account.get('default_to_oauth_authentication')
        if not default_to_oauth:
            findings.append({
                'type': 'authentication',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'Azure AD authentication is not set as default',
                'recommendation': 'Enable Azure AD as the default authentication method',
                'remediation': 'Set defaultToOAuthAuthentication to true'
            })
        
        return findings
    
    def analyze_data_protection(self, storage_account: Dict) -> List[Dict]:
        """
        Analyze data protection features.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            List of security findings
        """
        findings = []
        
        blob_props = storage_account.get('blob_service_properties', {})
        
        # Check soft delete
        delete_retention = blob_props.get('delete_retention_policy', {})
        if not delete_retention.get('enabled', False):
            findings.append({
                'type': 'data_protection',
                'severity': 'medium',
                'resource': storage_account['name'],
                'finding': 'Soft delete for blobs is not enabled',
                'recommendation': 'Enable soft delete to protect against accidental deletion',
                'remediation': 'Enable soft delete with appropriate retention period (7-365 days)'
            })
        
        # Check container soft delete
        container_delete_retention = blob_props.get('container_delete_retention_policy', {})
        if not container_delete_retention.get('enabled', False):
            findings.append({
                'type': 'data_protection',
                'severity': 'medium',
                'resource': storage_account['name'],
                'finding': 'Soft delete for containers is not enabled',
                'recommendation': 'Enable container soft delete',
                'remediation': 'Enable container soft delete with retention period'
            })
        
        # Check versioning
        is_versioning_enabled = blob_props.get('is_versioning_enabled', False)
        if not is_versioning_enabled:
            findings.append({
                'type': 'data_protection',
                'severity': 'low',
                'resource': storage_account['name'],
                'finding': 'Blob versioning is not enabled',
                'recommendation': 'Consider enabling versioning for better data protection',
                'remediation': 'Enable blob versioning'
            })
        
        # Check change feed
        change_feed = blob_props.get('change_feed', {})
        if not change_feed.get('enabled', False):
            findings.append({
                'type': 'data_protection',
                'severity': 'info',
                'resource': storage_account['name'],
                'finding': 'Change feed is not enabled',
                'recommendation': 'Enable change feed for audit and tracking capabilities',
                'remediation': 'Enable change feed logging'
            })
        
        return findings
    
    def analyze_storage_account_security(
        self,
        storage_account: Dict,
        config: Dict
    ) -> Dict:
        """
        Comprehensive security analysis for a storage account.
        
        Args:
            storage_account: Storage account dictionary
            config: Configuration dictionary
            
        Returns:
            Dictionary with security analysis results
        """
        security_config = config.get('security', {})
        all_findings = []
        
        # Run security checks based on configuration
        if security_config.get('check_public_access', True):
            all_findings.extend(self.analyze_public_access(storage_account))
        
        if security_config.get('check_encryption', True):
            all_findings.extend(self.analyze_encryption(storage_account))
        
        if security_config.get('check_network_rules', True):
            all_findings.extend(self.analyze_network_access(storage_account))
        
        if security_config.get('check_auth_methods', True):
            all_findings.extend(self.analyze_authentication(storage_account))
        
        if security_config.get('check_soft_delete', True) or security_config.get('check_versioning', True):
            all_findings.extend(self.analyze_data_protection(storage_account))
        
        # Categorize by severity
        findings_by_severity = {
            'critical': [f for f in all_findings if f.get('severity') == 'critical'],
            'high': [f for f in all_findings if f.get('severity') == 'high'],
            'medium': [f for f in all_findings if f.get('severity') == 'medium'],
            'low': [f for f in all_findings if f.get('severity') == 'low'],
            'info': [f for f in all_findings if f.get('severity') == 'info']
        }
        
        # Calculate security score (0-100)
        total_checks = len(all_findings)
        critical_count = len(findings_by_severity['critical'])
        high_count = len(findings_by_severity['high'])
        medium_count = len(findings_by_severity['medium'])
        
        # Simple scoring: deduct points based on severity
        security_score = 100
        security_score -= critical_count * 25
        security_score -= high_count * 15
        security_score -= medium_count * 5
        security_score = max(0, security_score)
        
        return {
            'storage_account': storage_account['name'],
            'security_score': security_score,
            'total_findings': len(all_findings),
            'findings_by_severity': findings_by_severity,
            'all_findings': all_findings
        }
