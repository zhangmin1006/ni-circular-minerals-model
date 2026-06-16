"""
Loader for ../data/data_register.csv — the single source of truth for the model's
real anchors, policy targets and proxy parameters.

Previously these values were hand-copied into seed_parameters.py and the module
defaults, which risked silent drift between the documented evidence base and the
numbers the model actually ran on. This loader makes the register authoritative:
seed_parameters, the MFA and the scenario runner now read their values from here,
so editing the CSV (e.g. after a supplier survey) updates the model directly.
"""

import csv
import os

REGISTER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "data_register.csv")


def load_data_register(path=REGISTER_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return {row["parameter"]: row for row in csv.DictReader(f, skipinitialspace=True)}


_REGISTER = None


def _register():
    global _REGISTER
    if _REGISTER is None:
        _REGISTER = load_data_register()
    return _REGISTER


def value(name, default=None):
    """Return the numeric value of a register parameter, or `default` if the
    parameter is missing or non-numeric (e.g. NA / placeholder matrices)."""
    row = _register().get(name)
    if row is None:
        return default
    raw = row.get("value", "")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def status(name, default="proxy"):
    row = _register().get(name)
    return row.get("status", default) if row else default
