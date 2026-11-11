# -*- coding: utf-8 -*-
"""走神提醒功能测试（unittest，纯逻辑部分）
运行：python -m unittest test_wander -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class WanderLogicTest(unittest.TestCase):
    """空闲阈值判定与走神记录读写"""

    @classmethod
    def setUpClass(cls):
        import focus
        cls.focus = focus

    def test_idle_below_limit_not_due(self):
        self.assertFalse(self.focus.wander_due(179, False, limit=180))

    def test_idle_at_limit_is_due(self):
        self.assertTrue(self.focus.wander_due(180, False, limit=180))

    def test_idle_over_limit_but_already_warned_not_due(self):
        self.assertFalse(self.focus.wander_due(600, True, limit=180))

    def test_default_limit_is_one_minute(self):
        # 未显式传 limit 时，默认阈值应为 1 分钟（60 秒）
        self.assertFalse(self.focus.wander_due(59, False))
        self.assertTrue(self.focus.wander_due(60, False))

    def test_append_and_load_wander_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            orig = self.focus.WANDER_FILE
            self.focus.WANDER_FILE = Path(td) / 'wander.json'
            try:
                self.assertEqual(self.focus.load_wander(), [])
                rec = self.focus.append_wander('概统作业', 1760000000, 181, '去刷手机了')
                self.assertEqual(rec['task'], '概统作业')
                self.assertEqual(rec['idle_seconds'], 181)
                self.assertEqual(rec['note'], '去刷手机了')
                self.assertIn('at', rec)
                items = self.focus.load_wander()
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]['note'], '去刷手机了')
                # 第二条：不填写的也存档，note 为空
                self.focus.append_wander('概统作业', 1760001000, 200, '')
                items = self.focus.load_wander()
                self.assertEqual(len(items), 2)
                self.assertEqual(items[1]['note'], '')
            finally:
                self.focus.WANDER_FILE = orig

    def test_corrupt_wander_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as td:
            orig = self.focus.WANDER_FILE
            self.focus.WANDER_FILE = Path(td) / 'wander.json'
            try:
                self.focus.WANDER_FILE.write_text('{not json', encoding='utf-8')
                self.assertEqual(self.focus.load_wander(), [])
            finally:
                self.focus.WANDER_FILE = orig


if __name__ == '__main__':
    unittest.main()
