"""
Storage Account collector module.
Collects information about Azure Storage Accounts across subscriptions.
"""

import logging
from typing import Dict, List, Optional
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.subscription import SubscriptionClient
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError

logger = logging.getLogger(__name__)


class StorageAccountCollector:
    """Collects Azure Storage Account information."""
    
    def __init__(self, credential: TokenCredential):
        """
        Initialize the collector.
        
        Args:
            credential: Azure credential object
        """
        self.credential = credential
        self.subscription_client = SubscriptionClient(credential)
    
    def get_subscriptions(self, subscription_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Get list of accessible subscriptions.
        
        Args:
            subscription_ids: Optional list of specific subscription IDs to filter
            
        Returns:
            List of subscription dictionaries
        """
        subscriptions = []
        
        try:
            all_subs = self.subscription_client.subscriptions.list()
            
            for sub in all_subs:
                # Filter if specific subscriptions requested
                if subscription_ids and sub.subscription_id not in subscription_ids:
                    continue
                
                # Only include enabled subscriptions
                if sub.state == 'Enabled':
                    subscriptions.append({
                        'subscription_id': sub.subscription_id,
                        'display_name': sub.display_name,
                        'state': sub.state,
                        'tenant_id': getattr(sub, 'tenant_id', None)  # Some API versions don't include tenant_id
                    })
                    logger.info(f"Found subscription: {sub.display_name} ({sub.subscription_id})")
            
            logger.info(f"Total accessible subscriptions: {len(subscriptions)}")
            return subscriptions
            
        except Exception as e:
            logger.error(f"Failed to retrieve subscriptions: {e}")
            raise
    
    def get_storage_accounts(
        self,
        subscription_id: str,
        resource_groups: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        required_tags: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Get storage accounts in a subscription.
        
        Args:
            subscription_id: Azure subscription ID
            resource_groups: Optional list of resource groups to filter
            locations: Optional list of locations to filter
            required_tags: Optional tags to filter by
            
        Returns:
            List of storage account dictionaries
        """
        storage_accounts = []
        
        try:
            storage_client = StorageManagementClient(self.credential, subscription_id)
            
            # List all storage accounts in subscription
            all_accounts = storage_client.storage_accounts.list()
            
            for account in all_accounts:
                # Apply filters
                if resource_groups and account.id.split('/')[4] not in resource_groups:
                    continue
                
                if locations and account.location not in locations:
                    continue
                
                if required_tags:
                    account_tags = account.tags or {}
                    if not all(account_tags.get(k) == v for k, v in required_tags.items()):
                        continue
                
                # Extract storage account details
                account_info = {
                    'id': account.id,
                    'name': account.name,
                    'resource_group': account.id.split('/')[4],
                    'location': account.location,
                    'sku': account.sku.name if account.sku else None,
                    'kind': account.kind,
                    'tier': account.sku.tier if account.sku else None,
                    'creation_time': account.creation_time.isoformat() if account.creation_time else None,
                    'primary_location': account.primary_location,
                    'secondary_location': account.secondary_location,
                    'status_of_primary': getattr(account, 'status_of_primary', None),
                    'status_of_secondary': getattr(account, 'status_of_secondary', None),
                    'tags': account.tags or {},
                    
                    # Security settings (use getattr for optional properties)
                    'https_only': getattr(account, 'enable_https_traffic_only', None),
                    'min_tls_version': getattr(account, 'minimum_tls_version', None),
                    'allow_blob_public_access': getattr(account, 'allow_blob_public_access', None),
                    'allow_shared_key_access': getattr(account, 'allow_shared_key_access', None),
                    'default_to_oauth_authentication': getattr(account, 'default_to_oauth_authentication', None),
                    
                    # Encryption
                    'encryption_key_source': account.encryption.key_source if account.encryption else None,
                    'encryption_services': self._get_encryption_services(account.encryption) if account.encryption else {},
                    
                    # Network rules
                    'network_rule_set': self._get_network_rules(account.network_rule_set) if account.network_rule_set else {},
                    
                    # Blob service properties (will be enriched later)
                    'blob_service_properties': {},
                    
                    # Metadata
                    'subscription_id': subscription_id
                }
                
                storage_accounts.append(account_info)
                logger.debug(f"Collected storage account: {account.name}")
            
            logger.info(f"Found {len(storage_accounts)} storage accounts in subscription {subscription_id}")
            return storage_accounts
            
        except HttpResponseError as e:
            logger.error(f"HTTP error retrieving storage accounts: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve storage accounts: {e}")
            raise
    
    def get_blob_service_properties(self, subscription_id: str, resource_group: str, account_name: str) -> Dict:
        """
        Get blob service properties for a storage account.
        
        Args:
            subscription_id: Azure subscription ID
            resource_group: Resource group name
            account_name: Storage account name
            
        Returns:
            Dictionary of blob service properties
        """
        try:
            storage_client = StorageManagementClient(self.credential, subscription_id)
            blob_service = storage_client.blob_services.get_service_properties(
                resource_group,
                account_name
            )
            
            properties = {
                'cors_rules': [],
                'default_service_version': blob_service.default_service_version,
                'delete_retention_policy': self._get_retention_policy(blob_service.delete_retention_policy),
                'is_versioning_enabled': blob_service.is_versioning_enabled,
                'change_feed': self._get_change_feed(blob_service.change_feed),
                'restore_policy': self._get_restore_policy(blob_service.restore_policy),
                'container_delete_retention_policy': self._get_retention_policy(blob_service.container_delete_retention_policy),
                'last_access_time_tracking_policy': self._get_last_access_tracking(blob_service.last_access_time_tracking_policy)
            }
            
            if blob_service.cors and blob_service.cors.cors_rules:
                properties['cors_rules'] = [
                    {
                        'allowed_origins': rule.allowed_origins,
                        'allowed_methods': rule.allowed_methods,
                        'allowed_headers': rule.allowed_headers,
                        'exposed_headers': rule.exposed_headers,
                        'max_age_in_seconds': rule.max_age_in_seconds
                    }
                    for rule in blob_service.cors.cors_rules
                ]
            
            return properties
            
        except Exception as e:
            logger.warning(f"Failed to get blob service properties for {account_name}: {e}")
            return {}
    
    def _get_encryption_services(self, encryption) -> Dict:
        """Extract encryption service information."""
        services = {}
        
        if encryption.services:
            if encryption.services.blob:
                services['blob'] = {
                    'enabled': encryption.services.blob.enabled,
                    'key_type': encryption.services.blob.key_type
                }
            if encryption.services.file:
                services['file'] = {
                    'enabled': encryption.services.file.enabled,
                    'key_type': encryption.services.file.key_type
                }
            if encryption.services.queue:
                services['queue'] = {
                    'enabled': encryption.services.queue.enabled,
                    'key_type': encryption.services.queue.key_type
                }
            if encryption.services.table:
                services['table'] = {
                    'enabled': encryption.services.table.enabled,
                    'key_type': encryption.services.table.key_type
                }
        
        return services
    
    def _get_network_rules(self, network_rule_set) -> Dict:
        """Extract network rule information."""
        rules = {
            'default_action': network_rule_set.default_action,
            'bypass': network_rule_set.bypass,
            'ip_rules': [],
            'virtual_network_rules': [],
            'resource_access_rules': []
        }
        
        if network_rule_set.ip_rules:
            rules['ip_rules'] = [
                {
                    'value': rule.ip_address_or_range,
                    'action': rule.action
                }
                for rule in network_rule_set.ip_rules
            ]
        
        if network_rule_set.virtual_network_rules:
            rules['virtual_network_rules'] = [
                {
                    'id': rule.virtual_network_resource_id,
                    'action': rule.action,
                    'state': rule.state
                }
                for rule in network_rule_set.virtual_network_rules
            ]
        
        return rules
    
    def _get_retention_policy(self, policy) -> Dict:
        """Extract retention policy information."""
        if not policy:
            return {'enabled': False, 'days': None}
        
        return {
            'enabled': policy.enabled,
            'days': policy.days if policy.enabled else None
        }
    
    def _get_change_feed(self, change_feed) -> Dict:
        """Extract change feed information."""
        if not change_feed:
            return {'enabled': False}
        
        return {
            'enabled': change_feed.enabled,
            'retention_in_days': change_feed.retention_in_days if change_feed.enabled else None
        }
    
    def _get_restore_policy(self, policy) -> Dict:
        """Extract restore policy information."""
        if not policy:
            return {'enabled': False}
        
        return {
            'enabled': policy.enabled,
            'days': policy.days if policy.enabled else None
        }
    
    def _get_last_access_tracking(self, policy) -> Dict:
        """Extract last access time tracking policy."""
        if not policy:
            return {'enabled': False}
        
        return {
            'enabled': policy.enable,
            'name': policy.name if policy.enable else None,
            'tracking_granularity_in_days': policy.tracking_granularity_in_days if policy.enable else None
        }
    
    def collect_all(self, config: Dict) -> List[Dict]:
        """
        Collect all storage accounts based on configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of all storage accounts with enriched data
        """
        all_storage_accounts = []
        
        # Get subscriptions
        subscription_ids = config.get('scope', {}).get('subscriptions', [])
        subscriptions = self.get_subscriptions(subscription_ids if subscription_ids else None)
        
        # Collection parameters
        resource_groups = config.get('scope', {}).get('resource_groups', [])
        locations = config.get('scope', {}).get('locations', [])
        required_tags = config.get('scope', {}).get('required_tags', {})
        
        # Collect from each subscription
        for subscription in subscriptions:
            sub_id = subscription['subscription_id']
            logger.info(f"Collecting storage accounts from subscription: {subscription['display_name']}")
            
            accounts = self.get_storage_accounts(
                subscription_id=sub_id,
                resource_groups=resource_groups if resource_groups else None,
                locations=locations if locations else None,
                required_tags=required_tags if required_tags else None
            )
            
            # Enrich with blob service properties
            for account in accounts:
                blob_props = self.get_blob_service_properties(
                    sub_id,
                    account['resource_group'],
                    account['name']
                )
                account['blob_service_properties'] = blob_props
            
            all_storage_accounts.extend(accounts)
        
        logger.info(f"Total storage accounts collected: {len(all_storage_accounts)}")
        return all_storage_accounts
