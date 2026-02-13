"""Smoke tests for fin-reasoning-eval."""
import os, glob
def test_problems_exist():
    d = os.path.join(os.path.dirname(__file__), "..", "problems")
    assert os.path.isdir(d) and glob.glob(os.path.join(d, "**/*"), recursive=True)
def test_evaluation_exists():
    assert os.path.isdir(os.path.join(os.path.dirname(__file__), "..", "evaluation"))
