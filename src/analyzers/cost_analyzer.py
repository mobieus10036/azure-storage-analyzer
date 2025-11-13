"""
Cost analyzer module.
Analyzes storage costs and identifies optimization opportunities.
"""

import logging
from typing import Dict, List
from ..utils.helpers import format_bytes, format_currency

logger = logging.getLogger(__name__)


# Approximate Azure Storage pricing (per GB per month) - East US region
# These are estimates; actual pricing varies by region and commitment
PRICING = {
    'Hot': {
        'Standard_LRS': 0.0184,
        'Standard_GRS': 0.0368,
        'Standard_RAGRS': 0.046,
        'Standard_ZRS': 0.0221,
        'Standard_GZRS': 0.0455,
        'Standard_RAGZRS': 0.05525
    },
    'Cool': {
        'Standard_LRS': 0.01,
        'Standard_GRS': 0.02,
        'Standard_RAGRS': 0.025,
        'Standard_ZRS': 0.012,
        'Standard_GZRS': 0.025,
        'Standard_RAGZRS': 0.03125
    },
    'Archive': {
        'Standard_LRS': 0.00099,
        'Standard_GRS': 0.00198,
        'Standard_RAGRS': 0.00198
    }
}

# Azure Files workload profiles - blended storage + transaction costs
# Actual costs vary significantly based on read/write/list operation patterns
FILE_SHARE_PRICING = {
    'light': {  # Light usage: basic file storage, infrequent access
        'Standard_LRS': 0.10,  # ~$0.075/GB storage + ~$0.025/GB transactions
        'Standard_GRS': 0.18,
        'Standard_ZRS': 0.12,
        'Standard_GZRS': 0.22,
        'Premium_LRS': 0.20,
        'Premium_ZRS': 0.24
    },
    'moderate': {  # Moderate usage: typical department file shares
        'Standard_LRS': 0.20,  # ~$0.075/GB storage + ~$0.125/GB transactions
        'Standard_GRS': 0.35,
        'Standard_ZRS': 0.25,
        'Standard_GZRS': 0.45,
        'Premium_LRS': 0.20,
        'Premium_ZRS': 0.24
    },
    'heavy': {  # Heavy usage: FSLogix, AVD profiles, continuous I/O
        'Standard_LRS': 0.48,  # ~$0.075/GB storage + ~$0.40/GB transactions
        'Standard_GRS': 0.75,
        'Standard_ZRS': 0.55,
        'Standard_GZRS': 0.85,
        'Premium_LRS': 0.20,  # Premium includes transactions in storage cost
        'Premium_ZRS': 0.24
    }
}


