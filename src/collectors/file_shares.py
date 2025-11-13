"""
File share collector module.
Collects information about Azure File shares within storage accounts.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from azure.storage.fileshare import ShareServiceClient, ShareClient
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

logger = logging.getLogger(__name__)


class FileShareCollector:
    """Collects Azure File share information."""
    
    def __init__(self, credential: TokenCredential):
        """
        Initialize the collector.
        
        Args:
            credential: Azure credential object
        """
        self.credential = credential
    
    def get_file_shares(self, account_url: str) -> List[Dict]:
        """
        Get all file shares in a storage account.
        
        Args:
            account_url: Storage account URL (e.g., https://account.blob.core.windows.net)
            
        Returns:
            List of file share information dictionaries
        """
        shares = []
        
        try:
            # Convert blob URL to file URL
            file_account_url = account_url.replace('.blob.', '.file.')
            
            # Create service client
            service_client = ShareServiceClient(
                account_url=file_account_url,
                credential=self.credential,
                token_intent='backup'  # Required for Azure AD authentication
            )
            
            # List all shares
            share_list = service_client.list_shares(include_metadata=True, include_snapshots=False)
            
            for share in share_list:
                try:
                    share_info = {
                        'name': share.name,
                        'quota': share.get('quota', 0),  # GB
                        'metadata': share.get('metadata', {}),
                        'last_modified': share.get('last_modified').isoformat() if share.get('last_modified') else None,
                        'etag': share.get('etag'),
                        'access_tier': getattr(share, 'access_tier', None),
                        'protocols': getattr(share, 'enabled_protocols', None),
                        'root_squash': getattr(share, 'root_squash', None),
                    }
                    
                    # Get share client for detailed properties
                    share_client = service_client.get_share_client(share.name)
                    
                    try:
                        properties = share_client.get_share_properties()
                        share_info.update({
                            'provisioned_quota': properties.quota,
                            'snapshot': properties.snapshot,
                            'access_tier': getattr(properties, 'access_tier', None),
                            'access_tier_change_time': getattr(properties, 'access_tier_change_time', None),
                            'access_tier_transition_state': getattr(properties, 'access_tier_transition_state', None),
                            'deleted': getattr(properties, 'deleted', False),
                            'deleted_time': getattr(properties, 'deleted_time', None),
                            'remaining_retention_days': getattr(properties, 'remaining_retention_days', None),
                            'enabled_protocols': getattr(properties, 'enabled_protocols', 'SMB'),
                            'root_squash': getattr(properties, 'root_squash', None),
                        })
                        
                        # Get share statistics (usage)
                        try:
                            stats = share_client.get_share_stats()
                            share_info['usage_bytes'] = stats.share_usage_bytes if hasattr(stats, 'share_usage_bytes') else stats
                            share_info['usage_gb'] = round(share_info['usage_bytes'] / (1024**3), 2) if share_info['usage_bytes'] else 0
                        except Exception as e:
                            logger.debug(f"Could not get stats for share {share.name}: {e}")
                            share_info['usage_bytes'] = 0
                            share_info['usage_gb'] = 0
                            
                    except Exception as e:
                        logger.warning(f"Could not get detailed properties for share {share.name}: {e}")
                    
                    shares.append(share_info)
                    logger.debug(f"Found file share: {share.name}")
                    
                except Exception as e:
                    logger.warning(f"Error processing share {share.name}: {e}")
                    continue
            
            logger.info(f"Found {len(shares)} file shares in storage account")
            return shares
            
        except HttpResponseError as e:
            if e.status_code == 404:
                logger.debug("Storage account does not have file service enabled or accessible")
                return []
            else:
                logger.warning(f"HTTP error retrieving file shares: {e.message}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving file shares: {e}")
            return []
    
    def analyze_file_share(
        self,
        share_client: ShareClient,
        share_name: str,
        config: Dict
    ) -> Dict:
        """
        Analyze a file share in detail.
        
        Args:
            share_client: ShareClient instance
            share_name: Name of the share
            config: Configuration dictionary
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'share_name': share_name,
            'total_files': 0,
            'total_directories': 0,
            'total_size_bytes': 0,
            'file_types': {},
            'large_files': [],
            'old_files': [],
        }
        
        stale_threshold_days = config.get('stale_data', {}).get('threshold_days', 90)
        large_file_threshold_mb = config.get('stale_data', {}).get('large_file_threshold_mb', 100)
        max_files_to_scan = config.get('stale_data', {}).get('max_files_to_scan', 10000)
        
        try:
            root_dir = share_client.get_directory_client("")
            
            def scan_directory(directory_client, current_path="", depth=0, files_scanned=0):
                """Recursively scan directory."""
                if files_scanned >= max_files_to_scan:
                    return files_scanned
                
                if depth > 10:  # Prevent too deep recursion
                    return files_scanned
                
                try:
                    items = directory_client.list_directories_and_files()
                    
                    for item in items:
                        if files_scanned >= max_files_to_scan:
                            break
                        
                        item_name = item.name if hasattr(item, 'name') else item['name']
                        is_directory = item.get('is_directory', False)
                        
                        if is_directory:
                            analysis['total_directories'] += 1
                            # Recursively scan subdirectory
                            subdir_client = directory_client.get_subdirectory_client(item_name)
                            files_scanned = scan_directory(
                                subdir_client,
                                f"{current_path}/{item_name}" if current_path else item_name,
                                depth + 1,
                                files_scanned
                            )
                        else:
                            # It's a file
                            analysis['total_files'] += 1
                            files_scanned += 1
                            
                            file_size = item.get('size', 0)
                            analysis['total_size_bytes'] += file_size
                            
                            # Track file type
                            ext = item_name.split('.')[-1].lower() if '.' in item_name else 'no_extension'
                            analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
                            
                            # Track large files
                            if file_size > (large_file_threshold_mb * 1024 * 1024):
                                analysis['large_files'].append({
                                    'name': f"{current_path}/{item_name}" if current_path else item_name,
                                    'size_bytes': file_size,
                                    'size_mb': round(file_size / (1024**2), 2)
                                })
                            
                            # Track old files
                            last_modified = item.get('last_modified')
                            if last_modified:
                                age_days = (datetime.now(timezone.utc) - last_modified).days
                                if age_days > stale_threshold_days:
                                    analysis['old_files'].append({
                                        'name': f"{current_path}/{item_name}" if current_path else item_name,
                                        'last_modified': last_modified.isoformat(),
                                        'age_days': age_days,
                                        'size_bytes': file_size
                                    })
                    
                    return files_scanned
                    
                except Exception as e:
                    logger.debug(f"Error scanning directory {current_path}: {e}")
                    return files_scanned
            
            # Start scanning from root
            total_scanned = scan_directory(root_dir)
            
            # Calculate summary statistics
            analysis['total_size_gb'] = round(analysis['total_size_bytes'] / (1024**3), 2)
            analysis['files_scanned'] = total_scanned
            analysis['large_files_count'] = len(analysis['large_files'])
            analysis['old_files_count'] = len(analysis['old_files'])
            
            # Sort large files by size
            analysis['large_files'] = sorted(
                analysis['large_files'],
                key=lambda x: x['size_bytes'],
                reverse=True
            )[:10]  # Keep top 10
            
            # Sort old files by age
            analysis['old_files'] = sorted(
                analysis['old_files'],
                key=lambda x: x['age_days'],
                reverse=True
            )[:10]  # Keep top 10
            
            logger.info(f"Analyzed share {share_name}: {total_scanned} files scanned")
            
        except Exception as e:
            logger.error(f"Error analyzing file share {share_name}: {e}")
        
        return analysis
    
    def collect_share_data(
        self,
        account_name: str,
        account_url: str,
        config: Dict
    ) -> List[Dict]:
        """
        Collect file share data for a storage account.
        
        Args:
            account_name: Storage account name
            account_url: Storage account URL
            config: Configuration dictionary
            
        Returns:
            List of file share data dictionaries
        """
        shares = self.get_file_shares(account_url)
        
        if not shares:
            return []
        
        quick_mode = config.get('execution', {}).get('quick_mode', False)
        
        # Enrich with detailed analysis if not in quick mode
        if not quick_mode:
            file_account_url = account_url.replace('.blob.', '.file.')
            service_client = ShareServiceClient(
                account_url=file_account_url,
                credential=self.credential,
                token_intent='backup'  # Required for Azure AD authentication
            )
            
            for share in shares:
                try:
                    logger.debug(f"Analyzing file share: {share['name']}")
                    share_client = service_client.get_share_client(share['name'])
                    analysis = self.analyze_file_share(share_client, share['name'], config)
                    share['analysis'] = analysis
                except Exception as e:
                    logger.warning(f"Failed to analyze share {share['name']}: {e}")
                    share['analysis'] = {}
        else:
            logger.debug("Quick mode: skipping detailed file share analysis")
        
        return shares
