# 🛡️ VibeGuard Auditor

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-VibeGuard-blue?logo=github)](https://github.com/marketplace/actions/vibeguard-auditor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

**SOTA Python-based linter that ranks your code quality from 0-1000 based on Vibecoding vs Engineering patterns.**

Stop vibecoding, start engineering. VibeGuard detects security issues, code smells, technical debt, and anti-patterns in your codebase — then scores it objectively.

---

## 🚀 Features

- **🎯 Objective Scoring**: Your code starts at 1000 points. Every violation deducts points based on severity
- **🔒 Security First**: Detects hardcoded secrets, SQL injection patterns, dangerous eval() usage
- **⚡ Native GitHub Integration**: Beautiful job summaries, inline file annotations, and actionable feedback
- **🐳 Zero Config**: Runs in Docker — works on any runner (Ubuntu, Windows, macOS)
- **📊 100+ Rules**: Covers security, stability, maintainability, performance, testing, and more
- **🎨 Categorized Reports**: Violations grouped by type (Security, Code Smells, Hygiene, etc.)

---

## 📖 Quick Start

### Basic Usage

Add this to your workflow file (`.github/workflows/vibeguard.yml`):

```yaml
name: VibeGuard Code Quality Check
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Run VibeGuard Auditor
        uses: fab/vibe-check@v1
        with:
          threshold: 800
```

**That's it!** VibeGuard will scan your code and fail the build if the score drops below 800.

---

## ⚙️ Configuration

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `threshold` | Minimum score required to pass (0-1000) | No | `800` |

### Outputs

| Output | Description |
|--------|-------------|
| `score` | The final calculated score after all deductions |

### Example: Custom Threshold

```yaml
- name: Run VibeGuard (Strict Mode)
  uses: fab/vibe-check@v1
  with:
    threshold: 950  # Only allow 50 points of violations
```

### Example: Use Score in Later Steps

```yaml
- name: Run VibeGuard
  id: vibeguard
  uses: fab/vibe-check@v1
  with:
    threshold: 700

- name: Post Score to Slack
  run: |
    echo "Code Quality Score: ${{ steps.vibeguard.outputs.score }}/1000"
```

---

## 📋 Rule Categories

VibeGuard scans for **100+ patterns** across these categories:

| Category | Examples | Severity |
|----------|----------|----------|
| 🔒 **Security** | Hardcoded secrets, SQL injection, `eval()` | Critical (-100 pts) |
| ⚡ **Stability** | Empty catch blocks, bare excepts, TODOs | High (-50 pts) |
| 🔧 **Maintainability** | Huge files (>2000 lines), deep nesting | Medium (-30 pts) |
| 👃 **Code Smells** | `var` keyword, nested ternaries, god objects | Medium (-25 pts) |
| 🧹 **Hygiene** | `console.log`, trailing whitespace, debugger | Low (-5 pts) |
| 🧪 **Testing** | Skipped tests, focused tests, empty assertions | Medium (-40 pts) |
| ⚡ **Performance** | Synchronous I/O, nested loops | Medium (-25 pts) |
| 📦 **Dependencies** | Wildcard imports, absolute paths | Medium (-25 pts) |
| 🌿 **VCS** | Merge conflict markers, committed `.env` | Critical (-100 pts) |

---

## 📊 Sample Output

### Job Summary (visible in GitHub Actions UI)

```markdown
# ✅ VibeGuard Code Quality Report

## 📊 Final Score
Score: 872/1000 ████████████████████
Threshold: 800
Status: PASSED

## 📉 Violations Detected (12)

### 🔒 Security (-80 pts)
| File | Rule | Line | Penalty |
|------|------|------|--------:|
| `src/config.js` | Hardcoded API Key | L23 | -80 |

### 🧹 Code Hygiene (-30 pts)
| File | Rule | Line | Penalty |
|------|------|------|--------:|
| `src/utils.js` | Console Log | L45 | -5 |
| `src/index.ts` | TODO Comment | L12 | -15 |
...
```

### Inline Annotations (visible on Files Changed tab)

![GitHub Annotations Preview](https://user-images.githubusercontent.com/placeholder.png)

---

## 🎯 Why VibeGuard?

| Traditional Linters | VibeGuard |
|---------------------|-----------|
| ❌ Pass/Fail only | ✅ **Quantified score** (0-1000) |
| ❌ Fragmented tools (ESLint, Prettier, etc.) | ✅ **One unified scanner** |
| ❌ No security detection | ✅ **Hardcoded secrets, SQL injection** |
| ❌ Generic warnings | ✅ **Severity-weighted penalties** |
| ❌ Hard to track improvement | ✅ **Score trending over time** |

---

## 🧑‍💻 Advanced Workflows

### Fail on Critical Issues Only

```yaml
- name: VibeGuard (Permissive)
  uses: fab/vibe-check@v1
  with:
    threshold: 500  # Allow more violations
```

### Run on PRs Only

```yaml
on:
  pull_request:
    branches: [main, develop]
```

### Matrix Testing (Multiple Languages)

```yaml
jobs:
  audit:
    strategy:
      matrix:
        project: [frontend, backend, mobile]
    steps:
      - uses: actions/checkout@v4
      - name: VibeGuard ${{ matrix.project }}
        uses: fab/vibe-check@v1
        with:
          threshold: 850
```

---

## 🛠️ Local Development

Want to test VibeGuard locally before pushing?

```bash
# Clone the action repo
git clone https://github.com/fab/vibe-check.git
cd vibe-check

# Build the Docker image
docker build -t vibeguard .

# Run on your project
docker run -v $(pwd):/github/workspace vibeguard
```

Or run the Python script directly:

```bash
python3 vibeguard.py
```

---

## 📚 Rule Reference

<details>
<summary><strong>🔒 Security Rules (Click to Expand)</strong></summary>

| ID | Rule | Pattern | Weight |
|----|------|---------|--------|
| SEC01 | Committed `.env` file | Filename match | -100 |
| SEC02 | AWS Access Key Pattern | Regex | -100 |
| SEC03 | Private Key File | `.pem`, `.key`, etc. | -100 |
| SEC04 | Hardcoded Password | `password = "..."` | -80 |
| SEC05 | Hardcoded API Key | `api_key = "..."` | -80 |
| SEC06 | `eval()` Usage | Dangerous execution | -70 |
| SEC07 | SQL Concatenation | Injection risk | -60 |

</details>

<details>
<summary><strong>⚡ Stability Rules</strong></summary>

| ID | Rule | Pattern | Weight |
|----|------|---------|--------|
| STB01 | Empty Catch Block | `catch (e) {}` | -50 |
| STB02 | Bare Except | `except: pass` | -50 |
| STB03 | TODO Comment | `// TODO` | -15 |
| STB04 | FIXME Comment | `// FIXME` | -20 |
| STB05 | XXX Comment | `// XXX` | -25 |

</details>

[See full rule list in `vibeguard.py`](./vibeguard.py)

---

## 🤝 Contributing

Found a false positive? Want to add new rules? PRs welcome!

1. Fork the repo
2. Add your rule to `RULES` in `vibeguard.py`
3. Test locally: `python vibeguard.py`
4. Submit PR with examples

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Credits

Created by [@fab](https://github.com/fab) to combat vibecoding and promote SOTA engineering.

Inspired by the eternal struggle between "it works on my machine" and "it works in production."

---

## 🔗 Links

- [GitHub Marketplace](https://github.com/marketplace/actions/vibeguard-auditor)
- [Report Issues](https://github.com/fab/vibe-check/issues)
- [View Source](https://github.com/fab/vibe-check)

---

**Stop vibecoding. Start engineering. Ship with confidence.** 🚀
