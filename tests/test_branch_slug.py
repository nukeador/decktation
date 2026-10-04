"""Branch preview paths remain readable and deterministic."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "branch-slug.py"
SPEC = importlib.util.spec_from_file_location("branch_slug", SCRIPT)
branch_slug = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(branch_slug)


def test_slash_separated_branch_is_readable():
    assert branch_slug.branch_slug("feat/haptic-feedback") == "feat-haptic-feedback"


def test_lossy_slug_has_stable_identity_suffix():
    first = branch_slug.branch_slug("feature/chat polish")
    second = branch_slug.branch_slug("feature/chat polish")
    assert first == second
    assert first.startswith("feature-chat-polish-")
    assert len(first.rsplit("-", 1)[1]) == 10


def test_empty_branch_has_fallback():
    assert branch_slug.branch_slug("") == "branch"
