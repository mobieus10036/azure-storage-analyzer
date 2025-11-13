#!/usr/bin/env python3
"""
Azure Storage Assessment Toolkit
Main CLI entry point
"""

import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Import internal modules
from src.utils import (
    get_azure_credential,
    Config,
    setup_logging,
    ensure_directory,
    get_timestamp_string
)
from src.collectors import (
    StorageAccountCollector,
    BlobContainerCollector,
    MetricsCollector,
    FileShareCollector
)
from src.analyzers import (
    CostAnalyzer,
    SecurityAnalyzer,
    GovernanceAnalyzer
)
from src.reporters import (
    JSONReporter,
    CSVReporter,
    MarkdownReporter,
    PDFReporter
)

logger = logging.getLogger(__name__)


def detect_workload_profile_from_shares(file_shares):
    """
    Auto-detect workload profile based on file share characteristics.
    
    Args:
        file_shares: List of file share data
        
    Returns:
        Detected profile: 'light', 'moderate', or 'heavy'
    """
    if not file_shares:
        return 'light'
    
    # Check for FSLogix/AVD indicators in share names
    fslogix_indicators = ['fslogix', 'profile', 'userprofile', 'avd', 'wvd', 'vdi', 'citrix']
    
    for share in file_shares:
        share_name = share.get('name', '').lower()
        if any(indicator in share_name for indicator in fslogix_indicators):
            logger.info(f"Auto-detected FSLogix/AVD workload from share: {share['name']}")
            return 'heavy'
    
    # Check total capacity (large file shares often have higher transaction rates)
    total_capacity_gb = sum(share.get('usage_bytes', 0) for share in file_shares) / (1024 ** 3)
    
    if total_capacity_gb > 500:  # Large deployments likely have moderate-to-heavy usage
        logger.info(f"Auto-detected moderate workload based on capacity: {total_capacity_gb:.2f} GB")
        return 'moderate'
    
    logger.info(f"Auto-detected light workload (capacity: {total_capacity_gb:.2f} GB)")
    return 'light'


