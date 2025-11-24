"""
Scanner Module
Handles file scanning, AST parsing, and violation detection
"""

import os
import re
import ast
import subprocess
from typing import List, Dict, Any, Tuple
from pathlib import Path


class Violation:
    """Represents a single code violation"""
    
    def __init__(self, file: str, rule_id: str, rule_name: str, 
                 deduction: int, desc: str, line: int = None):
        self.file = file
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.deduction = deduction
        self.desc = desc
        self.line = line
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'file': self.file,
            'id': self.rule_id,
            'rule': self.rule_name,
            'deduction': self.deduction,
            'desc': self.desc
        }
        if self.line:
            result['line'] = self.line
        return result


class CodeScanner:
    """Scans files for code quality violations"""
    
    # Directories to ignore during scanning
    IGNORE_DIRS = {'.git', '.github', 'node_modules', 'dist', 'build', 
                   'venv', '__pycache__', '.venv', 'vendor', '.pytest_cache'}
    
    # Files to ignore during scanning
    IGNORE_FILES = {'package-lock.json', 'yarn.lock', 'poetry.lock', 
                    'Cargo.lock', 'go.sum', 'pnpm-lock.yaml'}
    
    # Extensions to scan for content
    TEXT_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', 
                      '.c', '.cpp', '.h', '.rb', '.php', '.html', '.css', 
                      '.scss', '.sass', '.vue', '.svelte', '.md', '.txt', 
                      '.yml', '.yaml', '.json', '.xml', '.sh', '.bash'}
    
    def __init__(self, rules_manager, exclude_patterns: List[str] = None, logger=None):
        """
        Initialize the code scanner
        
        Args:
            rules_manager: RulesManager instance
            exclude_patterns: List of regex patterns for files to exclude
            logger: Logger instance for structured logging
        """
        self.rules_manager = rules_manager
        self.exclude_patterns = exclude_patterns or []
        self.logger = logger
        self.violations: List[Violation] = []
        self.files_scanned = 0
    
    def is_excluded(self, filepath: str) -> bool:
        """
        Check if file matches exclusion patterns
        
        Args:
            filepath: Path to check
        
        Returns:
            True if file should be excluded
        """
        for pattern in self.exclude_patterns:
            if re.match(pattern.replace('*', '.*'), filepath):
                return True
        return False
    
    def is_comment_line(self, line: str, file_ext: str) -> bool:
        """
        Detect if a line is a comment based on file type
        
        Args:
            line: Line of code to check
            file_ext: File extension
        
        Returns:
            True if line is a comment
        """
        stripped = line.strip()
        if file_ext in ['.py', '.sh', '.bash', '.yml', '.yaml']:
            return stripped.startswith('#')
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.go']:
            return stripped.startswith('//') or stripped.startswith('*')
        return False
    
    def has_ignore_comment(self, line: str, next_line: str = None) -> bool:
        """
        Check if line has a vibeguard:ignore comment
        
        Args:
            line: Current line
            next_line: Next line (for checking inline ignores)
        
        Returns:
            True if violation should be ignored
        """
        # Check for inline ignore: code  # vibeguard:ignore
        if 'vibeguard:ignore' in line or 'vibeguard: ignore' in line:
            return True
        
        # Check for next-line ignore
        if next_line and ('vibeguard:ignore' in next_line or 'vibeguard: ignore' in next_line):
            return True
        
        return False
    
    def check_python_ast_violations(self, filepath: str, content: str, 
                                    brutal_mode: bool = False) -> List[Violation]:
        """
        Use AST to detect Python-specific violations with precision
        
        Args:
            filepath: Path to Python file
            content: File contents
            brutal_mode: Whether brutal mode is enabled
        
        Returns:
            List of Violation objects
        """
        violations = []
        try:
            tree = ast.parse(content)
            lines = content.splitlines()
            
            for node in ast.walk(tree):
                # Detect eval() usage
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == 'eval':
                        # Check for ignore comment
                        line_num = node.lineno
                        current_line = lines[line_num - 1] if line_num <= len(lines) else ""
                        next_line = lines[line_num] if line_num < len(lines) else ""
                        
                        if not self.has_ignore_comment(current_line, next_line):
                            rule = self.rules_manager.get_rule_by_id('SEC06')
                            if rule:
                                penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                                violations.append(Violation(
                                    file=filepath,
                                    rule_id='SEC06',
                                    rule_name=rule['name'],
                                    deduction=penalty,
                                    desc='Real eval() call detected via AST',
                                    line=line_num
                                ))
                    
                    # Detect print() in non-test files
                    elif node.func.id == 'print' and 'test' not in filepath.lower():
                        line_num = node.lineno
                        current_line = lines[line_num - 1] if line_num <= len(lines) else ""
                        next_line = lines[line_num] if line_num < len(lines) else ""
                        
                        if not self.has_ignore_comment(current_line, next_line):
                            rule = self.rules_manager.get_rule_by_id('HYG02')
                            if rule:
                                penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                                violations.append(Violation(
                                    file=filepath,
                                    rule_id='HYG02',
                                    rule_name=rule['name'],
                                    deduction=penalty,
                                    desc='Print statement in production code',
                                    line=line_num
                                ))
        
        except SyntaxError:
            # Ignore syntax errors - regex will still catch some issues
            pass
        
        return violations
    
    def scan_file(self, filepath: str, brutal_mode: bool = False) -> List[Violation]:
        """
        Scan a single file for violations
        
        Args:
            filepath: Path to file to scan
            brutal_mode: Whether brutal mode is enabled
        
        Returns:
            List of Violation objects
        """
        violations = []
        filename = os.path.basename(filepath)
        file_ext = os.path.splitext(filename)[1]
        
        # Check filename rules
        for rule in self.rules_manager.get_rules_by_type('filename'):
            if re.search(rule['pattern'], filename):
                penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                violations.append(Violation(
                    file=filepath,
                    rule_id=rule['id'],
                    rule_name=rule['name'],
                    deduction=penalty,
                    desc=rule['desc']
                ))
        
        # Check path rules
        for rule in self.rules_manager.get_rules_by_type('path'):
            if re.search(rule['pattern'], filepath):
                penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                violations.append(Violation(
                    file=filepath,
                    rule_id=rule['id'],
                    rule_name=rule['name'],
                    deduction=penalty,
                    desc=rule['desc']
                ))
        
        # Check content for text files
        if file_ext in self.TEXT_EXTENSIONS:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.splitlines()
                    self.files_scanned += 1
                    
                    # Python AST analysis for precision
                    if file_ext == '.py':
                        ast_violations = self.check_python_ast_violations(
                            filepath, content, brutal_mode
                        )
                        violations.extend(ast_violations)
                    
                    # Check line count
                    for rule in self.rules_manager.get_rules_by_type('lines'):
                        max_lines = rule.get('max', float('inf'))
                        if len(lines) > max_lines:
                            penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                            violations.append(Violation(
                                file=filepath,
                                rule_id=rule['id'],
                                rule_name=f"{rule['name']} ({len(lines)} lines)",
                                deduction=penalty,
                                desc=rule['desc']
                            ))
                    
                    # Check EOF newline
                    for rule in self.rules_manager.get_rules_by_type('eof'):
                        if content and not content.endswith('\n'):
                            penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                            violations.append(Violation(
                                file=filepath,
                                rule_id=rule['id'],
                                rule_name=rule['name'],
                                deduction=penalty,
                                desc=rule['desc']
                            ))
                    
                    # Check regex patterns with smart comment detection
                    for rule in self.rules_manager.get_rules_by_type('regex'):
                        pattern = rule['pattern']
                        matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
                        
                        for match in matches[:3]:  # Limit to 3 matches per rule per file
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                            
                            # Check for ignore comment
                            next_line = lines[line_num] if line_num < len(lines) else ""
                            if self.has_ignore_comment(line_content, next_line):
                                continue
                            
                            # Smart filtering: Skip code-related rules if line is a comment
                            is_comment = self.is_comment_line(line_content, file_ext)
                            if is_comment and not rule['id'].startswith(('DOC', 'STB03', 'STB04', 'STB05')):
                                continue
                            
                            penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                            violations.append(Violation(
                                file=filepath,
                                rule_id=rule['id'],
                                rule_name=rule['name'],
                                deduction=penalty,
                                desc=rule['desc'],
                                line=line_num
                            ))
            
            except Exception:
                # Skip binary files or permission errors
                pass
        
        return violations
    
    def scan_directory(self, root_dir: str = '.', brutal_mode: bool = False) -> List[Violation]:
        """
        Recursively scan a directory for violations
        
        Args:
            root_dir: Root directory to scan
            brutal_mode: Whether brutal mode is enabled
        
        Returns:
            List of all Violation objects found
        """
        self.violations = []
        self.files_scanned = 0
        
        for root, dirs, files in os.walk(root_dir):
            # Filter directories to ignore
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                if file in self.IGNORE_FILES:
                    continue
                
                filepath = os.path.relpath(os.path.join(root, file))
                
                # Check exclusion patterns
                if self.is_excluded(filepath):
                    continue
                
                file_violations = self.scan_file(filepath, brutal_mode)
                self.violations.extend(file_violations)
        
        return self.violations


