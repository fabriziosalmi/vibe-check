"""
Unit tests for RulesManager
"""

import os
import sys
import tempfile
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rules import RulesManager


def test_rules_manager_loads_rules():
    """Test that rules manager loads rules from YAML"""
    rules_manager = RulesManager()
    assert len(rules_manager) > 0
    assert len(rules_manager.get_active_rules()) > 0


def test_rules_manager_ignores_rules():
    """Test that rules can be ignored via configuration"""
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {"ignore": ["SEC01", "HYG01"]}
        json.dump(config, f)
        config_path = f.name
    
    try:
        rules_manager = RulesManager()
        rules_manager.load_config(config_path)
        
        assert 'SEC01' in rules_manager.ignore_rules
        assert 'HYG01' in rules_manager.ignore_rules
        
        # Verify rules are actually filtered
        active_rules = rules_manager.get_active_rules()
        rule_ids = [r['id'] for r in active_rules]
        
        assert 'SEC01' not in rule_ids
        assert 'HYG01' not in rule_ids
    
    finally:
        os.unlink(config_path)


def test_rules_manager_get_rule_by_id():
    """Test retrieving a specific rule by ID"""
    rules_manager = RulesManager()
    rule = rules_manager.get_rule_by_id('SEC01')
    
    assert rule is not None
    assert rule['id'] == 'SEC01'
    assert 'weight' in rule
    assert 'type' in rule


def test_rules_manager_get_critical_rules():
    """Test retrieving only critical rules"""
    rules_manager = RulesManager()
    critical_rules = rules_manager.get_critical_rules()
    
    assert len(critical_rules) > 0
    
    for rule in critical_rules:
        assert rule.get('critical', False) == True


def test_rules_manager_calculate_penalty():
    """Test penalty calculation with brutal mode"""
    rules_manager = RulesManager()
    rule = rules_manager.get_rule_by_id('SEC01')
    
    normal_penalty = rules_manager.calculate_penalty(rule, brutal_mode=False)
    brutal_penalty = rules_manager.calculate_penalty(rule, brutal_mode=True)
    
    assert brutal_penalty == normal_penalty * 2


def test_rules_manager_get_rules_by_type():
    """Test filtering rules by type"""
    rules_manager = RulesManager()
    
    regex_rules = rules_manager.get_rules_by_type('regex')
    filename_rules = rules_manager.get_rules_by_type('filename')
    
    assert len(regex_rules) > 0
    assert len(filename_rules) > 0
    
    for rule in regex_rules:
        assert rule['type'] == 'regex'
    
    for rule in filename_rules:
        assert rule['type'] == 'filename'


if __name__ == '__main__':
    # Run basic tests
    print("Running RulesManager tests...")
    
    test_rules_manager_loads_rules()
    print("✓ Rules loading test passed")
    
    test_rules_manager_ignores_rules()
    print("✓ Rule ignoring test passed")
    
    test_rules_manager_get_rule_by_id()
    print("✓ Get rule by ID test passed")
    
    test_rules_manager_get_critical_rules()
    print("✓ Critical rules test passed")
    
    test_rules_manager_calculate_penalty()
    print("✓ Penalty calculation test passed")
    
    test_rules_manager_get_rules_by_type()
    print("✓ Get rules by type test passed")
    
    print("\n✅ All tests passed!")
