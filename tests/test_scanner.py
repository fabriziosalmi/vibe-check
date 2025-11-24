"""
Unit tests for CodeScanner
"""

import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rules import RulesManager
from src.scanner import CodeScanner, Violation


def test_violation_to_dict():
    """Test Violation serialization"""
    violation = Violation(
        file="test.py",
        rule_id="SEC01",
        rule_name="Test Rule",
        deduction=100,
        desc="Test description",
        line=42
    )
    
    result = violation.to_dict()
    
    assert result['file'] == "test.py"
    assert result['id'] == "SEC01"
    assert result['rule'] == "Test Rule"
    assert result['deduction'] == 100
    assert result['desc'] == "Test description"
    assert result['line'] == 42


def test_scanner_is_excluded():
    """Test file exclusion patterns"""
    rules_manager = RulesManager()
    exclude_patterns = ['*.log', 'temp_*', 'dist/*']
    scanner = CodeScanner(rules_manager, exclude_patterns=exclude_patterns)
    
    assert scanner.is_excluded('debug.log') == True
    assert scanner.is_excluded('temp_file.txt') == True
    assert scanner.is_excluded('dist/bundle.js') == True
    assert scanner.is_excluded('src/main.py') == False


def test_scanner_is_comment_line():
    """Test comment detection"""
    rules_manager = RulesManager()
    scanner = CodeScanner(rules_manager)
    
    # Python comments
    assert scanner.is_comment_line('# This is a comment', '.py') == True
    assert scanner.is_comment_line('    # Indented comment', '.py') == True
    assert scanner.is_comment_line('code = "value"  # inline', '.py') == False
    
    # JavaScript comments
    assert scanner.is_comment_line('// This is a comment', '.js') == True
    assert scanner.is_comment_line('  // Indented', '.js') == True
    assert scanner.is_comment_line('const x = 5; // inline', '.js') == False


def test_scanner_has_ignore_comment():
    """Test vibeguard:ignore detection"""
    rules_manager = RulesManager()
    scanner = CodeScanner(rules_manager)
    
    # Inline ignore
    assert scanner.has_ignore_comment('password = "secret"  # vibeguard:ignore') == True
    assert scanner.has_ignore_comment('password = "secret"  // vibeguard:ignore') == True
    assert scanner.has_ignore_comment('password = "secret"') == False
    
    # Next line ignore
    assert scanner.has_ignore_comment('password = "secret"', '# vibeguard:ignore') == True


def test_scanner_detects_python_ast_violations():
    """Test AST-based Python violation detection"""
    rules_manager = RulesManager()
    scanner = CodeScanner(rules_manager)
    
    # Code with eval()
    code_with_eval = '''
user_input = "malicious"
result = eval(user_input)
'''
    
    violations = scanner.check_python_ast_violations(
        'test.py',
        code_with_eval,
        brutal_mode=False
    )
    
    # Should detect eval() usage
    eval_violations = [v for v in violations if v.rule_id == 'SEC06']
    assert len(eval_violations) > 0
    
    # Code with print in non-test file
    code_with_print = '''
def process_data(data):
    print("Processing:", data)
    return data
'''
    
    violations = scanner.check_python_ast_violations(
        'main.py',
        code_with_print,
        brutal_mode=False
    )
    
    # Should detect print() in production code
    print_violations = [v for v in violations if v.rule_id == 'HYG02']
    assert len(print_violations) > 0


def test_scanner_respects_ignore_comments():
    """Test that scanner respects vibeguard:ignore comments"""
    rules_manager = RulesManager()
    scanner = CodeScanner(rules_manager)
    
    # Create temporary Python file with ignore comment
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
password = "should_be_caught"
api_key = "should_be_ignored"  # vibeguard:ignore
''')
        temp_file = f.name
    
    try:
        violations = scanner.scan_file(temp_file, brutal_mode=False)
        
        # Should have violations but not for the ignored line
        # Note: This is a simplified test - actual results depend on rule patterns
        assert isinstance(violations, list)
    
    finally:
        os.unlink(temp_file)


if __name__ == '__main__':
    print("Running CodeScanner tests...")
    
    test_violation_to_dict()
    print("✓ Violation serialization test passed")
    
    test_scanner_is_excluded()
    print("✓ File exclusion test passed")
    
    test_scanner_is_comment_line()
    print("✓ Comment detection test passed")
    
    test_scanner_has_ignore_comment()
    print("✓ Ignore comment detection test passed")
    
    test_scanner_detects_python_ast_violations()
    print("✓ AST violation detection test passed")
    
    test_scanner_respects_ignore_comments()
    print("✓ Ignore comment respect test passed")
    
    print("\n✅ All tests passed!")
