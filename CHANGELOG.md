# Changelog

All notable changes to VibeGuard Auditor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-11-24

### ✨ Added
- **Modular Architecture**: Separated codebase into `src/scanner.py`, `src/rules.py`, `src/reporter.py`, and `src/logger.py`
- **AST-Based Python Parsing**: Uses Python's `ast` module for precise violation detection, eliminating false positives
- **Inline Ignore Comments**: Support for `# vibeguard:ignore` and `// vibeguard:ignore` to suppress specific violations
- **Externalized Rules**: All 115 rules now in `config/rules.yaml` for easy customization
- **Structured Logging**: Professional logging with `--verbose` and `--quiet` flags
- **Comprehensive Test Suite**: Unit tests in `tests/` directory with sample violation files
- **CLI with argparse**: Proper command-line argument parsing replacing manual `os.environ` reads
- **Custom Rules Support**: `--rules` flag to specify custom rules YAML file
- **Package Structure**: Proper Python package with `src/__init__.py`

### 🔧 Changed
- **Entry Point**: `vibeguard.py` now uses modular architecture (legacy version moved to `vibeguard_legacy.py`)
- **Comment Detection**: Smarter comment detection that distinguishes code from comments
- **Performance**: Faster Python file scanning with AST parsing
- **Error Handling**: Better error messages and graceful failures

### 📝 Improved
- **False Positives**: Dramatically reduced with AST parsing for Python
- **Code Organization**: Clean separation of concerns across modules
- **Maintainability**: Each module has single responsibility
- **Documentation**: Comprehensive README, MIGRATION guide, and inline documentation
- **Testing**: Can now verify the auditor actually works with test suite

### 🐛 Fixed
- Regex patterns catching code in comments
- String literals triggering false positives (e.g., "don't eval()" in strings)
- Inconsistent logging output

### 📚 Documentation
- New comprehensive README.md with all v1.4.0 features
- Added MIGRATION.md guide for upgrading from older versions
- Created tests/README.md explaining the test suite
- Added inline docstrings to all modules and functions

### ⚠️ Deprecated
- `vibeguard_legacy.py`: Old monolithic version kept for compatibility but not maintained

## [1.3.0] - Previous Version

### Features
- 300+ rules for code quality detection
- Git history audit (last 50 commits)
- GitHub Actions integration
- Brutal mode with double penalties
- Configurable thresholds

---

## Migration Guide

See [MIGRATION.md](MIGRATION.md) for detailed upgrade instructions from v1.3.x to v1.4.0.

## Contributing

When adding new rules:
1. Add rule definition to `config/rules.yaml`
2. Add test case to `tests/test_violations.*`
3. Run tests to verify: `python tests/test_rules.py`
4. Update this CHANGELOG under `[Unreleased]`
