"""Change report generator service."""

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


def generate_change_report(run_id: str, diffs: dict[str, Any], findings: dict[str, Any]) -> str:
    """Generate a change report JSON file for a run.

    Args:
        run_id: The run identifier
        diffs: Dictionary containing diff summary data
        findings: Dictionary containing analyzer findings

    Returns:
        Path to the generated JSON file (absolute path as string)

    Raises:
        OSError: If the directory cannot be created or file cannot be written
    """
    # Create artifacts directory structure: artifacts/<run_id>/
    artifacts_dir = Path("artifacts") / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Create the change report JSON structure
    report = {
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "diff_summary": diffs,
        "analyzer_findings": findings,
    }

    # Write JSON file
    report_path = artifacts_dir / "change_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Return absolute path as string
    return str(report_path.absolute())

