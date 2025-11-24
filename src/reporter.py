"""
Reporter Module
Handles output formatting, GitHub annotations, and job summaries
"""

import os
from typing import List, Dict, Any
from collections import defaultdict


class Reporter:
    """Formats and outputs scan results"""
    
    CATEGORY_NAMES = {
        'security': '🔒 Security',
        'stability': '⚡ Stability',
        'maintainability': '🔧 Maintainability',
        'hygiene': '🧹 Code Hygiene',
        'code_smell': '👃 Code Smells',
        'testing': '🧪 Testing',
        'performance': '⚡ Performance',
        'documentation': '📝 Documentation',
        'dependencies': '📦 Dependencies',
        'vcs': '🌿 Version Control',
        'naming': '🏷️  Naming',
        'ux': '🎨 UI/UX',
        'ai_slop': '🤖 AI Slop',
        'react': '⚛️  React',
        'git': '🌿 Git Hygiene'
    }
    
    def __init__(self, logger=None):
        """
        Initialize the reporter
        
        Args:
            logger: Logger instance for structured logging
        """
        self.logger = logger
    
    def print_github_annotation(self, violation: Dict[str, Any], 
                               level: str = "warning") -> None:
        """
        Print GitHub Actions annotation
        
        Args:
            violation: Violation dictionary
            level: Annotation level ('error', 'warning', or 'notice')
        """
        file = violation.get('file', '')
        line = violation.get('line', '')
        rule_id = violation.get('id', '')
        rule_name = violation.get('rule', '')
        deduction = violation.get('deduction', 0)
        
        if line:
            location = f"file={file},line={line}"
        else:
            location = f"file={file}"
        
        message = f"[{rule_id}] {rule_name} (-{deduction} pts)"
        print(f"::{level} {location}::{message}")
    
    def write_job_summary(self, score: int, threshold: int, 
                         starting_score: int, violations: List[Dict[str, Any]]) -> None:
        """
        Write GitHub Actions job summary in Markdown format
        
        Args:
            score: Final score
            threshold: Required threshold
            starting_score: Starting score (usually 1000)
            violations: List of violation dictionaries
        """
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_file:
            return
        
        status_emoji = "✅" if score >= threshold else "❌"
        status_text = "PASSED" if score >= threshold else "FAILED"
        
        # Create progress bar
        bar_width = 20
        bar_filled = int((score / starting_score) * bar_width)
        progress_bar = "█" * bar_filled + "░" * (bar_width - bar_filled)
        
        md = f"""# {status_emoji} VibeGuard Code Quality Report

## 📊 Final Score

**Score:** `{score}/{starting_score}` {progress_bar}  
**Threshold:** `{threshold}`  
**Status:** **{status_text}**

---

## 📉 Violations Detected ({len(violations)})

"""
        
        if violations:
            # Group by category
            categories = defaultdict(list)
            for v in violations:
                rule_id = v['id']
                # Extract category from rule ID (first 3 chars) or use 'git' for GIT rules
                if rule_id.startswith('GIT'):
                    category = 'git'
                else:
                    # Map rule prefix to category
                    category = self._get_category_from_rule_id(rule_id)
                categories[category].append(v)
            
            for cat_id in sorted(categories.keys()):
                cat_name = self.CATEGORY_NAMES.get(cat_id, cat_id.title())
                cat_violations = categories[cat_id]
                cat_total = sum(v['deduction'] for v in cat_violations)
                
                md += f"### {cat_name} (-{cat_total} pts)\n\n"
                md += "| File | Rule | Line | Penalty |\n"
                md += "|------|------|------|--------:|\n"
                
                for v in cat_violations[:10]:  # Limit to 10 per category
                    file_display = v['file'][:50] + "..." if len(v['file']) > 50 else v['file']
                    line_info = f"L{v['line']}" if 'line' in v and v['line'] else "-"
                    md += f"| `{file_display}` | {v['rule']} | {line_info} | -{v['deduction']} |\n"
                
                if len(cat_violations) > 10:
                    md += f"| ... | *{len(cat_violations) - 10} more violations* | ... | ... |\n"
                
                md += "\n"
        else:
            md += "### 🎉 No violations found!\n\n"
            md += "Your code is **pristine**. Perfect SOTA engineering vibes. 🚀\n\n"
        
        md += "---\n\n"
        md += f"*Scanned with VibeGuard Auditor • Threshold: {threshold} • [Learn More](https://github.com/fabriziosalmi/vibe-check)*\n"
        
        with open(summary_file, "a") as f:
            f.write(md)
    
    def _get_category_from_rule_id(self, rule_id: str) -> str:
        """Map rule ID prefix to category"""
        prefix_map = {
            'SEC': 'security',
            'STB': 'stability',
            'MNT': 'maintainability',
            'HYG': 'hygiene',
            'SME': 'code_smell',
            'TST': 'testing',
            'PRF': 'performance',
            'DOC': 'documentation',
            'DEP': 'dependencies',
            'VCS': 'vcs',
            'NAM': 'naming',
            'UX': 'ux',
            'AI': 'ai_slop',
            'RCT': 'react',
            'GIT': 'git'
        }
        prefix = rule_id[:3]
        return prefix_map.get(prefix, 'other')
    
    def write_github_output(self, score: int) -> None:
        """
        Write score to GitHub Actions output
        
        Args:
            score: Final score to output
        """
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"score={score}\n")
    
    def print_summary(self, score: int, threshold: int, starting_score: int,
                     violations: List[Dict[str, Any]], files_scanned: int,
                     brutal_mode: bool = False) -> None:
        """
        Print human-readable summary to console
        
        Args:
            score: Final score
            threshold: Required threshold
            starting_score: Starting score
            violations: List of violations
            files_scanned: Number of files scanned
            brutal_mode: Whether brutal mode was enabled
        """
        mode_indicator = "🔥 BRUTAL MODE" if brutal_mode else "Standard Mode"
        
        if self.logger:
            self.logger.info(f"=== VibeGuard Scan Complete ({mode_indicator}) ===")
            self.logger.info(f"Files Scanned: {files_scanned}")
            self.logger.info(f"Total Violations: {len(violations)}")
            self.logger.info(f"Total Deductions: {starting_score - score} pts")
            self.logger.info(f"Final Score: {score}/{starting_score}")
            self.logger.info(f"Threshold: {threshold}")
            
            if score >= threshold:
                self.logger.info(f"✅ PASSED - Score meets threshold")
            else:
                self.logger.error(f"❌ FAILED - Score below threshold")
        else:
            print(f"\n=== VibeGuard Scan Complete ({mode_indicator}) ===")
            print(f"📁 Files Scanned: {files_scanned}")
            print(f"⚠️  Total Violations: {len(violations)}")
            print(f"📉 Total Deductions: {starting_score - score} pts")
            print(f"📊 Final Score: {score}/{starting_score}")
            print(f"🎯 Threshold: {threshold}")
            
            if score >= threshold:
                print(f"✅ VibeGuard PASSED: Score {score} meets threshold {threshold}")
            else:
                print(f"❌ VibeGuard FAILED: Score {score} is below threshold {threshold}")
                print(f"Vibecoding detected! Clean up the code and try again.")
    
    def print_violations_by_category(self, violations: List[Dict[str, Any]]) -> None:
        """
        Print violations grouped by category
        
        Args:
            violations: List of violation dictionaries
        """
        categories = defaultdict(list)
        for v in violations:
            category = self._get_category_from_rule_id(v['id'])
            categories[category].append(v)
        
        for cat_id in sorted(categories.keys()):
            cat_name = self.CATEGORY_NAMES.get(cat_id, cat_id.title())
            cat_violations = categories[cat_id]
            cat_total = sum(v['deduction'] for v in cat_violations)
            
            print(f"\n{cat_name} (-{cat_total} pts):")
            for v in cat_violations[:5]:  # Show top 5
                line_info = f" (L{v['line']})" if 'line' in v and v['line'] else ""
                print(f"  • {v['file']}{line_info}: {v['rule']} (-{v['deduction']} pts)")
            
            if len(cat_violations) > 5:
                print(f"  ... and {len(cat_violations) - 5} more")
