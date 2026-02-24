"""
Tests for the AST-level security validator in QueryAgent.
These run entirely offline — no LLM, no network.
"""
import pytest
import sys
import os

# Allow importing from backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.query_agent import _validate_ast


# ── Safe expressions that must pass ────────────────────────────────────────── #

SAFE = [
    "df['revenue'].sum()",
    "df[df['status'] == 'active'].groupby('region')['sales'].sum().reset_index()",
    "df['price'].mean()",
    "len(df)",
    "df.head(10)",
    "df['date'].max()",
    "df[df['amount'] > 100]['category'].value_counts().reset_index()",
    "pd.to_datetime(df['date']).dt.year.value_counts().reset_index()",
    "df.groupby('product')['qty'].sum().sort_values(ascending=False).reset_index()",
    "round(df['margin'].mean(), 2)",
    "df[['name', 'revenue']].sort_values('revenue', ascending=False).head(5)",
]

@pytest.mark.parametrize("code", SAFE)
def test_safe_expressions_pass(code):
    """Legitimate pandas expressions must not raise."""
    _validate_ast(code)  # should not raise


# ── Dangerous expressions that must be blocked ─────────────────────────────── #

DANGEROUS = [
    # Import statements
    ("import os", "Disallowed AST node"),
    ("__import__('os')", "Forbidden attribute"),
    # Class hierarchy traversal
    ("().__class__.__bases__[0].__subclasses__()", "Forbidden attribute"),
    ("df.__class__.__bases__", "Forbidden attribute"),
    # Builtins escape
    ("eval('1+1')", "Disallowed call"),
    ("exec('import os')", "Disallowed call"),
    # Open / file system
    ("open('/etc/passwd').read()", "Disallowed call"),
    # Disallowed names
    ("globals()", "Disallowed call"),
    ("locals()", "Disallowed call"),
    # Function definitions
    ("lambda x: x", "Disallowed AST node"),
    # Walrus / assignment expressions
    ("(x := 1)", "Disallowed AST node"),
]

@pytest.mark.parametrize("code,expected_fragment", DANGEROUS)
def test_dangerous_expressions_blocked(code, expected_fragment):
    """Dangerous constructs must raise ValueError."""
    with pytest.raises((ValueError, SyntaxError)):
        _validate_ast(code)


# ── Edge cases ──────────────────────────────────────────────────────────────── #

def test_empty_string_raises():
    with pytest.raises((ValueError, SyntaxError)):
        _validate_ast("")

def test_multiline_raises():
    """Statements (not expressions) must be rejected."""
    with pytest.raises((ValueError, SyntaxError)):
        _validate_ast("x = 1\ndf['x']")

def test_none_literal_passes():
    _validate_ast("None")

def test_numeric_literal_passes():
    _validate_ast("42")
