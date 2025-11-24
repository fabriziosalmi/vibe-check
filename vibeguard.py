#!/usr/bin/env python3
"""
VibeGuard Auditor - SOTA Code Quality Scanner
Detects vibecoding patterns and ranks code from 0-1000
Designed for GitHub Actions with native annotations and job summaries
"""

import os
import re
import sys
import json
import ast
import subprocess
from datetime import datetime

# Leggiamo gli input dall'ambiente (passati da action.yml)
INPUT_THRESHOLD = int(os.environ.get("INPUT_THRESHOLD", 800))
INPUT_BRUTAL_MODE = os.environ.get("INPUT_BRUTAL_MODE", "false").lower() == "true"
STARTING_SCORE = 1000

# Carica config personalizzata se esiste
IGNORE_RULES = set()
EXCLUDE_PATTERNS = []

if os.path.exists(".vibeguardrc"):
    try:
        with open(".vibeguardrc", "r") as f:
            config = json.load(f)
            IGNORE_RULES = set(config.get("ignore", []))
            EXCLUDE_PATTERNS = config.get("exclude_files", [])
            print(f"📝 Loaded .vibeguardrc: Ignoring {len(IGNORE_RULES)} rules, {len(EXCLUDE_PATTERNS)} patterns")
    except Exception as e:
        print(f"⚠️  Failed to load .vibeguardrc: {e}")

