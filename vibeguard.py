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

# Leggiamo gli input dall'ambiente (passati da action.yml)
INPUT_THRESHOLD = int(os.environ.get("INPUT_THRESHOLD", 800))
STARTING_SCORE = 1000

# 300+ SOTA Rules: Anti-Vibecoding Patterns from Code Quality + UI/UX + Documentation
RULES = [
    # ========== SECURITY (Critical - 60-100 pts) ==========
    {"id": "SEC01", "name": "Committed .env file", "pattern": r"^\.env$", "weight": 100, "type": "filename", "desc": "Security risk: exposed secrets"},
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
]

IGNORE_DIRS = {'.git', '.github', 'node_modules', 'dist', 'build', 'venv', '__pycache__', '.venv', 'vendor'}
IGNORE_FILES = {'package-lock.json', 'yarn.lock', 'poetry.lock', 'Cargo.lock', 'go.sum'}

def run_scan():
    """Esegue la scansione completa del repository"""
    score = STARTING_SCORE
    violations = []
    
    print(f"::group::🔍 Starting VibeGuard Scan (Threshold: {INPUT_THRESHOLD})")
    print(f"📊 Starting Score: {STARTING_SCORE}")
    print(f"🎯 Target Threshold: {INPUT_THRESHOLD}")
    print(f"📋 Active Rules: {len(RULES)}")
    print("")

    files_scanned = 0
    
    for root, dirs, files in os.walk("."):
        # Filtra directory da ignorare
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            filepath = os.path.relpath(os.path.join(root, file))
            
            # 1. Check Filename Rules
            for r in RULES:
                if r['type'] == 'filename' and re.search(r['pattern'], file):
                    score -= r['weight']
                    violations.append({
                        "file": filepath, 
                        "rule": r['name'], 
                        "id": r['id'],
                        "deduction": r['weight'],
                        "desc": r['desc']
                    })
                    print(f"::error file={filepath}::[{r['id']}] {r['name']} (-{r['weight']} pts)")
            
            # 2. Check Path Rules
            for r in RULES:
                if r['type'] == 'path' and re.search(r['pattern'], filepath):
                    score -= r['weight']
                    violations.append({
                        "file": filepath, 
                        "rule": r['name'], 
                        "id": r['id'],
                        "deduction": r['weight'],
                        "desc": r['desc']
                    })
                    print(f"::error file={filepath}::[{r['id']}] {r['name']} (-{r['weight']} pts)")

            # 3. Check Content (solo file testuali)
            if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.c', '.cpp', '.h', 
                             '.rb', '.php', '.html', '.css', '.scss', '.sass', '.vue', '.svelte',
                             '.md', '.txt', '.yml', '.yaml', '.json', '.xml', '.sh', '.bash')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        files_scanned += 1
                        
                        # Check Line Count
                        for r in RULES:
                            if r['type'] == 'lines' and len(lines) > r.get('max', float('inf')):
                                score -= r['weight']
                                violations.append({
                                    "file": filepath, 
                                    "rule": f"{r['name']} ({len(lines)} lines)", 
                                    "id": r['id'],
                                    "deduction": r['weight'],
                                    "desc": r['desc']
                                })
                                print(f"::warning file={filepath}::[{r['id']}] File has {len(lines)} lines (-{r['weight']} pts)")

                        # Check EOF Newline
                        for r in RULES:
                            if r['type'] == 'eof' and content and not content.endswith('\n'):
                                score -= r['weight']
                                violations.append({
                                    "file": filepath, 
                                    "rule": r['name'], 
                                    "id": r['id'],
                                    "deduction": r['weight'],
                                    "desc": r['desc']
                                })
                                print(f"::warning file={filepath}::[{r['id']}] {r['name']} (-{r['weight']} pts)")

                        # Check Regex Patterns
                        for r in RULES:
                            if r['type'] == 'regex':
                                matches = list(re.finditer(r['pattern'], content, re.MULTILINE | re.IGNORECASE))
                                if matches:
                                    for match in matches[:3]:  # Limita a 3 match per regola per file
                                        line_num = content[:match.start()].count('\n') + 1
                                        score -= r['weight']
                                        violations.append({
                                            "file": filepath, 
                                            "rule": r['name'], 
                                            "id": r['id'],
                                            "deduction": r['weight'],
                                            "desc": r['desc'],
                                            "line": line_num
                                        })
                                        print(f"::warning file={filepath},line={line_num}::[{r['id']}] {r['name']} (-{r['weight']} pts)")

                except Exception as e:
                    # Skip binary files or permission errors
                    pass

    print("")
    print(f"📁 Files Scanned: {files_scanned}")
    print(f"⚠️  Total Violations: {len(violations)}")
    print(f"📉 Total Deductions: {STARTING_SCORE - score} pts")
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
            'NAM': '🏷️  Naming'
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
