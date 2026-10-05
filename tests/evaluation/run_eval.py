import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from backend.agent.service import handle_message

class HistoryMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


# ============================================================
# Phase A Evaluation Contract
# ============================================================

DATASET_PATH = Path("evaluation/dataset.json")


# ------------------------------------------------------------
# Legacy source -> Canonical source
#
# dataset 中暂时保留旧名字，
# evaluator 在比较时统一转换。
# 不修改 Agent 的真实工具名称。
# ------------------------------------------------------------
SOURCE_ALIASES = {
    "order_tool": "get_order_status",
    "refund_tool": "get_refund_status",

    "refund_policy": "refund_policy_2026",
    "refund_policy.txt": "refund_policy_2026",

    "return_policy": "return_policy_2026",
    "return_policy.txt": "return_policy_2026",
}


def canonical_source(source):
    if source is None:
        return None

    return SOURCE_ALIASES.get(source, source)


# ------------------------------------------------------------
# Text normalization
# ------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    用于 Evaluation 的文本标准化。

    目的：
    - 统一不同 Unicode 连字符
    - 统一部分特殊空白
    - 消除普通空格和换行

    不做语义改写。
    """

    if text is None:
        return ""

    return (
        str(text)
        .replace("—", "-")
        .replace("–", "-")
        .replace("－", "-")
        .replace("−", "-")
        .replace("～", "~")
        .replace("　", " ")
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
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


# ------------------------------------------------------------
# Abstention detection
# ------------------------------------------------------------

ABSTENTION_MARKERS = [
    "不知道",
    "无法",
    "无法查询",
    "无法回答",
    "没有找到",
    "未找到",
    "没有相关信息",
    "暂无相关信息",
    "知识库中没有",
    "知识库没有",
    "没有足够的信息",
    "信息不足",
    "无法提供",
]


def is_abstention(answer: str) -> bool:
    normalized = normalize_text(answer)

    return any(
        normalize_text(marker) in normalized
        for marker in ABSTENTION_MARKERS
    )


def extract_sources(result: dict) -> list[str]:
    """
    提取 Agent 本次执行涉及的所有 source。
    """

    sources = []

    # Tool / explicit source
    for key in ("source", "actual_source", "tool"):
        value = result.get(key)
        if value:
            sources.append(canonical_source(value))

    # RAG results
    for item in result.get("results", []):
        document_id = item.get("document_id")
        if document_id:
            sources.append(canonical_source(document_id))

        metadata = item.get("metadata") or {}
        metadata_source = metadata.get("source")
        if metadata_source:
            sources.append(canonical_source(metadata_source))

    # 去重，同时保持顺序
    return list(dict.fromkeys(
        source for source in sources if source
    ))


# ------------------------------------------------------------
# A4 Answer Grounding
# ------------------------------------------------------------

def check_grounding(
    answer: str,
    results: list,
    required_keywords: list,
) -> dict:
    """
    检查回答所依赖的关键事实是否存在于检索证据中。

    第一版规则：
    1. required_keywords 必须存在于 retrieved evidence
    2. required_keywords 必须存在于 answer

    使用 normalize_text() 处理 Unicode
    标点和空白差异。

    不做语义同义词替换。
    """

    evidence_text = "\n".join(
        item.get("content", "")
        for item in results
    )

    normalized_evidence = normalize_text(
        evidence_text
    )

    normalized_answer = normalize_text(
        answer
    )

    missing_in_evidence = [
        keyword
        for keyword in required_keywords
        if normalize_text(keyword)
        not in normalized_evidence
    ]

    missing_in_answer = [
        keyword
        for keyword in required_keywords
        if normalize_text(keyword)
        not in normalized_answer
    ]

    grounded = (
        len(missing_in_evidence) == 0
        and len(missing_in_answer) == 0
    )

    return {
        "grounded": grounded,
        "missing_in_evidence": missing_in_evidence,
        "missing_in_answer": missing_in_answer,
    }


def evaluate_multi_turn_cases(cases):
    """
    A5 Multi-turn Evaluation

    multi_001 → multi_002 → multi_003
    使用同一个 history/context，模拟真实连续对话。
    """

    multi_cases = [
        case
        for case in cases
        if case.get("id", "").startswith("multi_")
    ]

    if not multi_cases:
        return []

    multi_cases.sort(key=lambda x: x["id"])

    history = []
    context = {}

    results = []

    print("\n========== Multi-turn Evaluation ==========")

    for case in multi_cases:
        question = case["question"]

        print(f"\n[MULTI] {case['id']} {question}")

        result = handle_message(
            question,
            history=history,
            context=context,
        )

        if isinstance(result.get("context"), dict):
            context.update(result["context"])

        if not isinstance(result, dict):
            result = {
                "answer": str(result),
            }

        answer = result.get("answer", "")

        print(f"    Answer: {answer}")

        # 当前轮加入历史
        history.append(
            HistoryMessage(
                role="user",
                content=question,
            )
        )

        history.append(
            HistoryMessage(
                role="assistant",
                content=answer,
            )
        )

        # 如果 Agent 返回了 context，则继续传给下一轮
        returned_context = result.get("context")

        if isinstance(returned_context, dict):
            context = returned_context

        # 当前 case 的基础验证
        expected_answer = case.get("expected_answer", "")
        required_keywords = case.get(
            "required_keywords",
            [],
        )

        reasons = []

        # if expected_answer:
        #     normalized_answer = normalize_text(answer)
        #     normalized_expected = normalize_text(expected_answer)

        #     if normalized_expected not in normalized_answer:
        #         reasons.append(
        #             f"expected answer not found: {expected_answer}"
        #         )

        # if required_keywords:
        #     if not contains_keywords(
        #         answer,
        #         required_keywords,
        #     ):
        #         reasons.append(
        #             f"missing required keywords: "
        #             f"{required_keywords}"
        #         )

        actual_sources = extract_sources(result)

        expected_source = case.get("expected_source")

        if expected_source:
            expected_source = canonical_source(
                expected_source
            )

            if expected_source not in actual_sources:
                reasons.append(
                    f"source expected={expected_source} "
                    f"actual={actual_sources}"
                )

        passed = len(reasons) == 0

        print(
            f"    {'PASS' if passed else 'FAIL'}"
        )

        for reason in reasons:
            print(f"    - {reason}")

        results.append({
            "id": case["id"],
            "category": case.get("category"),
            "question": question,
            "answer": answer,
            "expected_answer": expected_answer,
            "required_keywords": required_keywords,
            "expected_source": expected_source,
            "actual_sources": actual_sources,
            "passed": passed,
            "reasons": reasons,
        })

    return results

# ------------------------------------------------------------
# Single case evaluation
# ------------------------------------------------------------

def evaluate_case(case: dict) -> dict:

    question = case["question"]

    result = handle_message(question)

    if not isinstance(result, dict):
        raise TypeError(
            f"handle_message() returned {type(result).__name__}, "
            "expected dict"
        )

    answer = result.get("answer", "") or ""

    # A4: 判断是否为 RAG Case
    is_rag_case = result.get("type") == "rag"

    required_keywords = case.get("required_keywords", [])

    if is_rag_case:
        grounding = check_grounding(
            answer=answer,
            results=result.get("results", []),
            required_keywords=required_keywords,
        )
    else:
        grounding = {
            "grounded": None,
            "missing_in_evidence": [],
            "missing_in_answer": [],
        }

    reasons = []

    # ========================================================
    # 1. Answer expectation
    # ========================================================

    should_answer = case.get("should_answer", True)

    if should_answer is False:

        if not is_abstention(answer):

            reasons.append(
                "expected abstention but got an answer"
            )

    else:

        # should_answer=True 时，如果完全没有答案，
        # 直接判失败。
        if not answer.strip():

            reasons.append(
                "expected an answer but got empty answer"
            )

    # ========================================================
    # 2. Required keywords
    # ========================================================

    required_keywords = case.get(
        "required_keywords",
        [],
    )

    if required_keywords:

        if not contains_keywords(
            answer,
            required_keywords,
        ):

            reasons.append(
                "missing required keywords: "
                f"{required_keywords}"
            )

    # ========================================================
    # 3. Source validation
    # ========================================================

    expected_source = case.get("expected_source")

    # 必须无条件提取 actual_sources
    # 因为即使 expected_source 为 None，
    # report 也应该记录 Agent 实际返回了什么 source。
    actual_sources = extract_sources(result)

    if expected_source:
        expected_source = canonical_source(expected_source)

        if expected_source not in actual_sources:
            reasons.append(
                f"source expected={expected_source} "
                f"actual={actual_sources}"
            )

    # ========================================================
    # 4. Return normalized evaluation result
    # ========================================================

    return {
        "id": case["id"],
        "category": case.get("category"),
        "question": question,
        "grounding": grounding,
        "expected_source": expected_source,
        "actual_sources": actual_sources,
        "should_answer": should_answer,
        "answer": answer,
        "passed": len(reasons) == 0,
        "reasons": reasons,
    }


# ------------------------------------------------------------
# Main evaluation
# ------------------------------------------------------------

def run_evaluation() -> bool:

    # ========================================================
    # Load NEW dataset only
    # ========================================================

    if not DATASET_PATH.exists():

        print(
            f"[ERROR] Dataset not found: {DATASET_PATH}"
        )

        return False

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:

        dataset = json.load(f)

    if not isinstance(dataset, list):

        print(
            "[ERROR] Evaluation dataset must be a list."
        )

        return False

    if not dataset:

        print(
            "[ERROR] Evaluation dataset is empty."
        )

        return False

    print(
        f"[INFO] Dataset: {DATASET_PATH}"
    )

    print(
        f"[INFO] Cases: {len(dataset)}"
    )

    print()

    # ========================================================
    # Evaluate
    # ========================================================

    results = []

    for case in dataset:

        try:

            result = evaluate_case(case)

        except Exception as exc:

            result = {
                "id": case.get(
                    "id",
                    "unknown",
                ),
                "category": case.get(
                    "category"
                ),
                "question": case.get(
                    "question",
                    "",
                ),
                "passed": False,
                "reasons": [
                    "execution error: "
                    f"{type(exc).__name__}: {exc}"
                ],
            }

        results.append(result)

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{result['id']} "
            f"{case['question']}"
        )

        # ----------------------------------------------------
        # A4 Grounding
        # ----------------------------------------------------

        grounding = result.get("grounding")

        if grounding is not None:

            grounded = grounding.get(
                "grounded"
            )

            if grounded is True:

                print(
                    "    - GROUNDING: PASS"
                )

            elif grounded is False:

                print(
                    "    - GROUNDING: FAIL"
                )

                missing_in_evidence = (
                    grounding.get(
                        "missing_in_evidence",
                        [],
                    )
                )

                missing_in_answer = (
                    grounding.get(
                        "missing_in_answer",
                        [],
                    )
                )

                if missing_in_evidence:

                    print(
                        "      missing in evidence: "
                        f"{missing_in_evidence}"
                    )

                if missing_in_answer:

                    print(
                        "      missing in answer: "
                        f"{missing_in_answer}"
                    )

            else:

                print(
                    "    - GROUNDING: N/A"
                )

        for reason in result["reasons"]:

            print(
                f"    - {reason}"
            )

    
    
    multi_results = evaluate_multi_turn_cases(dataset)

    # multi_* 已经单独执行，不再重复作为普通单轮 case 计入
    results = [
        result
        for result in results
        if not result["id"].startswith("multi_")
    ]

    results.extend(multi_results)

    # ========================================================
    # Summary
    # ========================================================

    total = len(results)

    passed_count = sum(
        result["passed"]
        for result in results
    )

    failed_count = (
        total - passed_count
    )

    pass_rate = (
        passed_count / total
        if total
        else 0
    )

    quality_gate = (
        "PASSED"
        if failed_count == 0
        else "FAILED"
    )

    # ========================================================
    # A4 Grounding Summary
    #
    # 注意：
    # Grounding 当前只是观察指标，
    # 暂时不影响 passed / quality_gate。
    # ========================================================

    grounding_results = [
        result.get("grounding", {})
        for result in results
        if result.get("grounding", {}).get(
            "grounded"
        ) is not None
    ]

    grounding_total = len(
        grounding_results
    )

    grounding_passed = sum(
        grounding["grounded"]
        for grounding in grounding_results
    )

    grounding_failed = (
        grounding_total
        - grounding_passed
    )

    grounding_pass_rate = (
        grounding_passed / grounding_total
        if grounding_total
        else 0
    )

    report = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "dataset": str(
            DATASET_PATH
        ),

        "total": total,

        "passed": passed_count,

        "failed": failed_count,

        "pass_rate": round(
            pass_rate,
            4,
        ),

        "quality_gate": quality_gate,

        # A4 Grounding
        "grounding_summary": {
            "total": grounding_total,
            "grounded": grounding_passed,
            "not_grounded": grounding_failed,
            "grounding_pass_rate": round(
                grounding_pass_rate,
                4,
            ),
        },

        "results": results,
    }

    # ========================================================
    # Save report
    # ========================================================

    report_dir = Path(
        "reports/evaluation"
    )

    report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        report_dir
        / "latest.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # Console summary
    # ========================================================

    print()

    print(
        f"Report saved: {report_path}"
    )

    print()

    print(
        "========== Evaluation =========="
    )

    print(
        f"Total: {total}"
    )

    print(
        f"Passed: {passed_count}"
    )

    print(
        f"Failed: {failed_count}"
    )

    print(
        f"Pass Rate: {pass_rate:.2%}"
    )

    print()

    print(
        "========== Grounding =========="
    )

    print(
        f"RAG cases checked: {grounding_total}"
    )

    print(
        f"Grounded: {grounding_passed}"
    )

    print(
        f"Not grounded: {grounding_failed}"
    )

    print(
        f"Grounding Pass Rate: "
        f"{grounding_pass_rate:.2%}"
    )

    print()

    if failed_count:

        print(
            "[QUALITY GATE] FAILED"
        )

        print(
            "Some evaluation cases did not pass."
        )

        return False

    print(
        "[QUALITY GATE] PASSED"
    )

    return True


if __name__ == "__main__":

    success = run_evaluation()

    sys.exit(
        0 if success else 1
    )