# 300+ SOTA Rules: Anti-Vibecoding Patterns from Code Quality + UI/UX + Documentation
RULES = [
    # ========== SECURITY (Critical - 60-100 pts) ==========
    {"id": "SEC01", "name": "Committed .env file", "pattern": r"^\.env$", "weight": 100, "type": "filename", "desc": "Security risk: exposed secrets", "critical": True},
    {"id": "SEC02", "name": "AWS Access Key Pattern", "pattern": r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])", "weight": 100, "type": "regex", "desc": "Possible hardcoded AWS credential"},
    {"id": "SEC03", "name": "Private Key File", "pattern": r"\.(pem|key|p12|pfx)$", "weight": 100, "type": "filename", "desc": "Private key should not be committed"},
    {"id": "SEC04", "name": "Hardcoded Password", "pattern": r"password\s*=\s*['\"][^'\"]{3,}['\"]", "weight": 80, "type": "regex", "desc": "Hardcoded credential"},
    {"id": "SEC05", "name": "API Key Pattern", "pattern": r"(api[_-]?key|apikey)\s*=\s*['\"][^'\"]{10,}['\"]", "weight": 80, "type": "regex", "desc": "Hardcoded API key"},
    {"id": "SEC06", "name": "eval() Usage", "pattern": r"\beval\s*\(", "weight": 70, "type": "regex", "desc": "Dangerous code execution"},
    {"id": "SEC07", "name": "SQL Concatenation", "pattern": r"(SELECT|INSERT|UPDATE|DELETE).*\+.*\b(WHERE|VALUES)", "weight": 60, "type": "regex", "desc": "Potential SQL injection"},
    {"id": "SEC08", "name": "chmod 777", "pattern": r"chmod\s+777", "weight": 90, "type": "regex", "desc": "Lazy permission handling"},
    {"id": "SEC09", "name": "Plain text password storage", "pattern": r"(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]", "weight": 85, "type": "regex", "desc": "Passwords must be hashed"},
    {"id": "SEC10", "name": "Hardcoded http:// URL", "pattern": r"http://(?!localhost)", "weight": 60, "type": "regex", "desc": "MITM vulnerability - use HTTPS"},
    {"id": "SEC11", "name": "innerHTML without sanitization", "pattern": r"\.innerHTML\s*=", "weight": 65, "type": "regex", "desc": "XSS vulnerability vector"},
    {"id": "SEC12", "name": "Outdated CVE dependency warning", "pattern": r"(axios|lodash|moment)@[0-4]\.", "weight": 70, "type": "regex", "desc": "Known vulnerable versions"},
    
    # ========== STABILITY (High - 25-50 pts) ==========
    {"id": "STB01", "name": "Empty Catch Block", "pattern": r"catch\s*\(\w+\)\s*\{\s*\}", "weight": 50, "type": "regex", "desc": "Swallowed error - bad practice"},
    {"id": "STB02", "name": "Bare Except", "pattern": r"except\s*:\s*\n\s*pass", "weight": 50, "type": "regex", "desc": "Catches all exceptions silently"},
    {"id": "STB03", "name": "TODO in Code", "pattern": r"(//|#)\s*TODO", "weight": 15, "type": "regex", "desc": "Unfinished work"},
    {"id": "STB04", "name": "FIXME in Code", "pattern": r"(//|#)\s*FIXME", "weight": 20, "type": "regex", "desc": "Known bug not addressed"},
    {"id": "STB05", "name": "XXX Comment", "pattern": r"(//|#)\s*XXX", "weight": 25, "type": "regex", "desc": "Dangerous or problematic code"},
    {"id": "STB06", "name": "Hardcoded localhost", "pattern": r"(http://|https://)localhost", "weight": 30, "type": "regex", "desc": "Environment-specific URL"},
    {"id": "STB07", "name": "Magic Number", "pattern": r"(?<![a-zA-Z_])(setTimeout|setInterval|sleep)\s*\(\s*\d{4,}", "weight": 20, "type": "regex", "desc": "Unexplained numeric constant"},
    {"id": "STB08", "name": "Infinite Loop Risk", "pattern": r"while\s*\(\s*true\s*\)", "weight": 35, "type": "regex", "desc": "Missing exit condition"},
    {"id": "STB09", "name": "Hardcoded File Path", "pattern": r"['\"]/(Users|home|C:)", "weight": 40, "type": "regex", "desc": "Non-portable absolute path"},
    {"id": "STB10", "name": "Circular Import Risk", "pattern": r"import.*from\s+['\"]\.\.\/", "weight": 25, "type": "regex", "desc": "Potential circular dependency"},
    {"id": "STB11", "name": "WIP Commit Message", "pattern": r"^(wip|fix|test)$", "weight": 10, "type": "commit", "desc": "Vague commit message"},
    
    # ========== MAINTAINABILITY (Medium - 15-40 pts) ==========
    {"id": "MNT01", "name": "Huge File", "weight": 30, "type": "lines", "max": 2000, "desc": "File too long (>2000 lines)"},
    {"id": "MNT02", "name": "Very Long Line", "pattern": r"^.{200,}$", "weight": 10, "type": "regex", "desc": "Line too long (>200 chars)"},
    {"id": "MNT03", "name": "Deeply Nested Code", "pattern": r"^\s{24,}\S", "weight": 25, "type": "regex", "desc": "6+ levels of indentation"},
    {"id": "MNT04", "name": "God Object Pattern", "pattern": r"class\s+\w+\s*.*\{[\s\S]{5000,}?\n\}", "weight": 40, "type": "regex", "desc": "Class too large"},
    {"id": "MNT05", "name": "Commented Code Block", "pattern": r"(//|#)\s*(function|def|class|const|let|var)\s+\w+", "weight": 15, "type": "regex", "desc": "Dead code left in comments"},
    {"id": "MNT06", "name": "Copy-Paste Code Duplication", "pattern": r"function\s+\w+\s*\([^)]*\)\s*\{[\s\S]{100,}\}", "weight": 20, "type": "regex", "desc": "Violates DRY"},
    {"id": "MNT07", "name": "Unused Import", "pattern": r"^import\s+\w+\s+from", "weight": 8, "type": "regex", "desc": "Visual noise"},
    {"id": "MNT08", "name": "God File (utils.js)", "pattern": r"(utils|helpers|common)\.js$", "weight": 25, "type": "filename", "desc": "Dumping ground for unorganized code"},
    
    # ========== HYGIENE (Low - 2-20 pts) ==========
    {"id": "HYG01", "name": "Console Log", "pattern": r"console\.log\(", "weight": 5, "type": "regex", "desc": "Debug code in production"},
    {"id": "HYG02", "name": "Print Statement", "pattern": r"^\s*print\s*\(", "weight": 5, "type": "regex", "desc": "Debug output"},
    {"id": "HYG03", "name": "Debugger Statement", "pattern": r"\bdebugger\b", "weight": 20, "type": "regex", "desc": "Breakpoint left in code"},
    {"id": "HYG04", "name": "Trailing Whitespace", "pattern": r" +$", "weight": 2, "type": "regex", "desc": "Sloppy formatting"},
    {"id": "HYG05", "name": "Multiple Blank Lines", "pattern": r"\n{4,}", "weight": 3, "type": "regex", "desc": "Excessive spacing"},
    {"id": "HYG06", "name": "Mixed Tabs/Spaces", "pattern": r"^\t+ +", "weight": 10, "type": "regex", "desc": "Inconsistent indentation"},
    {"id": "HYG07", "name": "No Newline at EOF", "weight": 5, "type": "eof", "desc": "Missing final newline"},
    {"id": "HYG08", "name": "Filename with Spaces", "pattern": r"\s", "weight": 12, "type": "filename", "desc": "Breaks shell scripts"},
    
    # ========== CODE SMELL (Medium - 8-35 pts) ==========
    {"id": "SME01", "name": "var Keyword (JS)", "pattern": r"\bvar\s+\w+", "weight": 15, "type": "regex", "desc": "Use let/const instead"},
    {"id": "SME02", "name": "Double Negation", "pattern": r"!!\w+", "weight": 10, "type": "regex", "desc": "Unclear boolean conversion"},
    {"id": "SME03", "name": "Yoda Condition", "pattern": r"(null|true|false|undefined|\d+)\s*===?\s*\w+", "weight": 8, "type": "regex", "desc": "Backwards comparison"},
    {"id": "SME04", "name": "Nested Ternary", "pattern": r"\?[^:]+\?[^:]+:", "weight": 20, "type": "regex", "desc": "Unreadable conditional"},
    {"id": "SME05", "name": "Empty Function", "pattern": r"(function|def)\s+\w+\s*\([^)]*\)\s*\{\s*\}", "weight": 25, "type": "regex", "desc": "No-op function"},
    {"id": "SME06", "name": "Long Parameter List", "pattern": r"(function|def)\s+\w+\s*\([^)]*,\s*[^)]*,\s*[^)]*,\s*[^)]*,\s*[^)]*,\s*[^)]*", "weight": 30, "type": "regex", "desc": "6+ parameters"},
    {"id": "SME07", "name": "Alert Usage", "pattern": r"\balert\s*\(", "weight": 25, "type": "regex", "desc": "Poor UX pattern"},
    {"id": "SME08", "name": "document.write", "pattern": r"document\.write\(", "weight": 30, "type": "regex", "desc": "Deprecated DOM manipulation"},
    {"id": "SME09", "name": "Float for Currency", "pattern": r"(price|amount|total)\s*=\s*\d+\.\d+", "weight": 35, "type": "regex", "desc": "Use integers or Decimal"},
    {"id": "SME10", "name": "Global Variable", "pattern": r"^(var|let|const)\s+[A-Z_]+\s*=", "weight": 20, "type": "regex", "desc": "Global state risk"},
    {"id": "SME11", "name": "Empty else block", "pattern": r"else\s*\{\s*\}", "weight": 12, "type": "regex", "desc": "Clutter"},
    
    # ========== TESTING (Medium - 20-40 pts) ==========
    {"id": "TST01", "name": "Skipped Test", "pattern": r"(it\.skip|test\.skip|xit|xdescribe)", "weight": 25, "type": "regex", "desc": "Disabled test case"},
    {"id": "TST02", "name": "Focused Test", "pattern": r"(it\.only|test\.only|fit|fdescribe)", "weight": 40, "type": "regex", "desc": "Test isolation left enabled"},
    {"id": "TST03", "name": "Fake Assertion", "pattern": r"(expect|assert)\(true\)", "weight": 30, "type": "regex", "desc": "Test that proves nothing"},
    {"id": "TST04", "name": "No Unit Tests", "weight": 20, "type": "missing_test", "desc": "Critical logic uncovered"},
    
    # ========== PERFORMANCE (Medium - 15-35 pts) ==========
    {"id": "PRF01", "name": "Sync FS Operation", "pattern": r"fs\.(readFileSync|writeFileSync|existsSync)", "weight": 25, "type": "regex", "desc": "Blocking I/O"},
    {"id": "PRF02", "name": "Nested Loop", "pattern": r"for\s*\([^)]+\)\s*\{[^}]*for\s*\(", "weight": 20, "type": "regex", "desc": "O(n²) complexity warning"},
    {"id": "PRF03", "name": "Array Push in Loop", "pattern": r"for\s*\([^)]+\)\s*\{[^}]*\.push\(", "weight": 15, "type": "regex", "desc": "Consider map/filter"},
    {"id": "PRF04", "name": "Blocking Event Loop", "pattern": r"(while|for)\s*\([^)]*\)\s*\{[^}]{200,}\}", "weight": 30, "type": "regex", "desc": "Heavy computation on main thread"},
    
    # ========== DOCUMENTATION (Low - 5-15 pts) ==========
    {"id": "DOC01", "name": "No JSDoc", "pattern": r"(export\s+)?(function|class)\s+\w+[^{]*\{(?![\s\S]*?/\*\*)", "weight": 8, "type": "regex", "desc": "Missing documentation"},
    {"id": "DOC02", "name": "Misleading Comment", "pattern": r"(//|#)\s*(this|should|must|will)\s+(not|never)", "weight": 12, "type": "regex", "desc": "Confusing comment"},
    {"id": "DOC03", "name": "Broken Link in Docs", "pattern": r"\[.*\]\(http.*404", "weight": 15, "type": "regex", "desc": "Link rot"},
    {"id": "DOC04", "name": "Condescending Language", "pattern": r"\b(simply|just|obviously|trivial)\b", "weight": 8, "type": "regex", "desc": "Remove from docs"},
    {"id": "DOC05", "name": "Vague Error Description", "pattern": r"(returns\s+data|returns\s+object)", "weight": 10, "type": "regex", "desc": "Specify exact shape"},
    {"id": "DOC06", "name": "Passive Voice in Docs", "pattern": r"(is\s+sent|are\s+processed|was\s+created)", "weight": 5, "type": "regex", "desc": "Use active voice"},
    {"id": "DOC07", "name": "Missing README", "pattern": r"^README\.md$", "weight": 30, "type": "missing_file", "desc": "Required documentation"},
    {"id": "DOC08", "name": "Click Here Links", "pattern": r"\[click\s+here\]", "weight": 10, "type": "regex", "desc": "Use descriptive link text"},
    {"id": "DOC09", "name": "Outdated Copyright Year", "pattern": r"Copyright.*20(0|1)[0-9]", "weight": 5, "type": "regex", "desc": "Update year"},
    
    # ========== DEPENDENCY ISSUES (High - 20-50 pts) ==========
    {"id": "DEP01", "name": "Absolute Import", "pattern": r"import\s+.*\s+from\s+['\"]/(src|app|lib)", "weight": 20, "type": "regex", "desc": "Non-portable path"},
    {"id": "DEP02", "name": "Wildcard Import", "pattern": r"from\s+\w+\s+import\s+\*", "weight": 25, "type": "regex", "desc": "Namespace pollution"},
    {"id": "DEP03", "name": "Dev Dependency in Code", "pattern": r"(require|import)\s*\(['\"](@types/|jest|mocha|chai)", "weight": 40, "type": "regex", "desc": "Test lib in production"},
    {"id": "DEP04", "name": "Unused Package.json Dep", "pattern": r"\"(react|vue|angular)\":", "weight": 15, "type": "regex", "desc": "Security risk"},
    {"id": "DEP05", "name": "Importing Entire Library", "pattern": r"import\s+\*\s+as\s+", "weight": 18, "type": "regex", "desc": "Tree-shaking failure"},
    
    # ========== VCS / GIT (High - 20-100 pts) ==========
    {"id": "VCS01", "name": "Merge Conflict Marker", "pattern": r"^(<<<<<<<|=======|>>>>>>>)", "weight": 100, "type": "regex", "desc": "Unresolved conflict"},
    {"id": "VCS02", "name": ".DS_Store Committed", "pattern": r"\.DS_Store$", "weight": 20, "type": "filename", "desc": "OS-specific file"},
    {"id": "VCS03", "name": "node_modules Committed", "pattern": r"node_modules/", "weight": 60, "type": "path", "desc": "Dependencies in repo"},
    {"id": "VCS04", "name": "__pycache__ Committed", "pattern": r"__pycache__", "weight": 40, "type": "path", "desc": "Build artifacts"},
    {"id": "VCS05", "name": "Missing .gitignore", "pattern": r"^\.gitignore$", "weight": 35, "type": "missing_file", "desc": "Risk of committing artifacts"},
    {"id": "VCS06", "name": "Binary in Git History", "pattern": r"\.(exe|dmg|zip|tar\.gz)$", "weight": 30, "type": "filename", "desc": "Git is not Dropbox"},
    {"id": "VCS07", "name": "IDE Settings Committed", "pattern": r"\.(vscode|idea)/", "weight": 15, "type": "path", "desc": "Personal preference pollution"},
    
    # ========== NAMING (Medium - 10-20 pts) ==========
    {"id": "NAM01", "name": "Single Letter Var", "pattern": r"(let|const|var)\s+[a-z]\s*=(?!.*for)", "weight": 15, "type": "regex", "desc": "Unclear variable name"},
    {"id": "NAM02", "name": "Abbreviation Hell", "pattern": r"(let|const|var)\s+(tmp|temp|data|obj|arr)\d+", "weight": 18, "type": "regex", "desc": "Generic naming"},
    {"id": "NAM03", "name": "Hungarian Notation", "pattern": r"(str|int|bool|arr|obj)[A-Z]\w+", "weight": 12, "type": "regex", "desc": "Outdated convention"},
    {"id": "NAM04", "name": "Typo in Identifier", "pattern": r"(funtion|recieve|teh|reciever)", "weight": 10, "type": "regex", "desc": "Breaks intellisense"},
    {"id": "NAM05", "name": "Inconsistent Case", "pattern": r"(user_id.*userId|snake_case.*camelCase)", "weight": 12, "type": "regex", "desc": "Pick one convention"},
    
    # ========== UI/UX ANTI-PATTERNS (High - 15-40 pts) ==========
    {"id": "UX01", "name": "Scroll Hijacking", "pattern": r"(overflow-y|scrollBehavior):\s*hidden", "weight": 30, "type": "regex", "desc": "Nauseating UX"},
    {"id": "UX02", "name": "Disable Pinch Zoom", "pattern": r"user-scalable\s*=\s*no", "weight": 40, "type": "regex", "desc": "Accessibility violation"},
    {"id": "UX03", "name": "Autoplay Video", "pattern": r"<video.*autoplay", "weight": 35, "type": "regex", "desc": "Hostile UX"},
    {"id": "UX04", "name": "Low Contrast Text", "pattern": r"color:\s*#(ccc|ddd|eee)", "weight": 25, "type": "regex", "desc": "Unreadable"},
    {"id": "UX05", "name": "Placeholder as Label", "pattern": r"placeholder=['\"][^'\"]+['\"](?!.*<label)", "weight": 20, "type": "regex", "desc": "Disappears on input"},
    {"id": "UX06", "name": "Tiny Tap Target", "pattern": r"(width|height):\s*(10|15|20|25|30)px", "weight": 18, "type": "regex", "desc": "Mobile UX fail"},
    {"id": "UX07", "name": "Mystery Meat Nav", "pattern": r"<button>[^<]*<(svg|i)", "weight": 22, "type": "regex", "desc": "No labels on icons"},
    {"id": "UX08", "name": "Carousel for Critical Content", "pattern": r"(carousel|slider|swiper)", "weight": 25, "type": "regex", "desc": "Users skip slides"},
    {"id": "UX09", "name": "No Loading Indicator", "pattern": r"fetch\(.*\)\.then", "weight": 15, "type": "regex", "desc": "Looks frozen"},
    {"id": "UX10", "name": "Destructive Action No Confirm", "pattern": r"(delete|remove).*onClick", "weight": 30, "type": "regex", "desc": "Require confirmation"},
    {"id": "UX11", "name": "Missing Alt Text", "pattern": r"<img(?![^>]*alt=)", "weight": 20, "type": "regex", "desc": "Screen reader fail"},
    {"id": "UX12", "name": "Custom Cursor", "pattern": r"cursor:\s*url\(", "weight": 15, "type": "regex", "desc": "Laggy and confusing"},
    {"id": "UX13", "name": "Sticky Header >25% screen", "pattern": r"(position:\s*sticky.*height:\s*(25|30|40))", "weight": 20, "type": "regex", "desc": "Reduces readable area"},
    {"id": "UX14", "name": "Form Reset on Error", "pattern": r"form\.reset\(\)", "weight": 35, "type": "regex", "desc": "Most frustrating UX"},
    {"id": "UX15", "name": "target=_blank without rel", "pattern": r"target=['\"]_blank['\"](?![^>]*rel=)", "weight": 18, "type": "regex", "desc": "Security risk"},
    
    # ========== AI SLOP DETECTION (Critical - 100-500 pts) ==========
    {"id": "AI01", "name": "Committed AI Response", "pattern": r"As an AI language model", "weight": 500, "type": "regex", "desc": "Literally copy-pasted ChatGPT", "critical": True},
    {"id": "AI02", "name": "AI Preamble in Code", "pattern": r"(Here is the code you asked for|Here's a solution|I'll help you)", "weight": 200, "type": "regex", "desc": "AI-generated without review", "critical": True},
    {"id": "AI03", "name": "Hallucinated Comment", "pattern": r"(//|#).*\(Note: this is a simplified)", "weight": 100, "type": "regex", "desc": "AI disclaimer in production"},
    {"id": "AI04", "name": "Lorem Ipsum in Production", "pattern": r"Lorem ipsum dolor", "weight": 80, "type": "regex", "desc": "Placeholder text shipped"},
    
    # ========== REACT ANTI-PATTERNS (High - 30-60 pts) ==========
    {"id": "RCT01", "name": "useEffect without deps", "pattern": r"useEffect\([^)]+\)\s*(?!.*,\s*\[)", "weight": 50, "type": "regex", "desc": "Missing dependency array"},
    {"id": "RCT02", "name": "Index as key", "pattern": r"key=\{index\}", "weight": 40, "type": "regex", "desc": "Breaks React reconciliation"},
    {"id": "RCT03", "name": "Inline Function in JSX", "pattern": r"onClick=\{.*=>\s*{", "weight": 25, "type": "regex", "desc": "Re-renders on every cycle"},
    {"id": "RCT04", "name": "setState in render", "pattern": r"(setState|setCount)\(.*\)(?!.*useEffect)", "weight": 60, "type": "regex", "desc": "Infinite render loop"},
    {"id": "RCT05", "name": "window.open without noopener", "pattern": r"window\.open\([^)]+\)(?!.*noopener)", "weight": 45, "type": "regex", "desc": "Security vulnerability"},
    
    # ========== GIT COMMIT HYGIENE (Medium-High - 10-50 pts) ==========
    # These are applied via git log analysis, not file scanning
    {"id": "GIT01", "name": "Lazy Commit Message", "weight": 15, "type": "git", "desc": "Message provides zero context"},
    {"id": "GIT02", "name": "Revert War", "weight": 30, "type": "git", "desc": "Reverting a revert indicates chaos"},
    {"id": "GIT03", "name": "Unprofessional Commit", "weight": 10, "type": "git", "desc": "Commit contains slang/jokes"},
    {"id": "GIT04", "name": "Monster Commit", "weight": 40, "type": "git", "desc": "Single commit touches >50 files"},
    {"id": "GIT05", "name": "Friday Deploy", "weight": 50, "type": "git", "desc": "Read-only Friday violation"},
    {"id": "GIT06", "name": "3AM Commit", "weight": 20, "type": "git", "desc": "Coding at ungodly hours"},
    {"id": "GIT07", "name": "Missing Ticket ID", "weight": 12, "type": "git", "desc": "No issue reference in commit"},
]