class GitScanner:
    """Scans git history for behavioral anti-patterns"""
    
    def __init__(self, rules_manager, logger=None):
        """
        Initialize git scanner
        
        Args:
            rules_manager: RulesManager instance
            logger: Logger instance for structured logging
        """
        self.rules_manager = rules_manager
        self.logger = logger
    
    def scan_history(self, brutal_mode: bool = False, 
                    commit_limit: int = 50) -> Tuple[int, List[Dict]]:
        """
        Analyze git commit history for anti-patterns
        
        Args:
            brutal_mode: Whether brutal mode is enabled
            commit_limit: Number of commits to analyze
        
        Returns:
            Tuple of (total_deductions, violations_list)
        """
        violations = []
        total_deductions = 0
        
        # Check if .git directory exists
        if not os.path.isdir('.git'):
            if self.logger:
                self.logger.warning("Git history audit skipped (no .git directory found)")
            return 0, []
        
        try:
            # Fix GitHub Actions dubious ownership issue
            subprocess.run(
                ['git', 'config', '--global', '--add', 'safe.directory', '*'],
                capture_output=True,
                timeout=5
            )
            
            # Get commit history
            result = subprocess.run(
                ['git', 'log', '-n', str(commit_limit), 
                 '--pretty=format:%H|%an|%cd|%s', '--date=format:%a %H:%M'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                if self.logger:
                    self.logger.warning(f"Git history audit skipped: {result.stderr[:100]}")
                return 0, []
            
            commits = result.stdout.strip().split('\n')
            
            if not commits or len(commits) <= 1 or commits[0] == '':
                if self.logger:
                    self.logger.warning("Git history audit skipped (insufficient commit history)")
                return 0, []
            
            # Analyze commits
            violations, total_deductions = self._analyze_commits(commits, brutal_mode)
        
        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.warning("Git history audit timed out")
        except FileNotFoundError:
            if self.logger:
                self.logger.warning("Git not found, skipping history audit")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Git history audit failed: {e}")
        
        return total_deductions, violations
    
    def _analyze_commits(self, commits: List[str], brutal_mode: bool) -> Tuple[List[Dict], int]:
        """Analyze commit messages and metadata"""
        violations = []
        total_deductions = 0
        
        # Patterns for lazy commits
        lazy_patterns = [
            r'^(wip|fix|test|asdasd|asd|tmp|temp|debug|update|changes)$',
            r'^(merge|rebase|commit|push)$',
            r'^\.$',
            r'^[0-9]+$',
        ]
        
        # Unprofessional keywords
        unpro_keywords = ['oops', 'lol', 'yolo', 'fml', 'wtf', 'fuck', 
                         'shit', 'hope this works', 'fingers crossed', 'idk']
        
        for commit_line in commits:
            if not commit_line:
                continue
            
            parts = commit_line.split('|')
            if len(parts) < 4:
                continue
            
            commit_hash = parts[0][:7]
            author = parts[1]
            date_str = parts[2]
            message = parts[3].lower()
            
            # GIT01: Lazy commit message
            for pattern in lazy_patterns:
                if re.match(pattern, message, re.IGNORECASE):
                    rule = self.rules_manager.get_rule_by_id('GIT01')
                    if rule:
                        penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                        total_deductions += penalty
                        violations.append({
                            "file": f"commit {commit_hash}",
                            "rule": rule['name'],
                            "id": rule['id'],
                            "deduction": penalty,
                            "desc": f"'{message[:50]}' provides zero context"
                        })
                    break
            
            # GIT02: Revert war
            if 'revert "revert' in message:
                rule = self.rules_manager.get_rule_by_id('GIT02')
                if rule:
                    penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                    total_deductions += penalty
                    violations.append({
                        "file": f"commit {commit_hash}",
                        "rule": rule['name'],
                        "id": rule['id'],
                        "deduction": penalty,
                        "desc": "Reverting a revert indicates chaos"
                    })
            
            # GIT03: Unprofessional commit
            for keyword in unpro_keywords:
                if keyword in message:
                    rule = self.rules_manager.get_rule_by_id('GIT03')
                    if rule:
                        penalty = self.rules_manager.calculate_penalty(rule, brutal_mode)
                        total_deductions += penalty
                        violations.append({
                            "file": f"commit {commit_hash}",
                            "rule": rule['name'],
                            "id": rule['id'],
                            "deduction": penalty,
                            "desc": f"Contains '{keyword}'"
                        })
                    break
        
        return violations, total_deductions
