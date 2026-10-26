"""Designs on the host: publishing one to the marketplace catalogue (approve-then-Run, owner only)"""
from pathlib import Path

from dash_sdk import action

PUBLISH = str(Path(__file__).resolve().parent / "design-publish")


@action("design_publish")
def a_design_publish(args):
    """a design from /designs → `_designs/<login>-<name>.json` in the marketplace repo, as a design/<slug> PR that
    GitHub checks (colours only, the publisher's own file) and merges; every install then lists it"""
    did = str(args.get("id", ""))
    if not did.isdigit():
        raise ValueError("bad design id")
    name = str(args.get("name", "")).strip()[:40] or f"design {did}"
    return (f"publish the design “{name}” to the marketplace catalogue under your GitHub login: "
            f"GitHub checks it holds only colours and corner sizes, then merges it and every install can add it.",
            ["python3", "-I", PUBLISH, did], 1800)
