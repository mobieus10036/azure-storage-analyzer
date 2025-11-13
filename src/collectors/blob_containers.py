"""
Blob container collector module.
Collects information about blob containers and blobs within storage accounts.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

logger = logging.getLogger(__name__)


class BlobContainerCollector:
    """Collects blob container and blob information."""
    
    def __init__(self, credential: TokenCredential):
        """
        Initialize the collector.
        
        Args:
            credential: Azure credential object
        """
        self.credential = credential
    
    def get_containers(self, account_url: str) -> List[Dict]:
        """
        Get all containers in a storage account.
        
        Args:
            account_url: Storage account URL (https://<account>.blob.core.windows.net)
            
        Returns:
            List of container dictionaries
        """
        containers = []
        
        try:
            blob_service_client = BlobServiceClient(account_url=account_url, credential=self.credential)
            
            for container in blob_service_client.list_containers(include_metadata=True):
                container_info = {
                    'name': container.name,
                    'last_modified': container.last_modified.isoformat() if container.last_modified else None,
                    'public_access': container.public_access if hasattr(container, 'public_access') else None,
                    'has_immutability_policy': container.has_immutability_policy if hasattr(container, 'has_immutability_policy') else False,
                    'has_legal_hold': container.has_legal_hold if hasattr(container, 'has_legal_hold') else False,
                    'metadata': container.metadata or {},
                    'lease_status': container.lease.status if hasattr(container, 'lease') and container.lease else None,
                    'lease_state': container.lease.state if hasattr(container, 'lease') and container.lease else None,
                    
                    # To be populated
                    'blob_count': 0,
                    'total_size_bytes': 0,
                    'stale_blob_count': 0,
                    'access_tier_distribution': {}
                }
                
                containers.append(container_info)
                logger.debug(f"Found container: {container.name}")
            
            logger.info(f"Found {len(containers)} containers in storage account")
            return containers
            
        except HttpResponseError as e:
            logger.error(f"HTTP error listing containers: {e.message}")
            return []
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []
    
    def analyze_container_blobs(
        self,
        account_url: str,
        container_name: str,
        stale_threshold_days: int = 90,
        sample_size: Optional[int] = None,
        max_blobs: Optional[int] = None
    ) -> Dict:
        """
        Analyze blobs within a container.
        
        Args:
            account_url: Storage account URL
            container_name: Container name
            stale_threshold_days: Days to consider a blob stale
            sample_size: If set, sample this many blobs instead of analyzing all
            max_blobs: Maximum number of blobs to analyze (for performance)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            blob_service_client = BlobServiceClient(account_url=account_url, credential=self.credential)
            container_client = blob_service_client.get_container_client(container_name)
            
            analysis = {
                'blob_count': 0,
                'total_size_bytes': 0,
                'stale_blob_count': 0,
                'stale_size_bytes': 0,
                'access_tier_distribution': {
                    'Hot': {'count': 0, 'size_bytes': 0},
                    'Cool': {'count': 0, 'size_bytes': 0},
                    'Archive': {'count': 0, 'size_bytes': 0},
                    'None': {'count': 0, 'size_bytes': 0}
                },
                'blob_types': {
                    'BlockBlob': 0,
                    'PageBlob': 0,
                    'AppendBlob': 0
                },
                'sampled': sample_size is not None,
                'sample_size': 0
            }
            
            blobs_analyzed = 0
            
            # List blobs
            for blob in container_client.list_blobs(include=['metadata', 'tags']):
                # Stop if max limit reached
                if max_blobs and blobs_analyzed >= max_blobs:
                    logger.debug(f"Reached max blob limit ({max_blobs}) for container {container_name}")
                    break
                
                # Sample if configured
                if sample_size and blobs_analyzed >= sample_size:
                    logger.debug(f"Reached sample size ({sample_size}) for container {container_name}")
                    analysis['sample_size'] = blobs_analyzed
                    break
                
                blob_size = blob.size or 0
                analysis['blob_count'] += 1
                analysis['total_size_bytes'] += blob_size
                blobs_analyzed += 1
                
                # Access tier analysis
                access_tier = blob.blob_tier if hasattr(blob, 'blob_tier') and blob.blob_tier else 'None'
                if access_tier in analysis['access_tier_distribution']:
                    analysis['access_tier_distribution'][access_tier]['count'] += 1
                    analysis['access_tier_distribution'][access_tier]['size_bytes'] += blob_size
                
                # Blob type
                blob_type = str(blob.blob_type) if blob.blob_type else 'Unknown'
                if blob_type in analysis['blob_types']:
                    analysis['blob_types'][blob_type] += 1
                
                # Stale blob detection
                last_accessed = None
                
                # Check last access time if available (requires analytics logging)
                if hasattr(blob, 'last_accessed_on') and blob.last_accessed_on:
                    last_accessed = blob.last_accessed_on
                # Fall back to last modified
                elif hasattr(blob, 'last_modified') and blob.last_modified:
                    last_accessed = blob.last_modified
                
                if last_accessed:
                    # Ensure timezone aware
                    if last_accessed.tzinfo is None:
                        last_accessed = last_accessed.replace(tzinfo=timezone.utc)
                    
                    days_since_access = (datetime.now(timezone.utc) - last_accessed).days
                    
                    if days_since_access >= stale_threshold_days:
                        analysis['stale_blob_count'] += 1
                        analysis['stale_size_bytes'] += blob_size
            
            if sample_size and blobs_analyzed < sample_size:
                analysis['sample_size'] = blobs_analyzed
            
            logger.debug(f"Analyzed {blobs_analyzed} blobs in container {container_name}")
            return analysis
            
        except ResourceNotFoundError:
            logger.warning(f"Container {container_name} not found")
            return {
                'blob_count': 0,
                'total_size_bytes': 0,
                'stale_blob_count': 0,
                'error': 'Container not found'
            }
        except Exception as e:
            logger.error(f"Failed to analyze container {container_name}: {e}")
            return {
                'blob_count': 0,
                'total_size_bytes': 0,
                'stale_blob_count': 0,
                'error': str(e)
            }
    
    def collect_container_data(
        self,
        storage_account: Dict,
        config: Dict
    ) -> List[Dict]:
        """
        Collect container data for a storage account.
        
        Args:
            storage_account: Storage account dictionary
            config: Configuration dictionary
            
        Returns:
            List of enriched container dictionaries
        """
        account_url = f"https://{storage_account['name']}.blob.core.windows.net"
        
        # Get containers
        containers = self.get_containers(account_url)
        
        # Configuration
        stale_days = config.get('stale_data', {}).get('threshold_days', 90)
        sample_size = config.get('stale_data', {}).get('sample_size', 10000)
        max_container_size = config.get('stale_data', {}).get('max_container_size', 1000000)
        quick_mode = config.get('execution', {}).get('quick_mode', False)
        
        # Analyze each container
        for container in containers:
            if quick_mode:
                # Quick mode: skip detailed blob analysis
                logger.debug(f"Quick mode: skipping detailed analysis for {container['name']}")
                continue
            
            analysis = self.analyze_container_blobs(
                account_url=account_url,
                container_name=container['name'],
                stale_threshold_days=stale_days,
                sample_size=sample_size,
                max_blobs=max_container_size
            )
            
            # Merge analysis into container data
            container.update(analysis)
        
        return containers