class StorageAssessment:
    """Main assessment orchestrator."""
    
    def __init__(self, config: Config):
        """
        Initialize assessment.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.credential = get_azure_credential()
        
        # Initialize collectors
        self.storage_collector = StorageAccountCollector(self.credential)
        self.blob_collector = BlobContainerCollector(self.credential)
        self.metrics_collector = MetricsCollector(self.credential)
        self.fileshare_collector = FileShareCollector(self.credential)
        
        # Initialize analyzers
        self.cost_analyzer = CostAnalyzer(
            pricing_region=config.get('cost_analysis.pricing_region', 'eastus'),
            workload_profile=config.get('cost_analysis.workload_profile', 'moderate')
        )
        self.security_analyzer = SecurityAnalyzer()
        self.governance_analyzer = GovernanceAnalyzer()
        
        # Assessment results
        self.results = {
            'metadata': {
                'assessment_time': datetime.utcnow().isoformat(),
                'config': config.data
            },
            'storage_accounts': [],
            'summary': {}
        }
    
    def collect_data(self):
        """Collect data from Azure."""
        logger.info("=" * 80)
        logger.info("Starting data collection...")
        logger.info("=" * 80)
        
        # Collect storage accounts
        logger.info("Collecting storage accounts...")
        storage_accounts = self.storage_collector.collect_all(self.config.data)
        
        logger.info(f"Found {len(storage_accounts)} storage accounts")
        
        if not storage_accounts:
            logger.warning("No storage accounts found. Assessment complete.")
            return
        
        # Process each storage account
        parallel_config = self.config.get('execution.parallel', {})
        use_parallel = parallel_config.get('enabled', True)
        max_workers = parallel_config.get('max_workers', 5)
        
        if use_parallel and len(storage_accounts) > 1:
            logger.info(f"Processing storage accounts in parallel (max {max_workers} workers)...")
            self._process_parallel(storage_accounts, max_workers)
        else:
            logger.info("Processing storage accounts sequentially...")
            self._process_sequential(storage_accounts)
        
        logger.info(f"Data collection complete. Processed {len(self.results['storage_accounts'])} storage accounts.")
    
    def _process_sequential(self, storage_accounts):
        """Process storage accounts sequentially."""
        for account in tqdm(storage_accounts, desc="Processing storage accounts"):
            try:
                result = self._process_storage_account(account)
                self.results['storage_accounts'].append(result)
            except Exception as e:
                logger.error(f"Failed to process {account['name']}: {e}")
    
    def _process_parallel(self, storage_accounts, max_workers):
        """Process storage accounts in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._process_storage_account, account): account
                for account in storage_accounts
            }
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing storage accounts"):
                account = futures[future]
                try:
                    result = future.result()
                    self.results['storage_accounts'].append(result)
                except Exception as e:
                    logger.error(f"Failed to process {account['name']}: {e}")
    
    def _process_storage_account(self, storage_account):
        """
        Process a single storage account.
        
        Args:
            storage_account: Storage account dictionary
            
        Returns:
            Dictionary with complete assessment data for the account
        """
        account_name = storage_account['name']
        logger.debug(f"Processing storage account: {account_name}")
        
        # Collect containers
        containers = self.blob_collector.collect_container_data(
            storage_account,
            self.config.data
        )
        
        # Collect file shares
        file_shares = self.fileshare_collector.collect_share_data(
            account_name,
            f"https://{account_name}.blob.core.windows.net",
            self.config.data
        )
        
        # Collect metrics (if enabled)
        metrics = {}
        if self.config.get('metrics.enabled', True):
            metrics = self.metrics_collector.collect_metrics_for_account(
                storage_account,
                self.config.data
            )
        
        # Analyze costs
        cost_analysis = {}
        if self.config.get('cost_analysis.enabled', True):
            cost_analysis = self.cost_analyzer.analyze_storage_account_costs(
                storage_account,
                containers,
                file_shares,
                self.config.data
            )
        
        # Analyze security
        security_analysis = self.security_analyzer.analyze_storage_account_security(
            storage_account,
            self.config.data
        )
        
        # Analyze governance
        governance_analysis = self.governance_analyzer.analyze_governance(
            storage_account,
            containers,
            metrics,
            self.config.data
        )
        
        return {
            'storage_account': storage_account,
            'containers': containers,
            'file_shares': file_shares,
            'metrics': metrics,
            'cost_analysis': cost_analysis,
            'security_analysis': security_analysis,
            'governance_analysis': governance_analysis
        }
    
    def analyze_results(self):
        """Analyze collected data and generate summary."""
        logger.info("Analyzing results...")
        
        # Auto-detect workload profile if set to 'auto'
        current_profile = self.config.get('cost_analysis.workload_profile', 'moderate')
        if current_profile == 'auto':
            # Collect all file shares from all accounts
            all_file_shares = []
            for account in self.results['storage_accounts']:
                all_file_shares.extend(account.get('file_shares', []))
            
            # Detect workload profile
            detected_profile = detect_workload_profile_from_shares(all_file_shares)
            logger.info(f"Auto-detected workload profile: {detected_profile}")
            
            # Update cost analyzer with detected profile
            self.cost_analyzer.workload_profile = detected_profile
            
            # Recalculate costs with new profile
            for account_data in self.results['storage_accounts']:
                if self.config.get('cost_analysis.enabled', True):
                    account_data['cost_analysis'] = self.cost_analyzer.analyze_storage_account_costs(
                        account_data['storage_account'],
                        account_data.get('containers', []),
                        account_data.get('file_shares', []),
                        self.config.data
                    )
        
        summary = {
            'statistics': self._calculate_statistics(),
            'findings_statistics': self._calculate_findings_statistics(),
            'top_recommendations': self._generate_top_recommendations(),
            'storage_accounts_summary': self._generate_accounts_summary()
        }
        
        self.results['summary'] = summary
        logger.info("Analysis complete.")
    
    def _calculate_statistics(self):
        """Calculate overall statistics."""
        accounts = self.results['storage_accounts']
        
        stats = {
            'total_storage_accounts': len(accounts),
            'total_subscriptions': len(set(a['storage_account']['subscription_id'] for a in accounts)),
            'total_containers': sum(len(a.get('containers', [])) for a in accounts),
            'total_file_shares': sum(len(a.get('file_shares', [])) for a in accounts),
            'total_blobs': sum(
                sum(c.get('blob_count', 0) for c in a.get('containers', []))
                for a in accounts
            ),
            'total_capacity_bytes': sum(
                sum(c.get('total_size_bytes', 0) for c in a.get('containers', []))
                for a in accounts
            ) + sum(
                sum(s.get('usage_bytes', 0) for s in a.get('file_shares', []))
                for a in accounts
            ),
            'total_stale_size_bytes': sum(
                sum(c.get('stale_size_bytes', 0) for c in a.get('containers', []))
                for a in accounts
            ),
            'total_monthly_cost': sum(
                a.get('cost_analysis', {}).get('total_monthly_cost', 0)
                for a in accounts
            ),
            'total_monthly_savings': sum(
                a.get('cost_analysis', {}).get('total_monthly_savings', 0)
                for a in accounts
            ),
            'average_security_score': sum(
                a.get('security_analysis', {}).get('security_score', 0)
                for a in accounts
            ) / len(accounts) if accounts else 0,
            'accounts_with_public_access': sum(
                1 for a in accounts
                if a['storage_account'].get('allow_blob_public_access')
            ),
            'accounts_without_https_only': sum(
                1 for a in accounts
                if not a['storage_account'].get('https_only')
            ),
            'accounts_with_https_only': sum(
                1 for a in accounts
                if a['storage_account'].get('https_only')
            ),
            'accounts_without_public_access': sum(
                1 for a in accounts
                if not a['storage_account'].get('allow_blob_public_access')
            ),
            'accounts_with_soft_delete': sum(
                1 for a in accounts
                if a['storage_account'].get('blob_service_properties', {})
                .get('delete_retention_policy', {}).get('enabled')
            ),
            'accounts_without_soft_delete': sum(
                1 for a in accounts
                if not a['storage_account'].get('blob_service_properties', {})
                .get('delete_retention_policy', {}).get('enabled')
            ),
            'accounts_with_versioning': sum(
                1 for a in accounts
                if a['storage_account'].get('blob_service_properties', {})
                .get('is_versioning_enabled')
            ),
            'accounts_with_tls12': sum(
                1 for a in accounts
                if a['storage_account'].get('min_tls_version') in ['TLS1_2', 'TLS1_3']
            )
        }
        
        return stats
    
    def _calculate_findings_statistics(self):
        """Calculate findings statistics."""
        all_findings = []
        
        for account in self.results['storage_accounts']:
            security_findings = account.get('security_analysis', {}).get('all_findings', [])
            governance_findings = account.get('governance_analysis', {}).get('all_findings', [])
            
            # Add storage account name to each finding
            for finding in security_findings + governance_findings:
                finding['storage_account'] = account['storage_account']['name']
            
            all_findings.extend(security_findings)
            all_findings.extend(governance_findings)
        
        return {
            'total': len(all_findings),
            'critical': len([f for f in all_findings if f.get('severity') == 'critical']),
            'high': len([f for f in all_findings if f.get('severity') == 'high']),
            'medium': len([f for f in all_findings if f.get('severity') == 'medium']),
            'low': len([f for f in all_findings if f.get('severity') == 'low']),
            'info': len([f for f in all_findings if f.get('severity') == 'info'])
        }
    
    def _generate_top_recommendations(self):
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Collect all findings and cost recommendations
        for account in self.results['storage_accounts']:
            account_name = account['storage_account']['name']
            
            # Security findings
            security_findings = account.get('security_analysis', {}).get('all_findings', [])
            for finding in security_findings:
                recommendations.append({
                    'storage_account': account_name,
                    'severity': finding.get('severity', 'info'),
                    'title': finding.get('finding', 'Unknown'),
                    'finding': finding.get('finding', ''),
                    'impact': finding.get('type', ''),
                    'recommendation': finding.get('recommendation', ''),
                    'category': 'security'
                })
            
            # Cost recommendations
            cost_recs = account.get('cost_analysis', {}).get('optimization_recommendations', [])
            for rec in cost_recs:
                recommendations.append({
                    'storage_account': account_name,
                    'severity': rec.get('severity', 'medium'),
                    'title': f"Optimize {rec.get('container')} tier",
                    'finding': rec.get('reason', ''),
                    'impact': f"Cost optimization: {rec.get('current_tier')} → {rec.get('recommended_tier')}",
                    'recommendation': rec.get('reason', ''),
                    'estimated_savings': rec.get('estimated_savings', {}).get('monthly_savings', 0),
                    'category': 'cost'
                })
        
        # Sort by severity and potential savings
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        recommendations.sort(
            key=lambda x: (
                severity_order.get(x.get('severity', 'info'), 99),
                -x.get('estimated_savings', 0)
            )
        )
        
        return recommendations[:20]  # Top 20
    
    def _generate_accounts_summary(self):
        """Generate per-account summary."""
        summary = []
        
        for account in self.results['storage_accounts']:
            storage_account = account['storage_account']
            containers = account.get('containers', [])
            file_shares = account.get('file_shares', [])
            cost_analysis = account.get('cost_analysis', {})
            security_analysis = account.get('security_analysis', {})
            
            total_size_bytes = sum(c.get('total_size_bytes', 0) for c in containers)
            total_size_bytes += sum(s.get('usage_bytes', 0) for s in file_shares)
            
            summary.append({
                'name': storage_account['name'],
                'location': storage_account['location'],
                'sku': storage_account['sku'],
                'size_bytes': total_size_bytes,
                'container_count': len(containers),
                'share_count': len(file_shares),
                'security_score': security_analysis.get('security_score', 0),
                'monthly_cost': cost_analysis.get('total_monthly_cost', 0),
                'potential_savings': cost_analysis.get('total_monthly_savings', 0)
            })
        
        return summary
    
    def generate_reports(self):
        """Generate output reports."""
        logger.info("Generating reports...")
        
        output_dir = self.config.get('output.directory', './reports')
        ensure_directory(output_dir)
        
        timestamp = get_timestamp_string()
        formats = self.config.get('output.formats', ['json', 'csv', 'markdown'])
        
        generated_files = []
        
        # JSON report
        if 'json' in formats:
            json_reporter = JSONReporter(output_dir)
            json_file = json_reporter.generate_report(
                self.results,
                f"storage_assessment_{timestamp}.json"
            )
            generated_files.append(json_file)
            logger.info(f"✓ JSON report: {json_file}")
        
        # CSV reports
        if 'csv' in formats:
            csv_reporter = CSVReporter(output_dir)
            
            csv_file = csv_reporter.generate_storage_accounts_csv(
                self.results['storage_accounts'],
                f"storage_accounts_{timestamp}.csv"
            )
            generated_files.append(csv_file)
            logger.info(f"✓ CSV report: {csv_file}")
            
            # Findings CSV
            all_findings = []
            for account in self.results['storage_accounts']:
                findings = (
                    account.get('security_analysis', {}).get('all_findings', []) +
                    account.get('governance_analysis', {}).get('all_findings', [])
                )
                for finding in findings:
                    finding['storage_account'] = account['storage_account']['name']
                all_findings.extend(findings)
            
            if all_findings:
                findings_file = csv_reporter.generate_findings_csv(
                    all_findings,
                    f"findings_{timestamp}.csv"
                )
                generated_files.append(findings_file)
                logger.info(f"✓ Findings CSV: {findings_file}")
        
        # Markdown summary
        markdown_file = None
        if 'markdown' in formats:
            md_reporter = MarkdownReporter(output_dir)
            markdown_file = md_reporter.generate_report(
                self.results['summary'],
                f"summary_{timestamp}.md"
            )
            generated_files.append(markdown_file)
            logger.info(f"✓ Markdown summary: {markdown_file}")
        
        # PDF report (generated from Markdown)
        if 'pdf' in formats:
            try:
                pdf_reporter = PDFReporter(output_dir)
                
                # Generate markdown first if not already done
                if not markdown_file:
                    md_reporter = MarkdownReporter(output_dir)
                    markdown_file = md_reporter.generate_report(
                        self.results['summary'],
                        f"summary_{timestamp}.md"
                    )
                
                # Convert markdown to PDF
                pdf_file = pdf_reporter.generate_report(
                    markdown_file=markdown_file,
                    filename=f"summary_{timestamp}.pdf"
                )
                generated_files.append(pdf_file)
                logger.info(f"✓ PDF summary: {pdf_file}")
            except ImportError as e:
                logger.warning(f"PDF generation skipped: {e}")
                logger.warning("Install PDF dependencies with: pip install reportlab")
            except Exception as e:
                logger.error(f"Failed to generate PDF report: {e}")
        
        logger.info(f"Reports generated in: {output_dir}")
        return generated_files
    
    def run(self):
        """Run complete assessment."""
        try:
            self.collect_data()
            self.analyze_results()
            report_files = self.generate_reports()
            
            logger.info("=" * 80)
            logger.info("Assessment Complete!")
            logger.info("=" * 80)
            logger.info(f"Assessed {len(self.results['storage_accounts'])} storage accounts")
            logger.info(f"Generated {len(report_files)} report files")
            
            # Print summary statistics
            stats = self.results['summary'].get('statistics', {})
            logger.info(f"\nTotal capacity: {stats.get('total_capacity_bytes', 0) / (1024**3):.2f} GB")
            logger.info(f"Estimated monthly cost: ${stats.get('total_monthly_cost', 0):.2f}")
            logger.info(f"Potential monthly savings: ${stats.get('total_monthly_savings', 0):.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Assessment failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Azure Storage Assessment Toolkit - Analyze storage accounts for cost, security, and governance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick assessment (fast, PDF only)
  python assess_storage.py --quick --pdf-only

  # Standard assessment with all reports
  python assess_storage.py

  # Security-focused assessment
  python assess_storage.py --config examples/scenarios/security-audit.yaml

  # FinOps cost review
  python assess_storage.py --config examples/scenarios/finops-review.yaml

  # FSLogix optimization
  python assess_storage.py --config examples/scenarios/fslogix-optimization.yaml

  # Custom subscriptions only
  python assess_storage.py --subscription sub-id-1 --subscription sub-id-2
        """
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--subscription',
        action='append',
        dest='subscriptions',
        help='Subscription ID to assess (can be specified multiple times)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for reports'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode: skip detailed metrics collection (5x faster)'
    )
    parser.add_argument(
        '--pdf-only',
        action='store_true',
        help='Generate PDF report only (skip JSON/CSV)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    logger.info("=" * 80)
    logger.info("Azure Storage Assessment Toolkit")
    logger.info("=" * 80)
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Override config with command-line arguments
        if args.subscriptions:
            config.set('scope.subscriptions', args.subscriptions)
        
        if args.output_dir:
            config.set('output.directory', args.output_dir)
        
        if args.quick:
            logger.info("Quick mode enabled - skipping detailed metrics collection")
            config.set('execution.quick_mode', True)
            config.set('metrics.enabled', False)
            config.set('execution.parallel.max_workers', 10)
        
        if args.pdf_only:
            logger.info("PDF-only mode enabled")
            config.set('output.formats', ['pdf'])
        
        if args.verbose:
            config.set('execution.verbose', True)
        
        # Run assessment
        assessment = StorageAssessment(config)
        success = assessment.run()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\nAssessment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
