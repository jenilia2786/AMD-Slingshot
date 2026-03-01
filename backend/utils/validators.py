"""Input validators for AccelerateAI"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> dict:
    issues = []
    if len(password) < 8:
        issues.append("Minimum 8 characters required")
    if not re.search(r'[A-Z]', password):
        issues.append("At least one uppercase letter required")
    if not re.search(r'[0-9]', password):
        issues.append("At least one number required")
    return {"valid": len(issues) == 0, "issues": issues}


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """Basic XSS prevention"""
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    return text[:max_length]


def validate_reward(amount: int) -> bool:
    return 200 <= amount <= 1000


def validate_stipend(amount: int) -> bool:
    return amount >= 1000
