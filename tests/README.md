# VibeGuard Test Suite

This directory contains tests for the VibeGuard code quality scanner.

## Test Files

### Violation Test Files (Deliberate Failures)
These files contain deliberate code quality violations to verify the scanner works:

- `test_violations.py` - Python security and code smell violations
- `test_violations.js` - JavaScript anti-patterns
- `test_violations.md` - Documentation violations

### Unit Tests
- `test_rules.py` - Tests for the RulesManager module
- `test_scanner.py` - Tests for the CodeScanner module

## Running Tests

### Run Unit Tests
```bash
# Run rules tests
python tests/test_rules.py

# Run scanner tests
python tests/test_scanner.py
```

### Test the Scanner on Violation Files
```bash
# Scan the test violations directory
python vibeguard_new.py --directory tests --threshold 0
```

This should detect multiple violations in the test files.

### Run with pytest (optional)
```bash
pip install pytest pytest-cov
pytest tests/ -v
```

## Expected Behavior

The violation test files (`test_violations.*`) should trigger multiple rule violations when scanned:

- Security violations (hardcoded credentials, eval usage, etc.)
- Code smell violations (var keyword, console.log, etc.)
- Documentation violations (passive voice, click here links, etc.)
- Violations with `# vibeguard:ignore` comments should be skipped

The unit tests (`test_rules.py`, `test_scanner.py`) should all pass.