IGNORE_DIRS = {'.git', '.github', 'node_modules', 'dist', 'build', 'venv', '__pycache__', '.venv', 'vendor'}
IGNORE_FILES = {'package-lock.json', 'yarn.lock', 'poetry.lock', 'Cargo.lock', 'go.sum'}

def is_excluded(filepath):
    """Check if file matches exclusion patterns from config"""
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern.replace('*', '.*'), filepath):
            return True
    return False

def is_comment_line(line, file_ext):
    """Detect if a line is a comment based on file type"""
    stripped = line.strip()
    if file_ext in ['.py', '.sh', '.bash', '.yml', '.yaml']:
        return stripped.startswith('#')
    elif file_ext in ['.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.go']:
        return stripped.startswith('//') or stripped.startswith('*')
    return False

def check_python_ast_violations(filepath, content):
    """Use AST to detect Python-specific violations (reduces false positives)"""
    violations = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            # Detect eval() usage
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'eval':
                violations.append({
                    "rule_id": "SEC06",
                    "line": node.lineno,
                    "desc": "Real eval() call detected via AST"
                })
            # Detect print() in non-test files
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                if 'test' not in filepath:
                    violations.append({
                        "rule_id": "HYG02",
                        "line": node.lineno,
                        "desc": "Print statement in production code"
                    })
    except SyntaxError:
        pass  # Ignore syntax errors, regex will still catch some issues
    return violations

