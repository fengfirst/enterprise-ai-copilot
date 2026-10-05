
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.evaluation import run_eval


class TestQualityGate(unittest.TestCase):
    def test_failed_case_fails_quality_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = temp_path / "dataset.json"

            # dataset = [
            #     {
            #         "id": "failure_test",
            #         "message": "测试问题",
            #         "expected_type": "rag",
            #         "required_keywords": ["必须出现但实际不会出现的内容"],
            #     }
            # ]
            dataset = [
                {
                    "id": "failure_test",
                    "question": "测试问题",
                    "category": "knowledge",
                    "expected_answer": "模拟答案",
                    "should_answer": True,
                    "required_keywords": [
                        "必须出现但实际不会出现的内容"
                    ],
                    "expected_source": None,
                }
            ]

            dataset_path.write_text(
                json.dumps(dataset, ensure_ascii=False),
                encoding="utf-8",
            )

            
            with (
                patch.object(run_eval, "DATASET_PATH", dataset_path),
                patch.object(
                    run_eval,
                    "handle_message",
                    return_value={
                        "type": "rag",
                        "answer": "这是一个模拟答案",
                        "results": [],
                    },
                ),
            ):
                original_cwd = Path.cwd()
                try:
                    os.chdir(temp_path)
                    success = run_eval.run_evaluation()
                finally:
                    os.chdir(original_cwd)

            self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()