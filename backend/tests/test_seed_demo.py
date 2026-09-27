"""seed_demo's summary line: "Would add" only for a dry run, "Added" after a real run. No database needed."""

from scripts.seed_demo import summary


def test_dry_run_says_would_add():
    assert summary(12, 5, dry_run=True) == "Would add 12 tasks and 5 journal entries."


def test_real_run_says_added():
    assert summary(12, 5, dry_run=False) == "Added 12 tasks and 5 journal entries."