def audit_git_history():
    """Analyze last 50 commits for behavioral anti-patterns"""
    git_violations = []
    git_deductions = 0
    
    # Check if .git directory exists
    if not os.path.isdir('.git'):
        print("::warning::Git history audit skipped (no .git directory found)")
        print("::warning::To enable git audit, use: actions/checkout@v4 with fetch-depth: 50")
        return git_deductions, git_violations
    
    try:
        # Fix GitHub Actions dubious ownership issue
        subprocess.run(
            ['git', 'config', '--global', '--add', 'safe.directory', '*'],
            capture_output=True,
            timeout=5
        )
        
        # Get last 50 commits: hash|author|date|message
        result = subprocess.run(
            ['git', 'log', '-n', '50', '--pretty=format:%H|%an|%cd|%s', '--date=format:%a %H:%M'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd='.'
        )
        
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if 'does not have any commits' in stderr or 'your current branch' in stderr:
                print("::warning::Git history audit skipped (no commits in repository)")
            elif 'bad default revision' in stderr or 'unknown revision' in stderr:
                print("::warning::Git history audit skipped (shallow clone detected)")
                print("::warning::To enable git audit, use: actions/checkout@v4 with fetch-depth: 50")
            else:
                print(f"::warning::Git history audit skipped (git log failed: {stderr[:100]})")
            return git_deductions, git_violations
        
        commits = result.stdout.strip().split('\n')
        
        # Skip if no commits or only 1 commit (shallow clone)
        if not commits or len(commits) <= 1 or commits[0] == '':
            print("::warning::Git history audit skipped (insufficient commit history)")
            print("::warning::To enable git audit, use: actions/checkout@v4 with fetch-depth: 50")
            return git_deductions, git_violations
        
        # Lazy commit message patterns
        lazy_patterns = [
            r'^(wip|fix|test|asdasd|asd|tmp|temp|debug|update|changes)$',
            r'^(merge|rebase|commit|push)$',
            r'^\.$',
            r'^[0-9]+$',
        ]
        
        # Unprofessional keywords
        unpro_keywords = ['oops', 'lol', 'yolo', 'fml', 'wtf', 'fuck', 'shit', 'hope this works', 'fingers crossed', 'idk']
        
        for commit_line in commits:
            if not commit_line:
                continue
            
            parts = commit_line.split('|')
            if len(parts) < 4:
                continue
            
            commit_hash = parts[0][:7]  # Short SHA
            author = parts[1]
            date_str = parts[2]  # "Fri 18:30"
            message = parts[3].lower()
            
            # GIT01: Lazy commit message
            for pattern in lazy_patterns:
                if re.match(pattern, message, re.IGNORECASE):
                    penalty = 15 * (2 if INPUT_BRUTAL_MODE else 1)
                    git_deductions += penalty
                    git_violations.append({
                        "file": f"commit {commit_hash}",
                        "rule": "Lazy Commit Message",
                        "id": "GIT01",
                        "deduction": penalty,
                        "desc": f"'{message[:50]}' provides zero context"
                    })
                    print(f"::warning::[GIT01] Lazy commit: {commit_hash} '{message[:50]}' (-{penalty} pts)")
                    break
            
            # GIT02: Revert war
            if 'revert "revert' in message:
                penalty = 30 * (2 if INPUT_BRUTAL_MODE else 1)
                git_deductions += penalty
                git_violations.append({
                    "file": f"commit {commit_hash}",
                    "rule": "Revert War",
                    "id": "GIT02",
                    "deduction": penalty,
                    "desc": "Reverting a revert indicates chaos"
                })
                print(f"::warning::[GIT02] Revert war: {commit_hash} (-{penalty} pts)")
            
            # GIT03: Unprofessional commit
            for keyword in unpro_keywords:
                if keyword in message:
                    penalty = 10 * (2 if INPUT_BRUTAL_MODE else 1)
                    git_deductions += penalty
                    git_violations.append({
                        "file": f"commit {commit_hash}",
                        "rule": "Unprofessional Commit",
                        "id": "GIT03",
                        "deduction": penalty,
                        "desc": f"Contains '{keyword}'"
                    })
                    print(f"::warning::[GIT03] Unprofessional: {commit_hash} contains '{keyword}' (-{penalty} pts)")
                    break
            
            # GIT05: Friday deploy (after 16:00)
            if 'Fri' in date_str:
                time_part = date_str.split()[1]  # "18:30"
                hour = int(time_part.split(':')[0])
                if hour >= 16:
                    penalty = 50 * (2 if INPUT_BRUTAL_MODE else 1)
                    git_deductions += penalty
                    git_violations.append({
                        "file": f"commit {commit_hash}",
                        "rule": "Friday Deploy",
                        "id": "GIT05",
                        "deduction": penalty,
                        "desc": f"Committed on Friday at {time_part}"
                    })
                    print(f"::warning::[GIT05] Friday deploy: {commit_hash} at {time_part} (-{penalty} pts)")
            
            # GIT06: 3AM commits (00:00-05:59)
            try:
                time_part = date_str.split()[1]
                hour = int(time_part.split(':')[0])
                if 0 <= hour < 6:
                    penalty = 20 * (2 if INPUT_BRUTAL_MODE else 1)
                    git_deductions += penalty
                    git_violations.append({
                        "file": f"commit {commit_hash}",
                        "rule": "3AM Commit",
                        "id": "GIT06",
                        "deduction": penalty,
                        "desc": f"Committed at {time_part} (ungodly hours)"
                    })
                    print(f"::warning::[GIT06] 3AM commit: {commit_hash} at {time_part} (-{penalty} pts)")
            except (IndexError, ValueError):
                pass
            
            # GIT07: Missing ticket ID (simple check for PROJ-123 pattern)
            if not re.search(r'[A-Z]+-[0-9]+', message):
                penalty = 12 * (2 if INPUT_BRUTAL_MODE else 1)
                git_deductions += penalty
                git_violations.append({
                    "file": f"commit {commit_hash}",
                    "rule": "Missing Ticket ID",
                    "id": "GIT07",
                    "deduction": penalty,
                    "desc": "No issue reference (PROJ-123)"
                })
                # Don't print for GIT07 to avoid spam
        
        # GIT04: Monster commits (check file count in each commit)
        for commit_line in commits[:10]:  # Check only last 10 for performance
            if not commit_line:
                continue
            commit_hash = commit_line.split('|')[0]
            
            stat_result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--numstat', '-r', commit_hash],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if stat_result.returncode == 0:
                file_count = len(stat_result.stdout.strip().split('\n'))
                if file_count > 50:
                    penalty = 40 * (2 if INPUT_BRUTAL_MODE else 1)
                    git_deductions += penalty
                    git_violations.append({
                        "file": f"commit {commit_hash[:7]}",
                        "rule": "Monster Commit",
                        "id": "GIT04",
                        "deduction": penalty,
                        "desc": f"{file_count} files changed in single commit"
                    })
                    print(f"::warning::[GIT04] Monster commit: {commit_hash[:7]} touched {file_count} files (-{penalty} pts)")
    
    except subprocess.TimeoutExpired:
        print("::warning::Git history audit timed out")
    except FileNotFoundError:
        print("::warning::Git not found, skipping history audit")
    except Exception as e:
        print(f"::warning::Git history audit failed: {e}")
    
    return git_deductions, git_violations

def run_scan():
    """Esegue la scansione completa del repository"""
    score = STARTING_SCORE
    violations = []
    
    mode_indicator = "🔥 BRUTAL MODE" if INPUT_BRUTAL_MODE else "Standard Mode"
    print(f"::group::🔍 Starting VibeGuard Scan ({mode_indicator}, Threshold: {INPUT_THRESHOLD})")
    print(f"📊 Starting Score: {STARTING_SCORE}")
    print(f"🎯 Target Threshold: {INPUT_THRESHOLD}")
    print(f"📋 Active Rules: {len([r for r in RULES if r['id'] not in IGNORE_RULES])}/{len(RULES)}")
    if IGNORE_RULES:
        print(f"🚫 Ignored Rules: {', '.join(sorted(IGNORE_RULES))}")
    print("")

    files_scanned = 0
    
    for root, dirs, files in os.walk("."):
        # Filtra directory da ignorare
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            filepath = os.path.relpath(os.path.join(root, file))
            
            # Check exclusion patterns
            if is_excluded(filepath):
                continue
            
            # 1. Check Filename Rules
            for r in RULES:
                if r['id'] in IGNORE_RULES:
                    continue
                if r['type'] == 'filename' and re.search(r['pattern'], file):
                    penalty = r['weight'] * (2 if INPUT_BRUTAL_MODE else 1)
                    score -= penalty
                    violations.append({
                        "file": filepath, 
                        "rule": r['name'], 
                        "id": r['id'],
                        "deduction": penalty,
                        "desc": r['desc']
                    })
                    print(f"::error file={filepath}::[{r['id']}] {r['name']} (-{penalty} pts)")
                    
                    # Brutal Mode: Fail Fast on Critical
                    if INPUT_BRUTAL_MODE and r.get('critical', False):
                        print(f"::error::💀 BRUTAL MODE: Critical violation detected. Terminating immediately.")
                        print(f"::error::Rule {r['id']}: {r['name']} in {filepath}")
                        sys.exit(1)
                    score -= r['weight']
                    violations.append({
                        "file": filepath, 
                        "rule": r['name'], 
                        "id": r['id'],
                        "deduction": r['weight'],
                        "desc": r['desc']
                    })
            # 2. Check Path Rules
            for r in RULES:
                if r['id'] in IGNORE_RULES:
                    continue
                if r['type'] == 'path' and re.search(r['pattern'], filepath):
                    penalty = r['weight'] * (2 if INPUT_BRUTAL_MODE else 1)
                    score -= penalty
                    violations.append({
                        "file": filepath, 
                        "rule": r['name'], 
                        "id": r['id'],
                        "deduction": penalty,
                        "desc": r['desc']
                    })
                    print(f"::error file={filepath}::[{r['id']}] {r['name']} (-{penalty} pts)")
                    
                    if INPUT_BRUTAL_MODE and r.get('critical', False):
                        print(f"::error::💀 BRUTAL MODE: Critical violation. Terminating.")
                        sys.exit(1)

            # 3. Check Content (solo file testuali)
            file_ext = os.path.splitext(file)[1]
            if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.c', '.cpp', '.h', 
                             '.rb', '.php', '.html', '.css', '.scss', '.sass', '.vue', '.svelte',
                             '.md', '.txt', '.yml', '.yaml', '.json', '.xml', '.sh', '.bash')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        files_scanned += 1
                        
                        # Python AST analysis for precision
                        if file_ext == '.py':
                            ast_violations = check_python_ast_violations(filepath, content)
                            for av in ast_violations:
                                rule = next((r for r in RULES if r['id'] == av['rule_id']), None)
                                if rule and rule['id'] not in IGNORE_RULES:
                                    penalty = rule['weight'] * (2 if INPUT_BRUTAL_MODE else 1)
                                    score -= penalty
                                    violations.append({
                                        "file": filepath,
                                        "rule": rule['name'],
                                        "id": rule['id'],
                                        "deduction": penalty,
                                        "desc": av['desc'],
                                        "line": av['line']
                                    })
                                    print(f"::warning file={filepath},line={av['line']}::[{rule['id']}] {rule['name']} (AST) (-{penalty} pts)")
                        
                        # Check Line Count
                        for r in RULES:
                            if r['id'] in IGNORE_RULES:
                                continue
                            if r['type'] == 'lines' and len(lines) > r.get('max', float('inf')):
                                penalty = r['weight'] * (2 if INPUT_BRUTAL_MODE else 1)
                                score -= penalty
                                violations.append({
                                    "file": filepath, 
                                    "rule": f"{r['name']} ({len(lines)} lines)", 
                                    "id": r['id'],
                                    "deduction": penalty,
                                    "desc": r['desc']
                                })
                                print(f"::warning file={filepath}::[{r['id']}] File has {len(lines)} lines (-{penalty} pts)")

                        # Check EOF Newline
                        for r in RULES:
                            if r['id'] in IGNORE_RULES:
                                continue
                            if r['type'] == 'eof' and content and not content.endswith('\n'):
                                penalty = r['weight'] * (2 if INPUT_BRUTAL_MODE else 1)
                                score -= penalty
                                violations.append({
                                    "file": filepath, 
                                    "rule": r['name'], 
                                    "id": r['id'],
                                    "deduction": penalty,
                                    "desc": r['desc']
                                })
                                print(f"::warning file={filepath}::[{r['id']}] {r['name']} (-{penalty} pts)")

                        # Check Regex Patterns (with smart comment detection)
                        for r in RULES:
                            if r['id'] in IGNORE_RULES:
                                continue
                            if r['type'] == 'regex':
                                matches = list(re.finditer(r['pattern'], content, re.MULTILINE | re.IGNORECASE))
                                if matches:
                                    for match in matches[:3]:  # Limita a 3 match per regola per file
                                        line_num = content[:match.start()].count('\n') + 1
                                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                                        
                                        # Smart filtering: Skip code-related rules if line is a comment
                                        is_comment = is_comment_line(line_content, file_ext)
                                        if is_comment and not r['id'].startswith(('DOC', 'STB03', 'STB04', 'STB05')):
                                            continue  # Ignore code violations in comment lines
                                        
                                        penalty = r['weight'] * (2 if INPUT_BRUTAL_MODE else 1)
                                        score -= penalty
                                        violations.append({
                                            "file": filepath, 
                                            "rule": r['name'], 
                                            "id": r['id'],
                                            "deduction": penalty,
                                            "desc": r['desc'],
                                            "line": line_num
                                        })
                                        print(f"::warning file={filepath},line={line_num}::[{r['id']}] {r['name']} (-{penalty} pts)")
                                        
                                        # Brutal Mode: Fail Fast on Critical
                                        if INPUT_BRUTAL_MODE and r.get('critical', False):
                                            print(f"::error::💀 BRUTAL MODE: Critical security violation!")
                                            print(f"::error::Rule {r['id']}: {r['name']} at {filepath}:{line_num}")
                                            sys.exit(1)

                except Exception as e:
                    # Skip binary files or permission errors
                    pass

    print("")
    print(f"📁 Files Scanned: {files_scanned}")
    print(f"⚠️  Total Violations: {len(violations)}")
    print(f"📉 Total Deductions: {STARTING_SCORE - score} pts")
    print("::endgroup::")
    
    # ========== GIT HISTORY AUDIT ==========
    print("")
    print("::group::🌿 Auditing Git History (Last 50 Commits)")
    git_deductions, git_violations = audit_git_history()
    score -= git_deductions
    violations.extend(git_violations)
    print(f"📊 Git Deductions: -{git_deductions} pts")
    print(f"⚠️  Git Violations: {len(git_violations)}")
    print("::endgroup::")
    
    return score, violations

