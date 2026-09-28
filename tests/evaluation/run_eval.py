import json

from backend.agent.service import handle_message


DATASET_PATH = "tests/evaluation/dataset.json"


def normalize_text(text: str) -> str:
    return (
        text
        .replace("—", "-")
        .replace("–", "-")
        .replace("－", "-")
        .replace("～", "~")
        .replace(" ", "")
    )


def contains_keywords(answer: str, keywords: list[str]) -> bool:
    normalized_answer = normalize_text(answer)

    return all(
        normalize_text(keyword) in normalized_answer
        for keyword in keywords
    )


def run_evaluation():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for case in dataset:
        result = handle_message(case["message"])

        passed = True
        reasons = []

        if result["type"] != case["expected_type"]:
            passed = False
            reasons.append(
                f"type expected={case['expected_type']} "
                f"actual={result['type']}"
            )

        expected_tool = case.get("expected_tool")

        if expected_tool:
            actual_tool = result.get("tool")

            if actual_tool != expected_tool:
                passed = False
                reasons.append(
                    f"tool expected={expected_tool} "
                    f"actual={actual_tool}"
                )

        required_keywords = case.get(
            "required_keywords",
            [],
        )

        if required_keywords:
            if not contains_keywords(
                result["answer"],
                required_keywords,
            ):
                passed = False
                reasons.append(
                    "missing required keywords"
                )

        results.append(
            {
                "id": case["id"],
                "passed": passed,
                "reasons": reasons,
            }
        )

        status = "PASS" if passed else "FAIL"

        print(
            f"[{status}] "
            f"{case['id']} "
            f"{case['message']}"
        )

        if reasons:
            for reason in reasons:
                print(f"    - {reason}")

    passed_count = sum(
        item["passed"]
        for item in results
    )

    total = len(results)

    print()
    print("========== Evaluation ==========")
    print(f"Total: {total}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total - passed_count}")
    print(f"Pass Rate: {passed_count / total:.2%}")

    return results


if __name__ == "__main__":
    run_evaluation()