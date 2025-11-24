"""
Rules Management Module
Handles loading, filtering, and validation of VibeGuard rules
"""

import os
import yaml
from typing import List, Dict, Set, Any


class RulesManager:
    """Manages loading and filtering of audit rules"""
    
    def __init__(self, rules_path: str = None):
        """
        Initialize the rules manager
        
        Args:
            rules_path: Path to rules.yaml file. Defaults to config/rules.yaml
        """
        if rules_path is None:
            # Default to config/rules.yaml relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rules_path = os.path.join(project_root, 'config', 'rules.yaml')
        
        self.rules_path = rules_path
        self.rules: List[Dict[str, Any]] = []
        self.ignore_rules: Set[str] = set()
        self.load_rules()
    
    def load_rules(self) -> None:
        """Load rules from YAML configuration file"""
        if not os.path.exists(self.rules_path):
            raise FileNotFoundError(f"Rules file not found: {self.rules_path}")
        
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            rules_data = yaml.safe_load(f)
        
        # Flatten rules from categorized structure
        self.rules = []
        for category, rules_list in rules_data.items():
            for rule in rules_list:
                rule['category'] = category
                self.rules.append(rule)
    
    def load_config(self, config_path: str = '.vibeguardrc') -> None:
        """
        Load user configuration to ignore specific rules
        
        Args:
            config_path: Path to .vibeguardrc configuration file
        """
        if not os.path.exists(config_path):
            return
        
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.ignore_rules = set(config.get('ignore', []))
        except Exception as e:
            # Silently fail if config is malformed
            pass
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """
        Get all rules that are not ignored
        
        Returns:
            List of active rule dictionaries
        """
        return [r for r in self.rules if r['id'] not in self.ignore_rules]
    
    def get_rule_by_id(self, rule_id: str) -> Dict[str, Any]:
        """
        Get a specific rule by ID
        
        Args:
            rule_id: The rule identifier (e.g., 'SEC01')
        
        Returns:
            Rule dictionary or None if not found
        """
        return next((r for r in self.rules if r['id'] == rule_id), None)
    
    def get_rules_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """
        Get all active rules of a specific type
        
        Args:
            rule_type: Type of rule (e.g., 'regex', 'filename', 'path')
        
        Returns:
            List of matching rule dictionaries
        """
        return [r for r in self.get_active_rules() if r['type'] == rule_type]
    
    def get_critical_rules(self) -> List[Dict[str, Any]]:
        """
        Get all critical rules
        
        Returns:
            List of critical rule dictionaries
        """
        return [r for r in self.get_active_rules() if r.get('critical', False)]
    
    def get_rules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all active rules in a category
        
        Args:
            category: Rule category (e.g., 'security', 'stability')
        
        Returns:
            List of rule dictionaries in the category
        """
        return [r for r in self.get_active_rules() if r.get('category') == category]
    
    def calculate_penalty(self, rule: Dict[str, Any], brutal_mode: bool = False) -> int:
        """
        Calculate the penalty for a rule violation
        
        Args:
            rule: Rule dictionary
            brutal_mode: Whether brutal mode is enabled (doubles penalties)
        
        Returns:
            Penalty points
        """
        weight = rule['weight']
        return weight * 2 if brutal_mode else weight
    
    def __len__(self) -> int:
        """Return total number of rules"""
        return len(self.rules)
    
    def __repr__(self) -> str:
        """String representation"""
        active = len(self.get_active_rules())
        ignored = len(self.ignore_rules)
        return f"RulesManager({len(self.rules)} total, {active} active, {ignored} ignored)"