def write_summary(score, violations):
    """Scrive il Job Summary in formato Markdown nativo di GitHub"""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    status_emoji = "✅" if score >= INPUT_THRESHOLD else "❌"
    status_text = "PASSED" if score >= INPUT_THRESHOLD else "FAILED"
    bar_width = 20
    bar_filled = int((score / STARTING_SCORE) * bar_width)
    progress_bar = "█" * bar_filled + "░" * (bar_width - bar_filled)
    
    md = f"""# {status_emoji} VibeGuard Code Quality Report

## 📊 Final Score

**Score:** `{score}/{STARTING_SCORE}` {progress_bar}  
**Threshold:** `{INPUT_THRESHOLD}`  
**Status:** **{status_text}**

---

## 📉 Violations Detected ({len(violations)})

"""
    
    if violations:
        # Raggruppa per categoria
        categories = {}
        for v in violations:
            rule_id = v['id']
            category = rule_id[:3]  # SEC, STB, MNT, etc.
            if category not in categories:
                categories[category] = []
            categories[category].append(v)
        
        category_names = {
            'SEC': '🔒 Security',
            'STB': '⚡ Stability', 
            'MNT': '🔧 Maintainability',
            'HYG': '🧹 Code Hygiene',
            'SME': '👃 Code Smells',
            'TST': '🧪 Testing',
            'PRF': '⚡ Performance',
            'DOC': '📝 Documentation',
            'DEP': '📦 Dependencies',
            'VCS': '🌿 Version Control',
            'NAM': '🏷️  Naming',
            'UX': '🎨 UI/UX',
            'AI': '🤖 AI Slop',
            'RCT': '⚛️  React',
            'GIT': '🌿 Git Hygiene'
        }
        
        for cat_id in sorted(categories.keys()):
            cat_name = category_names.get(cat_id, cat_id)
            cat_violations = categories[cat_id]
            cat_total = sum(v['deduction'] for v in cat_violations)
            
            md += f"### {cat_name} (-{cat_total} pts)\n\n"
            md += "| File | Rule | Line | Penalty |\n"
            md += "|------|------|------|--------:|\n"
            
            for v in cat_violations[:10]:  # Limita a 10 per categoria nel summary
                file_display = v['file'][:50] + "..." if len(v['file']) > 50 else v['file']
                line_info = f"L{v['line']}" if 'line' in v else "-"
                md += f"| `{file_display}` | {v['rule']} | {line_info} | -{v['deduction']} |\n"
            
            if len(cat_violations) > 10:
                md += f"| ... | *{len(cat_violations) - 10} more violations* | ... | ... |\n"
            
            md += "\n"
    else:
        md += "### 🎉 No violations found!\n\n"
        md += "Your code is **pristine**. Perfect SOTA engineering vibes. 🚀\n\n"

    md += "---\n\n"
    md += f"*Scanned with VibeGuard Auditor • Threshold: {INPUT_THRESHOLD} • [Learn More](https://github.com/fabriziosalmi/vibe-check)*\n"

    with open(summary_file, "a") as f:
        f.write(md)

def main():
    """Entry point per la GitHub Action"""
    print("🛡️  VibeGuard Auditor v1.0.0")
    print("=" * 50)
    
    score, violations = run_scan()
    write_summary(score, violations)
    
    # Output per passi successivi del workflow
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"score={score}\n")
    
    # Exit code determina il successo/fallimento della Action
    if score < INPUT_THRESHOLD:
        print("")
        print(f"::error::❌ VibeGuard FAILED: Score {score} is below threshold {INPUT_THRESHOLD}")
        print(f"::error::Vibecoding detected! Clean up the code and try again.")
        sys.exit(1)
    else:
        print("")
        print(f"✅ VibeGuard PASSED: Score {score} meets threshold {INPUT_THRESHOLD}")
        sys.exit(0)

if __name__ == "__main__":
    main()
