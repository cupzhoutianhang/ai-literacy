import copy
import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from course_grading import apply_override, equal, feedback, grade_issue, load_catalog, parse_submission, score_answers, strict_json
from course_github import export_rows, latest_records, spreadsheet_cell, write_xlsx


def correct_answer(task):
    answer = {}
    for rule in task['rubric']:
        target = answer
        keys = rule['path'].split('.')
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        target[keys[-1]] = copy.deepcopy(rule['expected'])
    answer['process'] = {'first_prompt': '请阅读我上传的教学附件，严格依据原始资料和题目要求处理数据，生成符合提交模板的结构化结果。', 'revision_prompt': '请重新检查单位换算、缺失值和引用来源，保留原始编号，不补造数据，发现错误后逐项修正结果。'}
    return answer


def issue_body(task, answer, name='测试学生'):
    return '### 任务编号\n\n' + task['id'] + '\n\n### 姓名或课堂代号\n\n' + name + '\n\n### 班级（可选）\n\n测试班\n\n### 成果 JSON\n\n```json\n' + json.dumps(answer, ensure_ascii=False, indent=2) + '\n```\n\n### 补充附件（可选）\n\n_No response_\n\n### 提交确认\n\n- [x] 我理解公开提交\n'


def issue(task, answer):
    return {'number': 1, 'html_url': 'https://github.com/example/course/issues/1', 'user': {'login': 'real-student'}, 'body': issue_body(task, answer), 'updated_at': '2026-10-01T12:00:00Z'}


class CourseGradingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_every_task_has_full_score_solution_and_nonfull_placeholder(self):
        for task in self.catalog['tasks']:
            with self.subTest(task=task['id']):
                score, _ = score_answers(task, correct_answer(task))
                self.assertEqual(score, 100)
                template = json.loads((Path(__file__).resolve().parents[1] / 'assignments' / task['template']).read_text(encoding='utf-8'))
                self.assertLess(score_answers(task, template)[0], 100)

    def test_student_supplied_score_and_identity_are_ignored(self):
        task = self.catalog['tasks'][0]
        answer = correct_answer(task)
        answer.update(score=999, github_login='teacher', name='冒名')
        record = grade_issue(issue(task, answer), self.catalog)
        self.assertEqual(record['score'], 100)
        self.assertEqual(record['github_login'], 'real-student')
        self.assertEqual(record['name'], '测试学生')

    def test_wrong_value_loses_only_its_points(self):
        task = self.catalog['tasks'][0]
        answer = correct_answer(task)
        answer['records']['A-01']['pressure_mpa'] = 2400
        self.assertEqual(grade_issue(issue(task, answer), self.catalog)['score'], 90)

    def test_missing_null_and_boolean_are_different(self):
        task = self.catalog['tasks'][0]
        answer = correct_answer(task)
        del answer['records']['A-03']['temperature_c']
        self.assertEqual(score_answers(task, answer)[0], 90)
        self.assertFalse(equal(False, 0))
        self.assertFalse(equal(0, False))
        self.assertFalse(equal('150', 150))
        self.assertFalse(equal(float('inf'), 10))

    def test_json_rejects_duplicate_keys_nonfinite_and_arrays(self):
        for text in ['{"score":1,"score":2}', '{"x": NaN}', '[]', '{"x": Infinity}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                strict_json(text)

    def test_malformed_json_is_invalid_not_zero_grade(self):
        task = self.catalog['tasks'][0]
        submitted = issue(task, correct_answer(task))
        submitted['body'] = submitted['body'].replace('"records":', 'records:')
        record = grade_issue(submitted, self.catalog)
        self.assertEqual(record['status'], 'invalid')
        self.assertIsNone(record['score'])
        self.assertEqual(record['name'], '测试学生')

    def test_process_record_completeness_separate_from_answers(self):
        task = self.catalog['tasks'][0]
        answer = correct_answer(task)
        answer['process'] = {'first_prompt': '短', 'revision_prompt': ' ' * 100}
        self.assertEqual(score_answers(task, answer)[0], 80)

    def test_consent_and_duplicate_form_headers(self):
        task = self.catalog['tasks'][0]
        body = issue_body(task, correct_answer(task))
        with self.assertRaises(ValueError):
            parse_submission(body.replace('- [x]', '- [ ]'))
        with self.assertRaises(ValueError):
            parse_submission(body + '\n### 姓名或课堂代号\n\n另一个名字\n')

    def test_quote_like_header_inside_json_not_a_field(self):
        task = self.catalog['tasks'][0]
        answer = correct_answer(task)
        answer['process']['first_prompt'] += '\n### 姓名或课堂代号\n'
        self.assertEqual(parse_submission(issue_body(task, answer))['name'], '测试学生')

    def test_unordered_sources_retain_duplicates_check(self):
        self.assertTrue(equal(['S02', 'S01'], ['S01', 'S02'], {'unordered': True}))
        self.assertFalse(equal(['S01', 'S01'], ['S01', 'S02'], {'unordered': True}))
        self.assertFalse(equal(['a', 'b'], ['b', 'a']))

    def test_deadline_flag_and_teacher_override(self):
        catalog = copy.deepcopy(self.catalog)
        catalog['tasks'][0]['deadline'] = '2026-09-30T15:59:59Z'
        record = grade_issue(issue(catalog['tasks'][0], correct_answer(catalog['tasks'][0])), catalog)
        self.assertTrue(record['late'])
        apply_override(record, 95, '复核一项教学边界判断', 'teacher')
        self.assertEqual(record['score'], 95)
        self.assertEqual(record['auto_score'], 100)
        for score, reason in [(101, '原因'), (-1, '原因'), ('NaN', '原因'), (90, '')]:
            with self.assertRaises(ValueError):
                apply_override(record, score, reason, 'teacher')

    def test_feedback_escapes_user_markup_and_mentions(self):
        task = self.catalog['tasks'][0]
        submitted = issue(task, correct_answer(task))
        submitted['body'] = issue_body(task, correct_answer(task), '<img src=x> @teacher [x](https://evil.invalid)')
        rendered = feedback(grade_issue(submitted, self.catalog))
        self.assertNotIn('<img', rendered)
        self.assertIn('\\@teacher', rendered)

    def test_formula_injection_protected_and_workbook_valid(self):
        for value in ['=1+1', '+SUM(A1)', '-10', '@SUM(A1)', '  =1', '\t=1']:
            self.assertTrue(spreadsheet_cell(value).startswith("'"))
        rows = export_rows([{'name': '=HYPERLINK("evil")', 'score': 80}])
        self.assertTrue(rows[1][1].startswith("'"))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'grades.xlsx'
            write_xlsx(path, [('最新成绩', rows), ('全部提交', rows)])
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    ET.fromstring(archive.read(name))
                self.assertNotIn(b'<f>', archive.read('xl/worksheets/sheet1.xml'))

    def test_latest_submission_does_not_hide_pending_or_invalid(self):
        records = [{'github_login': 'User', 'task_id': 'A01', 'submitted_at': '2026-10-01T01:00:00Z', 'issue_number': 1, 'score': 100}, {'github_login': 'user', 'task_id': 'A01', 'submitted_at': '2026-10-01T02:00:00Z', 'issue_number': 2, 'score': None, 'status': 'invalid'}]
        latest = latest_records(records)
        self.assertEqual(len(latest), 1)
        self.assertIsNone(latest[0]['score'])
        self.assertEqual(latest[0]['issue_number'], 2)


if __name__ == '__main__':
    unittest.main()
