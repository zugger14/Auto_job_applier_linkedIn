"""
Legacy compatibility wrapper.
External job applications are powered by the deterministic Playwright engine in
`modules/external_apply_engine.py`.
"""

from modules.external_apply_engine import run_external_apply, run_external_apply as run_browser_use_apply

__all__ = ["run_external_apply", "run_browser_use_apply"]
