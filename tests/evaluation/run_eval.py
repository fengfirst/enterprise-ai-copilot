
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from backend.agent.service import handle_message



DATASET_PATH = Path("tests/evaluation/dataset.json")


def normalize_text(text: str) -> str:
    return (
        text
        .replace("—", "-")
        .replace("–", "-")
        .replace("－", "-")
        .replace("～", "~")
        .replace(" ", "")
    )


def contains_keywords(
    answer: str,
    keywords: list[str],
) -> bool:
    normalized_answer = normalize_text(answer)

    return all(
        normalize_text(keyword) in normalized_answer
        for keyword in keywords
    )


def evaluate_case(case: dict) -> dict:
    result = handle_message(case["message"])
    reasons = []

    if result["type"] != case["expected_type"]:
        reasons.append(
            f"type expected={case['expected_type']} "
            f"actual={result['type']}"
        )

    expected_tool = case.get("expected_tool")

    if expected_tool:
        actual_tool = result.get("tool")

        if actual_tool != expected_tool:
            reasons.append(
                f"tool expected={expected_tool} "
                f"actual={actual_tool}"
            )

    required_keywords = case.get("required_keywords", [])

    if required_keywords and not contains_keywords(
        result["answer"],
        required_keywords,
    ):
        reasons.append("missing required keywords")

    return {
        "id": case["id"],
        "message": case["message"],
        "passed": len(reasons) == 0,
        "reasons": reasons,
    }


def run_evaluation() -> bool:
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        dataset = json.load(f)

    if not dataset:
        print("[ERROR] Evaluation dataset is empty.")
        return False

    results = []

    for case in dataset:
        try:
            result = evaluate_case(case)
        except Exception as exc:
            result = {
                "id": case.get("id", "unknown"),
                "message": case.get("message", ""),
                "passed": False,
                "reasons": [
                    f"execution error: {type(exc).__name__}: {exc}"
                ],
            }

        results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"[{status}] "
            f"{result['id']} "
            f"{result['message']}"
        )

        for reason in result["reasons"]:
            print(f"    - {reason}")

    total = len(results)
    passed_count = sum(
        result["passed"] for result in results
    )
    failed_count = total - passed_count
    pass_rate = passed_count / total

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": round(pass_rate, 4),
        "quality_gate": "PASSED" if failed_count == 0 else "FAILED",
        "results": results,
    }

    report_dir = Path("reports/evaluation")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "latest.json"

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Report saved: {report_path}")

    print()
    print("========== Evaluation ==========")
    print(f"Total: {total}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Pass Rate: {pass_rate:.2%}")

    if failed_count:
        print()
        print("[QUALITY GATE] FAILED")
        print("Some evaluation cases did not pass.")
        return False

    print()
    print("[QUALITY GATE] PASSED")
    return True


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)