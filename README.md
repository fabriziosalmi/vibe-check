# VibeGuard Auditor ⚡

**v1.4.0** - Code Quality Scanner with Modular Architecture

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue)](https://github.com/features/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Anti-slop CI/CD gatekeeper** detecting security vulnerabilities, code smells, AI-generated slop, and git anti-patterns with intelligent 0-1000 scoring.

---

## 🚀 Features

### Core Capabilities
- ✅ **300+ Rules** across security, stability, maintainability, performance, UX, and more
- ✅ **AST-based Analysis** for Python - no more regex false positives
- ✅ **Git History Audit** - analyzes commit patterns and quality
- ✅ **Inline Ignore Comments** - `# vibeguard:ignore` to suppress false positives
- ✅ **Modular Architecture** - clean separation: scanner, rules, reporter
- ✅ **Structured Logging** - proper logging with verbosity levels
- ✅ **GitHub Actions Native** - annotations, job summaries, auto-fail
- ✅ **Configurable Rules** - externalized YAML configuration
- ✅ **CLI with argparse** - professional argument parsing

### Rule Categories
- 🔒 **Security** - Hardcoded credentials, SQL injection, eval() usage
- ⚡ **Stability** - Empty catch blocks, TODO/FIXME comments, magic numbers
- 🔧 **Maintainability** - God objects, huge files, deep nesting
- 🧹 **Code Hygiene** - Console.log, debugger statements, trailing whitespace
- 👃 **Code Smells** - var keyword, nested ternaries, long parameter lists
- 🧪 **Testing** - Skipped tests, focused tests, fake assertions
- ⚡ **Performance** - Sync I/O, nested loops, blocking operations
- 📝 **Documentation** - Missing docs, passive voice, "click here" links
- 🎨 **UI/UX** - Scroll hijacking, tiny tap targets, missing alt text
- 🤖 **AI Slop Detection** - Copy-pasted ChatGPT responses, Lorem Ipsum
- 🌿 **Git Hygiene** - Lazy commits, merge conflicts, unprofessional messages

---

## 📦 Installation

### As a GitHub Action

Add to `.github/workflows/vibe-check.yml`:

```yaml
name: VibeGuard Code Quality

on: [push, pull_request]

jobs:
  vibe-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 50  # Required for git history audit
      
      - name: Run VibeGuard Auditor
        uses: fabriziosalmi/vibe-check@main
        with:
          threshold: 800
          brutal_mode: false
```

### Local Installation

```bash
# Clone the repository
git clone https://github.com/fabriziosalmi/vibe-check.git
cd vibe-check

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python vibeguard_new.py
```

---

## 🎯 Usage

### Basic Usage

```bash
# Scan current directory with default threshold (800)
python vibeguard_new.py

# Set custom threshold
python vibeguard_new.py --threshold 900

# Enable brutal mode (double penalties, fail-fast on critical violations)
python vibeguard_new.py --brutal-mode

# Verbose output
python vibeguard_new.py --verbose

# Quiet mode (errors only)
python vibeguard_new.py --quiet

# Skip git history audit
python vibeguard_new.py --no-git

# Scan specific directory
python vibeguard_new.py --directory ./src
```

### Configuration File

Create `.vibeguardrc` in your project root:

```json
{
  "ignore": ["HYG01", "HYG02", "DOC04"],
  "exclude_files": [
    "*.min.js",
    "dist/*",
    "node_modules/*",
    "vendor/*"
  ]
}
```

### Inline Ignores

Suppress specific violations with comments:

```python
# This line will be ignored
password = "temporary_dev_password"  # vibeguard:ignore

# vibeguard:ignore
# This whole block is ignored
api_key = "dev_key_12345"
```

```javascript
// This line will be ignored
console.log("Debug info");  // vibeguard:ignore

// vibeguard:ignore
debugger;
```

---

## 📁 Project Structure

```
vibe-check/
├── src/                      # Source modules (NEW!)
│   ├── __init__.py          # Package initialization
│   ├── rules.py             # Rules management
│   ├── scanner.py           # File scanning and AST analysis
│   ├── reporter.py          # Output formatting and GitHub integration
│   └── logger.py            # Structured logging
├── config/                   # Configuration (NEW!)
│   └── rules.yaml           # Externalized rules definition
├── tests/                    # Test suite (NEW!)
│   ├── test_rules.py        # Unit tests for rules module
│   ├── test_scanner.py      # Unit tests for scanner module
│   ├── test_violations.py   # Sample file with deliberate violations
│   ├── test_violations.js   # JS violations for testing
│   └── test_violations.md   # Documentation violations
├── vibeguard_new.py          # Main entry point (REFACTORED)
├── vibeguard.py              # Legacy entry point (deprecated)
├── requirements.txt          # Python dependencies
├── action.yml                # GitHub Action definition
├── Dockerfile                # Container definition
└── README.md                 # This file

```

### Architecture

**Before (God Object)**:
- Single 730-line file with everything mixed together
- Hardcoded rules list
- Manual `os.environ` parsing
- print() everywhere
- Regex-only parsing (false positives)

**After (Modular)**:
- **src/rules.py**: Rule loading, filtering, validation
- **src/scanner.py**: File scanning, AST parsing, violation detection
- **src/reporter.py**: GitHub annotations, job summaries, console output
- **src/logger.py**: Structured logging with verbosity levels
- **config/rules.yaml**: Externalized rule definitions
- **vibeguard_new.py**: Clean CLI with argparse

---

## 🔧 Development

### Running Tests

```bash
# Run unit tests
python tests/test_rules.py
python tests/test_scanner.py

# Scan test violation files (should find many violations)
python vibeguard_new.py --directory tests --threshold 0

# With pytest (optional)
pip install pytest pytest-cov
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Adding New Rules

Edit `config/rules.yaml`:

```yaml
security:
  - id: SEC13
    name: Hardcoded JWT Secret
    pattern: "jwt\\.sign\\([^,]+,\\s*['\"][^'\"]{10,}['\"]"
    weight: 90
    type: regex
    desc: JWT secret should be in environment variable
    critical: true
```

### Creating Custom Rules Files

```bash
# Use custom rules file
python vibeguard_new.py --rules my_custom_rules.yaml
```

---

## 📊 Scoring System

- **Starting Score**: 1000
- **Deductions**: Each violation deducts points based on severity
- **Brutal Mode**: Doubles all penalties
- **Threshold**: Configurable pass/fail threshold (default: 800)

### Severity Levels
- **Critical (100 pts)**: Security vulnerabilities, merge conflicts
- **High (50-90 pts)**: Major code smells, test issues
- **Medium (20-49 pts)**: Maintainability problems, performance issues
- **Low (2-19 pts)**: Code hygiene, minor documentation issues

---

## 🎨 GitHub Actions Integration

### Annotations

VibeGuard creates GitHub code annotations:

```
::error file=src/auth.py,line=42::[SEC04] Hardcoded Password (-80 pts)
::warning file=src/utils.js,line=15::[HYG01] Console Log (-5 pts)
```

### Job Summary

Generates a detailed markdown summary in the Actions UI:

- ✅/❌ Pass/Fail status
- 📊 Score visualization with progress bar
- 📉 Violations grouped by category
- 📁 File-by-file breakdown

### Outputs

```yaml
- name: Run VibeGuard
  id: vibe-check
  uses: fabriziosalmi/vibe-check@main
  with:
    threshold: 850

- name: Use Score
  run: echo "Score was ${{ steps.vibe-check.outputs.score }}"
```

---

## 🚨 Brutal Mode

Enable with `--brutal-mode` or `brutal_mode: true` in GitHub Actions:

- **2x Penalties**: All violations count double
- **Fail-Fast**: Immediately exits on critical violations
- **Stricter Enforcement**: Perfect for production branches

```yaml
- uses: fabriziosalmi/vibe-check@main
  with:
    threshold: 900
    brutal_mode: true  # Production-ready code only!
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-rule`
3. Add your rule to `config/rules.yaml`
4. Add tests in `tests/`
5. Run tests: `python tests/test_rules.py`
6. Commit with atomic messages (not "fix" or "wip"!)
7. Submit a pull request

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by real-world code review pain
- Built to fight vibecoding and AI slop
- Designed for teams that value code quality

---

## 📬 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/fabriziosalmi/vibe-check/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/fabriziosalmi/vibe-check/discussions)
- 📧 **Email**: Open an issue instead!

---

**Practice what you preach.** ✨

Built with ❤️ and refactored to follow its own rules.
