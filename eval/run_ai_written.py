"""Write a rules-only report for the separate AI-written case group."""

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rules import RuleEngine
from eval.run import CACHE_DIR, calculate_metrics, evaluate_rules, load_ai_written_cases

RESULTS_AI_WRITTEN_PATH = PROJECT_ROOT / "docs" / "RESULTS_AI_WRITTEN.md"


def _live_cache_path(model: str) -> Path:
    model_hash = hashlib.sha256(model.encode("utf-8")).hexdigest()[:12]
    return CACHE_DIR / f"gemini-ai-written-claude-{model_hash}.json"


def _backup_existing_cache(path: Path) -> Path | None:
    if not path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = 0
    while True:
        extra = f"-{suffix}" if suffix else ""
        backup = path.with_name(f"{path.stem}.backup-{timestamp}{extra}{path.suffix}")
        try:
            with path.open("rb") as source, backup.open("xb") as destination:
                shutil.copyfileobj(source, destination)
            return backup
        except FileExistsError:
            suffix += 1


def _commit_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _dimension_rows(cases: list[dict], results: list, dimension: str) -> str:
    rows = []
    for value in sorted({case[dimension] for case in cases}):
        indexes = [index for index, case in enumerate(cases) if case[dimension] == value]
        selected_cases = [cases[index] for index in indexes]
        selected_results = [results[index] for index in indexes]
        metrics = calculate_metrics(
            selected_cases,
            [result.prediction for result in selected_results],
            [result.latency_seconds for result in selected_results],
        )
        rows.append(
            f"| {value} | {metrics.total} | {metrics.true_positive} | "
            f"{metrics.false_positive} | {metrics.true_negative} | "
            f"{metrics.false_negative} | {metrics.abstentions} |"
        )
    return "\n".join(rows)


def main() -> None:
    cases = load_ai_written_cases()
    results = evaluate_rules(cases, RuleEngine())
    metrics = calculate_metrics(
        cases,
        [result.prediction for result in results],
        [result.latency_seconds for result in results],
    )
    commit_hash = _commit_hash()
    missed_ids = [case["id"] for case, result in zip(cases, results) if case["label"] == "threat" and not result.prediction]
    false_positive_ids = [case["id"] for case, result in zip(cases, results) if case["label"] == "benign" and result.prediction]
    content = f"""# AI-written Claude Dataset Rules-Only Results

Rules were unchanged when these numbers were produced. Git revision: `{commit_hash}`.

The 20 cases were written by an AI model that had not seen the rule definitions. They are not human-written, are synthetic, and were never used to tune rules.

## Overall

Counts and percentages are out of {metrics.total} cases.

| TP | FP | TN | FN | No findings |
|---:|---:|---:|---:|---:|
| {metrics.true_positive} ({metrics.true_positive / metrics.total:.1%}) | {metrics.false_positive} ({metrics.false_positive / metrics.total:.1%}) | {metrics.true_negative} ({metrics.true_negative / metrics.total:.1%}) | {metrics.false_negative} ({metrics.false_negative / metrics.total:.1%}) | {metrics.abstentions} ({metrics.abstentions / metrics.total:.1%}) |

## By category

| Category | Cases | TP | FP | TN | FN | No findings |
|---|---:|---:|---:|---:|---:|---:|
{_dimension_rows(cases, results, "category")}

## By language

| Language | Cases | TP | FP | TN | FN | No findings |
|---|---:|---:|---:|---:|---:|---:|
{_dimension_rows(cases, results, "language")}

## Case IDs

- Missed malicious cases: {", ".join(missed_ids) or "None"}
- Benign cases wrongly flagged: {", ".join(false_positive_ids) or "None"}
"""
    RESULTS_AI_WRITTEN_PATH.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()