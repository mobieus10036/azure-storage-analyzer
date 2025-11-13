"""
Metrics collector module.
Collects Azure Monitor metrics for storage accounts.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from azure.mgmt.monitor import MonitorManagementClient
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects Azure Monitor metrics for storage accounts."""
    
    def __init__(self, credential: TokenCredential):
        """
        Initialize the collector.
        
        Args:
            credential: Azure credential object
        """
        self.credential = credential
    
    def get_storage_metrics(
        self,
        subscription_id: str,
        resource_id: str,
        metric_names: List[str],
        time_grain: str = "PT1H",
        retention_days: int = 30
    ) -> Dict[str, List[Dict]]:
        """
        Get Azure Monitor metrics for a storage account.
        
        Args:
            subscription_id: Azure subscription ID
            resource_id: Full resource ID of the storage account
            metric_names: List of metric names to retrieve
            time_grain: Time granularity (PT1M, PT1H, PT1D, etc.)
            retention_days: Number of days to look back
            
        Returns:
            Dictionary mapping metric names to their data points
        """
        metrics_data = {}
        
        try:
            monitor_client = MonitorManagementClient(self.credential, subscription_id)
            
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=retention_days)
            
            # Format time for API
            timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"
            
            # Request metrics
            metrics_list = ','.join(metric_names)
            
            response = monitor_client.metrics.list(
                resource_id,
                timespan=timespan,
                interval=time_grain,
                metricnames=metrics_list,
                aggregation='Total,Average,Maximum'
            )
            
            # Process response
            for metric in response.value:
                metric_name = metric.name.value
                data_points = []
                
                for timeseries in metric.timeseries:
                    for data in timeseries.data:
                        data_point = {
                            'timestamp': data.time_stamp.isoformat() if data.time_stamp else None,
                            'total': data.total if hasattr(data, 'total') else None,
                            'average': data.average if hasattr(data, 'average') else None,
                            'maximum': data.maximum if hasattr(data, 'maximum') else None,
                            'minimum': data.minimum if hasattr(data, 'minimum') else None,
                            'count': data.count if hasattr(data, 'count') else None
                        }
                        data_points.append(data_point)
                
                metrics_data[metric_name] = data_points
                logger.debug(f"Collected {len(data_points)} data points for metric {metric_name}")
            
            return metrics_data
            
        except HttpResponseError as e:
            logger.warning(f"HTTP error retrieving metrics: {e.message}")
            return {}
        except Exception as e:
            logger.warning(f"Failed to retrieve metrics for {resource_id}: {e}")
            return {}
    
    def calculate_usage_statistics(self, metrics_data: Dict[str, List[Dict]]) -> Dict:
        """
        Calculate usage statistics from metrics data.
        
        Args:
            metrics_data: Dictionary of metrics data
            
        Returns:
            Dictionary with calculated statistics
        """
        stats = {
            'total_transactions': 0,
            'total_ingress_bytes': 0,
            'total_egress_bytes': 0,
            'avg_latency_ms': 0,
            'avg_availability_percent': 0,
            'has_activity': False
        }
        
        # Transactions
        if 'Transactions' in metrics_data:
            transactions = metrics_data['Transactions']
            total = sum(dp.get('total', 0) or 0 for dp in transactions)
            stats['total_transactions'] = total
            stats['has_activity'] = total > 0
        
        # Ingress
        if 'Ingress' in metrics_data:
            ingress = metrics_data['Ingress']
            stats['total_ingress_bytes'] = sum(dp.get('total', 0) or 0 for dp in ingress)
        
        # Egress
        if 'Egress' in metrics_data:
            egress = metrics_data['Egress']
            stats['total_egress_bytes'] = sum(dp.get('total', 0) or 0 for dp in egress)
        
        # Latency
        if 'SuccessServerLatency' in metrics_data:
            latency = metrics_data['SuccessServerLatency']
            latency_values = [dp.get('average', 0) or 0 for dp in latency if dp.get('average')]
            if latency_values:
                stats['avg_latency_ms'] = sum(latency_values) / len(latency_values)
        
        # Availability
        if 'Availability' in metrics_data:
            availability = metrics_data['Availability']
            availability_values = [dp.get('average', 0) or 0 for dp in availability if dp.get('average')]
            if availability_values:
                stats['avg_availability_percent'] = sum(availability_values) / len(availability_values)
        
        return stats
    
    def collect_metrics_for_account(
        self,
        storage_account: Dict,
        config: Dict
    ) -> Dict:
        """
        Collect and analyze metrics for a storage account.
        
        Args:
            storage_account: Storage account dictionary
            config: Configuration dictionary
            
        Returns:
            Dictionary with metrics data and statistics
        """
        metrics_config = config.get('metrics', {})
        
        if not metrics_config.get('enabled', True):
            logger.debug(f"Metrics collection disabled for {storage_account['name']}")
            return {}
        
        subscription_id = storage_account['subscription_id']
        resource_id = storage_account['id']
        
        metric_names = metrics_config.get('metrics_list', [
            'Transactions',
            'Ingress',
            'Egress',
            'SuccessServerLatency',
            'Availability'
        ])
        
        time_grain = metrics_config.get('time_grain', 'PT1D')
        retention_days = metrics_config.get('retention_days', 30)
        
        # Collect metrics
        metrics_data = self.get_storage_metrics(
            subscription_id=subscription_id,
            resource_id=resource_id,
            metric_names=metric_names,
            time_grain=time_grain,
            retention_days=retention_days
        )
        
        # Calculate statistics
        statistics = self.calculate_usage_statistics(metrics_data)
        
        return {
            'metrics': metrics_data,
            'statistics': statistics
        }
