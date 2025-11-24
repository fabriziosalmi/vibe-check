# Migration Guide: VibeGuard v1 → v2

## Overview

VibeGuard v2 is a complete refactoring that follows the best practices it enforces:

- ✅ **No more God Object** - Split into scanner.py, rules.py, reporter.py
- ✅ **AST parsing** instead of regex-only for Python files
- ✅ **Comprehensive tests** in `tests/` directory
- ✅ **Externalized rules** in `config/rules.yaml`
- ✅ **Proper CLI** with argparse
- ✅ **Inline ignore comments** - `# vibeguard:ignore`
- ✅ **Structured logging** replacing print() statements
- ✅ **Modular architecture** for maintainability

---

## Breaking Changes

### 1. Entry Point

**Old:**
```bash
python vibeguard.py
```

**New:**
```bash
python vibeguard_new.py
```

### 2. Environment Variables vs CLI Args

**Old (GitHub Actions only):**
```yaml
env:
  INPUT_THRESHOLD: 800
  INPUT_BRUTAL_MODE: true
```

**New (CLI or GitHub Actions):**
```bash
# CLI
python vibeguard_new.py --threshold 800 --brutal-mode

# GitHub Actions (still works!)
with:
  threshold: 800
  brutal_mode: true
```

### 3. Configuration File Format

**Unchanged** - `.vibeguardrc` format is the same:

```json
{
  "ignore": ["HYG01", "SEC04"],
  "exclude_files": ["dist/*", "*.min.js"]
}
```

But now you can also specify custom rules file:

```bash
python vibeguard_new.py --rules custom_rules.yaml --config .vibeguardrc
```

---

## New Features

### 1. Inline Ignore Comments

**v1**: Could only ignore rules globally via `.vibeguardrc`

**v2**: Can ignore specific lines with comments:

```python
password = "dev_only"  # vibeguard:ignore

# vibeguard:ignore
api_key = "temporary"
```

### 2. AST-based Python Analysis

**v1**: Regex-only (many false positives)

**v2**: Uses Python's `ast` module for precise detection:

```python
# v1: Would catch this in a string
message = "don't eval() user input"  # False positive!

# v2: Only catches actual eval() calls via AST
result = eval(user_input)  # Real violation ✓
```

### 3. Structured Logging

**v1**: `print()` everywhere

**v2**: Proper logging with levels:

```bash
python vibeguard_new.py --verbose  # DEBUG level
python vibeguard_new.py --quiet    # ERROR level only
```

### 4. Modular Architecture

**v1**: Single 730-line file

**v2**: Clean modules:

```python
from src.rules import RulesManager
from src.scanner import CodeScanner
from src.reporter import Reporter
from src.logger import create_logger
```

---

## Migration Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This now includes PyYAML for the externalized rules.

### Step 2: Update GitHub Actions Workflow

**Old workflow:**
```yaml
- uses: fabriziosalmi/vibe-check@v1
  with:
    threshold: 800
```

**New workflow (recommended):**
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 50  # For git history audit

- uses: fabriziosalmi/vibe-check@main
  with:
    threshold: 800
    brutal_mode: false
```

### Step 3: Test Locally

```bash
# Test with new version
python vibeguard_new.py --directory . --threshold 700 --verbose

# Compare with old version
python vibeguard.py  # Should still work but show deprecation notice
```

### Step 4: Update Configuration (Optional)

If you want to customize rules, create `config/rules.yaml` or edit the default one.

### Step 5: Add Inline Ignores

Review violations and add `# vibeguard:ignore` where needed:

```python
# Known false positive - waiting for API update
legacy_auth = "Basic " + base64.b64encode(creds)  # vibeguard:ignore
```

---

## Compatibility Matrix

| Feature | v1 | v2 | Notes |
|---------|----|----|-------|
| GitHub Actions | ✅ | ✅ | Same interface |
| `.vibeguardrc` | ✅ | ✅ | Unchanged format |
| CLI Arguments | ❌ | ✅ | New: argparse |
| Inline Ignores | ❌ | ✅ | New: `# vibeguard:ignore` |
| AST Parsing | ❌ | ✅ | New: Python only |
| Modular Code | ❌ | ✅ | Refactored architecture |
| External Rules | ❌ | ✅ | New: YAML config |
| Structured Logging | ❌ | ✅ | New: proper logger |
| Unit Tests | ❌ | ✅ | New: `tests/` directory |

---

## Testing Your Migration

### 1. Run Unit Tests

```bash
python tests/test_rules.py
python tests/test_scanner.py
```

Should output:
```
✅ All tests passed!
```

### 2. Scan Test Violations

```bash
python vibeguard_new.py --directory tests --threshold 0
```

Should detect violations in `tests/test_violations.*` files.

### 3. Compare Scores

```bash
# Old version
python vibeguard.py > old_results.txt

# New version  
python vibeguard_new.py > new_results.txt

# Compare
diff old_results.txt new_results.txt
```

You might see slight differences due to:
- AST-based detection (fewer false positives)
- Inline ignore comments being respected
- Improved comment detection

---

## Rollback Plan

If you encounter issues, you can rollback:

### GitHub Actions

```yaml
# Pin to old version
- uses: fabriziosalmi/vibe-check@v1
```

### Local

```bash
# Use old entry point
python vibeguard.py
```

The old `vibeguard.py` file is preserved and will continue to work.

---

## FAQ

### Q: Will my scores change?

**A:** Slightly. The new AST-based parsing reduces false positives, so you might see higher scores for Python files.

### Q: Do I need to update my `.vibeguardrc`?

**A:** No, it uses the same format. But you can now also ignore rules inline with comments.

### Q: Can I use custom rules?

**A:** Yes! Create your own `rules.yaml` and use `--rules custom_rules.yaml`.

### Q: What about performance?

**A:** V2 is actually faster for large Python files because AST parsing is more efficient than complex regex.

### Q: Is the old version still supported?

**A:** The old `vibeguard.py` will remain in the repo for compatibility, but new features will only be added to v2.

---

## Getting Help

- 🐛 **Found a bug?** [Open an issue](https://github.com/fabriziosalmi/vibe-check/issues)
- 💬 **Have questions?** [Start a discussion](https://github.com/fabriziosalmi/vibe-check/discussions)
- 📖 **Read the docs**: [README_NEW.md](README_NEW.md)

---

## Timeline

- **v1.x**: Original monolithic version (still available)
- **v2.0**: Refactored modular version ⬅️ **You are here**
- **v2.1+**: New features, more rules, better performance

---

**Welcome to VibeGuard v2!** 🎉

Practice what you preach. Your code deserves it.
