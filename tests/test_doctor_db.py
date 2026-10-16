"""验证列表完整性、CSV 即时更新、精确查询与损坏数据的处理。"""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'doctor_db.py'
spec = importlib.util.spec_from_file_location('doctor_db', SCRIPT)
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)


class DoctorDbTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=10)

    def test_all_filtered_rows_in_both_formats(self):
        rows = db.rows_from(SCRIPT.parent.parent / 'data/doctors.csv')
        expected = [r for r in rows if '上海' in r['城市']]
        data = json.loads(self.run_cli('--city', '上海', '--json').stdout)
        self.assertEqual(data['rows'], expected)
        self.assertEqual(data['count'], len(expected))
        lines = self.run_cli('--city', '上海').stdout.splitlines()
        self.assertEqual(len(lines) - 1, len(expected))
        for row, line in zip(expected, lines[1:]):
            self.assertIn(row['姓名'], line)
            self.assertIn(row['备注'], line)

    def test_exact_name_and_new_doctor(self):
        for name in ('钱黎俊', '郭亚荣'):
            data = json.loads(self.run_cli('--name', name, '--json').stdout)
            self.assertEqual([r['姓名'] for r in data['rows']], [name])

    def test_name_keyword_has_no_unrelated_cross_references(self):
        data = json.loads(self.run_cli('--query', '钱黎俊', '--json').stdout)
        self.assertEqual([r['姓名'] for r in data['rows']], ['钱黎俊'])

    def test_trials_and_zero_matches(self):
        rows = db.rows_from(SCRIPT.parent.parent / 'data/trials.csv', 'trials')
        data = json.loads(self.run_cli('--table', 'trials', '--list', '--json').stdout)
        self.assertEqual(data['rows'], rows)
        self.assertEqual(len(self.run_cli('--table', 'trials').stdout.splitlines()) - 1, len(rows))
        self.assertEqual(json.loads(self.run_cli('--name', '不存在的测试医生', '--json').stdout)['count'], 0)

    def test_csv_update_without_rebuild_and_full_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'doctors.csv'
            row = dict.fromkeys(db.REQUIRED['doctors'], '测试')
            row.update({'序号': '1', '来源日期': '2026-10-16', '备注': '完整备注' * 100 + ',含逗号\n第二行'})
            def save(rows):
                with path.open('w', encoding='utf-8-sig', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=list(row));w.writeheader();w.writerows(rows)
            save([row])
            self.assertEqual(self.run_cli('--db', str(path), '--validate').returncode, 0)
            output = self.run_cli('--db', str(path)).stdout
            self.assertIn(row['备注'].replace('\n', '\\n'), output)
            save([row, dict(row, 序号='2', 姓名='新增')])
            self.assertEqual(json.loads(self.run_cli('--db', str(path), '--json').stdout)['count'], 2)
            self.assertEqual(self.run_cli('--db', str(path), '--validate').returncode, 0)
            save([row, row])
            self.assertNotEqual(self.run_cli('--db', str(path), '--validate').returncode, 0)

    def test_failures(self):
        self.assertNotEqual(self.run_cli('--list', '--query', '上海').returncode, 0)
        self.assertNotEqual(self.run_cli('--db', '/nonexistent/doctors.csv').returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.csv';path.write_text('name\n测试\n')
            self.assertNotEqual(self.run_cli('--db', str(path), '--validate').returncode, 0)


if __name__ == '__main__':
    unittest.main()