class CostAnalyzer:
    """Analyzes storage costs and optimization opportunities."""
    
    def __init__(self, pricing_region: str = 'eastus', workload_profile: str = 'moderate'):
        """
        Initialize the analyzer.
        
        Args:
            pricing_region: Azure region for pricing estimates
            workload_profile: Workload profile for file share transaction estimates (light/moderate/heavy)
        """
        self.pricing_region = pricing_region
        self.workload_profile = workload_profile
    
    def estimate_storage_cost(
        self,
        size_bytes: int,
        access_tier: str,
        sku: str
    ) -> float:
        """
        Estimate monthly storage cost.
        
        Args:
            size_bytes: Storage size in bytes
            access_tier: Access tier (Hot, Cool, Archive, FileShares)
            sku: Storage SKU name
            
        Returns:
            Estimated monthly cost in USD
        """
        if size_bytes == 0:
            return 0.0
        
        size_gb = size_bytes / (1024 ** 3)
        
        # Handle Azure Files with workload profile
        if access_tier == 'FileShares':
            profile = self.workload_profile if self.workload_profile in FILE_SHARE_PRICING else 'moderate'
            pricing_table = FILE_SHARE_PRICING[profile]
            
            if sku not in pricing_table:
                logger.debug(f"SKU {sku} not found in file share pricing, using Standard_LRS")
                sku = 'Standard_LRS'
            
            price_per_gb = pricing_table.get(sku, 0.20)
            return size_gb * price_per_gb
        
        # Handle blob storage tiers
        tier = access_tier if access_tier in PRICING else 'Hot'
        
        if sku not in PRICING.get(tier, {}):
            # Default to LRS if SKU not found
            logger.debug(f"SKU {sku} not found in pricing, using Standard_LRS")
            sku = 'Standard_LRS'
        
        price_per_gb = PRICING.get(tier, {}).get(sku, 0.0184)
        
        return size_gb * price_per_gb
    
    def calculate_tier_optimization_savings(
        self,
        current_tier: str,
        recommended_tier: str,
        size_bytes: int,
        sku: str
    ) -> Dict:
        """
        Calculate potential savings from tier optimization.
        
        Args:
            current_tier: Current access tier
            recommended_tier: Recommended access tier
            size_bytes: Data size in bytes
            sku: Storage SKU
            
        Returns:
            Dictionary with savings information
        """
        current_cost = self.estimate_storage_cost(size_bytes, current_tier, sku)
        optimized_cost = self.estimate_storage_cost(size_bytes, recommended_tier, sku)
        
        monthly_savings = current_cost - optimized_cost
        annual_savings = monthly_savings * 12
        
        return {
            'current_tier': current_tier,
            'recommended_tier': recommended_tier,
            'size_bytes': size_bytes,
            'size_gb': size_bytes / (1024 ** 3),
            'current_monthly_cost': current_cost,
            'optimized_monthly_cost': optimized_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': annual_savings,
            'savings_percent': (monthly_savings / current_cost * 100) if current_cost > 0 else 0
        }
    
    def analyze_container_cost_optimization(
        self,
        container: Dict,
        config: Dict
    ) -> List[Dict]:
        """
        Analyze cost optimization opportunities for a container.
        
        Args:
            container: Container dictionary with blob analysis
            config: Configuration dictionary
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        tier_config = config.get('cost_analysis', {}).get('tier_recommendations', {})
        cool_tier_days = tier_config.get('cool_tier_days', 30)
        archive_tier_days = tier_config.get('archive_tier_days', 180)
        min_size_gb = tier_config.get('min_size_gb', 1)
        
        # Get stale data information
        stale_blob_count = container.get('stale_blob_count', 0)
        stale_size_bytes = container.get('stale_size_bytes', 0)
        stale_size_gb = stale_size_bytes / (1024 ** 3)
        
        # Check if optimization is worthwhile
        if stale_size_gb < min_size_gb:
            return recommendations
        
        # Analyze access tier distribution
        tier_dist = container.get('access_tier_distribution', {})
        
        # Hot tier with stale data
        hot_tier = tier_dist.get('Hot', {})
        if hot_tier.get('count', 0) > 0 and stale_blob_count > 0:
            # Estimate how much stale data is in Hot tier (proportional)
            hot_stale_ratio = stale_blob_count / max(container.get('blob_count', 1), 1)
            hot_stale_size = hot_tier.get('size_bytes', 0) * hot_stale_ratio
            
            if hot_stale_size > 0:
                recommendations.append({
                    'type': 'tier_optimization',
                    'severity': 'medium',
                    'container': container['name'],
                    'current_tier': 'Hot',
                    'recommended_tier': 'Cool',
                    'affected_size_bytes': hot_stale_size,
                    'affected_blob_count': int(hot_tier.get('count', 0) * hot_stale_ratio),
                    'reason': f'Blobs not accessed in {cool_tier_days}+ days should move to Cool tier',
                    'estimated_savings': self.calculate_tier_optimization_savings(
                        'Hot', 'Cool', int(hot_stale_size), 'Standard_LRS'
                    )
                })
        
        # Very stale data should go to Archive
        if stale_size_bytes > 0:
            # This is approximate - would need more detailed last access data
            recommendations.append({
                'type': 'tier_optimization',
                'severity': 'low',
                'container': container['name'],
                'current_tier': 'Cool',
                'recommended_tier': 'Archive',
                'affected_size_bytes': stale_size_bytes,
                'affected_blob_count': stale_blob_count,
                'reason': f'Very old data (180+ days) could move to Archive tier',
                'estimated_savings': self.calculate_tier_optimization_savings(
                    'Cool', 'Archive', stale_size_bytes, 'Standard_LRS'
                )
            })
        
        return recommendations
    
    def analyze_storage_account_costs(
        self,
        storage_account: Dict,
        containers: List[Dict],
        file_shares: List[Dict],
        config: Dict
    ) -> Dict:
        """
        Analyze costs for a storage account.
        
        Args:
            storage_account: Storage account dictionary
            containers: List of container dictionaries
            file_shares: List of file share dictionaries
            config: Configuration dictionary
            
        Returns:
            Dictionary with cost analysis
        """
        total_size_bytes = sum(c.get('total_size_bytes', 0) for c in containers)
        total_size_bytes += sum(s.get('usage_bytes', 0) for s in file_shares)
        sku = storage_account.get('sku', 'Standard_LRS')
        
        # Calculate costs by tier (for blobs)
        tier_costs = {}
        for tier in ['Hot', 'Cool', 'Archive']:
            tier_size = sum(
                c.get('access_tier_distribution', {}).get(tier, {}).get('size_bytes', 0)
                for c in containers
            )
            if tier_size > 0:
                tier_costs[tier] = {
                    'size_bytes': tier_size,
                    'size_gb': tier_size / (1024 ** 3),
                    'monthly_cost': self.estimate_storage_cost(tier_size, tier, sku)
                }
        
        # Calculate file share costs
        file_share_size = sum(s.get('usage_bytes', 0) for s in file_shares)
        if file_share_size > 0:
            # Azure Files use FileShares pricing tier
            # Note: Pricing includes both storage and estimated transaction costs
            # Actual costs vary based on read/write/list operations
            tier_costs['FileShares'] = {
                'size_bytes': file_share_size,
                'size_gb': file_share_size / (1024 ** 3),
                'monthly_cost': self.estimate_storage_cost(file_share_size, 'FileShares', sku),
                'workload_profile': self.workload_profile,
                'note': f'Estimate based on "{self.workload_profile}" workload profile. Actual costs vary by transaction patterns.'
            }
        
        total_monthly_cost = sum(tc.get('monthly_cost', 0) for tc in tier_costs.values())
        
        # Gather all optimization recommendations
        all_recommendations = []
        for container in containers:
            recommendations = self.analyze_container_cost_optimization(container, config)
            all_recommendations.extend(recommendations)
        
        # Calculate total potential savings
        total_monthly_savings = sum(
            r.get('estimated_savings', {}).get('monthly_savings', 0)
            for r in all_recommendations
        )
        
        return {
            'storage_account': storage_account['name'],
            'total_size_bytes': total_size_bytes,
            'total_size_gb': total_size_bytes / (1024 ** 3),
            'sku': sku,
            'tier_costs': tier_costs,
            'total_monthly_cost': total_monthly_cost,
            'total_annual_cost': total_monthly_cost * 12,
            'optimization_recommendations': all_recommendations,
            'total_monthly_savings': total_monthly_savings,
            'total_annual_savings': total_monthly_savings * 12,
            'savings_percent': (total_monthly_savings / total_monthly_cost * 100) if total_monthly_cost > 0 else 0
        }
