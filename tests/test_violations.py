"""
Test file with deliberate security violations
This should be caught by VibeGuard scanner
"""

# SEC04: Hardcoded password
password = "mySecretPassword123"

# SEC05: Hardcoded API key
api_key = "sk_live_1234567890abcdef"

# SEC06: eval() usage
user_input = "print('hello')"
eval(user_input)

# SEC07: SQL concatenation (SQL injection risk)
query = "SELECT * FROM users WHERE id = " + user_id + " AND active = TRUE"

# HYG02: Print statement in production code
print("Debug: processing user data")

# STB02: Bare except
try:
    risky_operation()
except:
    pass

# This line should be ignored with inline comment
password2 = "ignored_password"  # vibeguard:ignore

# SME01: var keyword equivalent (Python global)
GLOBAL_STATE = {}

# vibeguard:ignore
# This whole section should be ignored
hardcoded_token = "ghp_secrettoken12345"
