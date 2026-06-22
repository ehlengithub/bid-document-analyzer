import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_customer_delivery.py"
SPEC = importlib.util.spec_from_file_location("check_customer_delivery", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


class CustomerDeliveryLeakCheckTest(unittest.TestCase):
    def assert_leak(self, text: str, expected: bool) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text(text, encoding="utf-8")
            failures = checker.find_leaks(
                [path],
                checker.DEFAULT_PATTERNS + checker.CUSTOMER_PROCESS_PATTERNS,
            )
        self.assertEqual(bool(failures), expected, failures)

    def test_allows_tender_numeric_ranges_without_service_pricing_context(self) -> None:
        self.assert_leak(
            "投标报价要求：设备高度1200-1800mm，安装距离300-600mm，按招标文件技术参数响应。",
            False,
        )

    def test_blocks_known_ranges_when_near_service_pricing_context(self) -> None:
        self.assert_leak("商务标+技术标：1200-1800。经济标格式整理300-600。", True)

    def test_blocks_explicit_service_quote_terms(self) -> None:
        self.assert_leak("服务报价：一组两陪1600-2200，打印胶装另算。", True)

    def test_blocks_customer_facing_process_markers(self) -> None:
        self.assert_leak("先确认什么、少了怎样、今天先做什么 | 最新技能重跑版", True)
        self.assert_leak("手机紧凑表格版 | 投标判断", True)

    def test_blocks_customer_facing_qa_wording(self) -> None:
        self.assert_leak("图文要求：全文检索未见明确要求。", True)
        self.assert_leak("原文截止已过；当前日期是2026年6月22日。", True)


if __name__ == "__main__":
    unittest.main()
