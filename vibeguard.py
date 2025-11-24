#!/usr/bin/env python3
"""
VibeGuard Auditor - SOTA Code Quality Scanner
Detects vibecoding patterns and ranks code from 0-1000
Designed for GitHub Actions with native annotations and job summaries

Refactored for maintainability with modular design
"""

import os
import sys
import argparse
import json
from typing import Tuple, List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rules import RulesManager
from scanner import CodeScanner, GitScanner
from reporter import Reporter
from logger import create_logger


STARTING_SCORE = 1000
DEFAULT_THRESHOLD = 800


def load_config(config_path: str = '.vibeguardrc') -> Tuple[List[str], List[str]]:
    """
    Load user configuration
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Tuple of (ignore_rules, exclude_patterns)
    """
    ignore_rules = []
    exclude_patterns = []
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                ignore_rules = config.get('ignore', [])
                exclude_patterns = config.get('exclude_files', [])
        except Exception as e:
            print(f"⚠️  Failed to load {config_path}: {e}")
    
    return ignore_rules, exclude_patterns


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='VibeGuard Auditor - Anti-slop code quality scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Scan current directory with defaults
  %(prog)s --threshold 900          # Require score >= 900
  %(prog)s --brutal-mode            # Enable brutal mode (double penalties)
  %(prog)s --verbose                # Show detailed logging
  %(prog)s --config custom.json     # Use custom config file
  
