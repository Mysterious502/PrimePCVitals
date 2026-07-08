import json
import os
import sys


def _resource_path(relative_path):
    """Works both in dev (python main.py) and in PyInstaller .exe bundle."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), "..", relative_path)


DATA_PATH = _resource_path(os.path.join("data", "recommendations.json"))


def load_rules():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def analyze_missing_tools(installed_app_names):
    """
    installed_app_names: list[str] (lowercased app display names)
    Pure string matching — zero CPU/RAM cost, no AI needed.
    """
    rules = load_rules()
    lowered = [name.lower() for name in installed_app_names]
    results = []

    for category, rule in rules.items():
        found = any(
            any(keyword in app for app in lowered)
            for keyword in rule["keywords"]
        )
        if not found:
            results.append({
                "category": category.replace("_", " ").title(),
                "message": rule["message"],
                "suggestions": rule["suggestions"],
            })

    return results