Exit codes:
  0: Success (score >= threshold)
  1: Failure (score < threshold or critical violations)
        """
    )
    
    parser.add_argument(
        '--threshold',
        type=int,
        default=None,
        metavar='N',
        help=f'Minimum score required to pass (0-1000). Default: {DEFAULT_THRESHOLD} or INPUT_THRESHOLD env var'
    )
    
    parser.add_argument(
        '--brutal-mode',
        action='store_true',
        default=None,
        help='Enable brutal mode: double penalties and fail-fast on critical violations. Default: false or INPUT_BRUTAL_MODE env var'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='.vibeguardrc',
        metavar='FILE',
        help='Path to configuration file. Default: .vibeguardrc'
    )
    
    parser.add_argument(
        '--rules',
        type=str,
        default=None,
        metavar='FILE',
        help='Path to rules YAML file. Default: config/rules.yaml'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - only show errors'
    )
    
    parser.add_argument(
        '--no-git',
        action='store_true',
        help='Skip git history audit'
    )
    
    parser.add_argument(
        '--directory',
        type=str,
        default='.',
        metavar='DIR',
        help='Directory to scan. Default: current directory'
    )
    
    return parser.parse_args()


def get_config_from_env_or_args(args: argparse.Namespace) -> Tuple[int, bool]:
    """
    Get configuration from environment variables (GitHub Actions) or CLI args
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Tuple of (threshold, brutal_mode)
    """
    # Threshold: CLI arg > env var > default
    if args.threshold is not None:
        threshold = args.threshold
    else:
        threshold = int(os.environ.get("INPUT_THRESHOLD", DEFAULT_THRESHOLD))
    
    # Brutal mode: CLI arg > env var > default
    if args.brutal_mode is not None:
        brutal_mode = args.brutal_mode
    else:
        brutal_mode = os.environ.get("INPUT_BRUTAL_MODE", "false").lower() == "true"
    
    return threshold, brutal_mode


def main() -> int:
    """
    Main entry point
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_args()
    
    # Create logger
    logger = create_logger(verbose=args.verbose, quiet=args.quiet)
    
    # Get configuration
    threshold, brutal_mode = get_config_from_env_or_args(args)
    ignore_rules, exclude_patterns = load_config(args.config)
    
    # Print header
    logger.info("🛡️  VibeGuard Auditor v1.4.0")
    logger.info("=" * 50)
    
    mode_indicator = "🔥 BRUTAL MODE" if brutal_mode else "Standard Mode"
    logger.group_start(f"🔍 Starting VibeGuard Scan ({mode_indicator}, Threshold: {threshold})")
    logger.info(f"Starting Score: {STARTING_SCORE}")
    logger.info(f"Target Threshold: {threshold}")
    
    # Initialize components
    try:
        rules_manager = RulesManager(rules_path=args.rules)
        rules_manager.ignore_rules = set(ignore_rules)
        
        logger.info(f"Active Rules: {len(rules_manager.get_active_rules())}/{len(rules_manager)}")
        if ignore_rules:
            logger.info(f"Ignored Rules: {', '.join(sorted(ignore_rules))}")
        
        code_scanner = CodeScanner(
            rules_manager=rules_manager,
            exclude_patterns=exclude_patterns,
            logger=logger
        )
        
        git_scanner = GitScanner(
            rules_manager=rules_manager,
            logger=logger
        )
        
        reporter = Reporter(logger=logger)
    
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        return 1
    
    # Scan files
    logger.info("")
    logger.info("Scanning files...")
    
    score = STARTING_SCORE
    violations = []
    
    try:
        # Scan code files
        file_violations = code_scanner.scan_directory(
            root_dir=args.directory,
            brutal_mode=brutal_mode
        )
        
        # Convert Violation objects to dictionaries
        for violation in file_violations:
            v_dict = violation.to_dict()
            violations.append(v_dict)
            score -= violation.deduction
            
            # Print GitHub annotation
            if violation.rule_id.startswith(('SEC', 'AI', 'VCS01')):
                reporter.print_github_annotation(v_dict, level="error")
            else:
                reporter.print_github_annotation(v_dict, level="warning")
            
            # Brutal mode: fail fast on critical violations
            if brutal_mode:
                rule = rules_manager.get_rule_by_id(violation.rule_id)
                if rule and rule.get('critical', False):
                    logger.critical("BRUTAL MODE: Critical violation detected. Terminating immediately.")
                    logger.critical(f"Rule {violation.rule_id}: {violation.rule_name} in {violation.file}")
                    logger.group_end()
                    return 1
        
        logger.info(f"Files Scanned: {code_scanner.files_scanned}")
        logger.info(f"File Violations: {len(file_violations)}")
        logger.info(f"File Deductions: -{STARTING_SCORE - score} pts")
        
    except Exception as e:
        logger.error(f"File scanning failed: {e}")
        logger.group_end()
        return 1
    
    logger.group_end()
    
    # Scan git history
    if not args.no_git:
        logger.group_start("🌿 Auditing Git History (Last 50 Commits)")
        
        try:
            git_deductions, git_violations = git_scanner.scan_history(
                brutal_mode=brutal_mode,
                commit_limit=50
            )
            
            score -= git_deductions
            violations.extend(git_violations)
            
            # Print git violations as warnings
            for v in git_violations:
                reporter.print_github_annotation(v, level="warning")
            
            logger.info(f"Git Deductions: -{git_deductions} pts")
            logger.info(f"Git Violations: {len(git_violations)}")
        
        except Exception as e:
            logger.warning(f"Git history scan failed: {e}")
        
        logger.group_end()
    
    # Print summary
    logger.info("")
    reporter.print_summary(
        score=score,
        threshold=threshold,
        starting_score=STARTING_SCORE,
        violations=violations,
        files_scanned=code_scanner.files_scanned,
        brutal_mode=brutal_mode
    )
    
    # Write GitHub outputs
    reporter.write_job_summary(
        score=score,
        threshold=threshold,
        starting_score=STARTING_SCORE,
        violations=violations
    )
    
    reporter.write_github_output(score)
    
    # Determine exit code
    if score < threshold:
        logger.error("")
        logger.error(f"❌ VibeGuard FAILED: Score {score} is below threshold {threshold}")
        logger.error("Vibecoding detected! Clean up the code and try again.")
        return 1
    else:
        logger.info("")
        logger.info(f"✅ VibeGuard PASSED: Score {score} meets threshold {threshold}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
