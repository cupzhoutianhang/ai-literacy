import base64
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from course_github import export_remote, grade_remote
from course_grading import grade_issue, load_catalog
from test_course_grading import correct_answer, issue


class FakeGitHub:
    repository = 'teacher/course'

    def __init__(self, submitted, previous=None, permission='write'):
        self.issue = copy.deepcopy(submitted)
        self.issue['title'] = '[作业 A01] 测试'
        self.issue['labels'] = [{'name': 'course-submission'}]
        self.previous = previous
        self.permission = permission
        self.saved = None
        self.comment = None
        self.reads = 0
        self.change_during_grading = False

    def ensure_branch(self):
        pass

    def api(self, path, method='GET', payload=None):
        if path.startswith('collaborators/'):
            return {'permission': self.permission}
        if path.startswith('issues/'):
            self.reads += 1
            value = copy.deepcopy(self.issue)
            if self.change_during_grading and self.reads > 1:
                value['body'] += '\nmodified'
            return value
        if path.startswith('git/ref/'):
            return {'object': {'sha': 'main'}}
        if path.startswith('git/trees/'):
            return {'tree': [] if self.previous is None else [{'path': 'records/issue-1.json', 'sha': 'record'}]}
        if path.startswith('git/blobs/'):
            return {'content': base64.b64encode(json.dumps(self.previous).encode('utf-8')).decode('ascii')}
        raise AssertionError(path)

    def read_record(self, number):
        return copy.deepcopy(self.previous), 'old-sha' if self.previous else None

    def save_record(self, record, sha):
        self.saved = copy.deepcopy(record)

    def post_feedback(self, record):
        self.comment = copy.deepcopy(record)

    def pages(self, path):
        return [copy.deepcopy(self.issue)]


class CourseRemoteTests(unittest.TestCase):
    def setUp(self):
        self.task = load_catalog()['tasks'][0]
        self.submission = issue(self.task, correct_answer(self.task))
        self.previous = grade_issue(self.submission)
        self.previous['is_test'] = False
        self.previous['history'] = []

    def test_manual_review_keeps_original_submission_timestamp(self):
        api = FakeGitHub(self.submission, self.previous)
        api.issue['updated_at'] = '2026-10-02T12:00:00Z'
        grade_remote(api, 1, {'_event_name': 'workflow_dispatch', 'sender': {'login': 'teacher'}}, '95', '复核结果')
        self.assertEqual(api.saved['score'], 95)
        self.assertEqual(api.saved['submitted_at'], self.previous['submitted_at'])

    def test_untrusted_manual_review_is_denied(self):
        for name, permission in [('issues', 'write'), ('workflow_dispatch', 'read')]:
            with self.subTest(name=name, permission=permission):
                api = FakeGitHub(self.submission, permission=permission)
                with self.assertRaises(ValueError):
                    grade_remote(api, 1, {'_event_name': name, 'sender': {'login': 'student'}}, '100', '伪造改分')
                self.assertIsNone(api.saved)

    def test_idempotent_grading_preserves_teacher_review(self):
        previous = copy.deepcopy(self.previous)
        previous.update(score=95, manual_review={'by': 'teacher', 'reason': '复核', 'at': 'now'})
        api = FakeGitHub(self.submission, previous)
        grade_remote(api, 1, {'_event_name': 'workflow_dispatch'})
        self.assertIsNone(api.saved)
        self.assertEqual(api.comment['score'], 95)

    def test_changed_body_resets_override_and_retains_history(self):
        previous = copy.deepcopy(self.previous)
        previous.update(score=95, manual_review={'by': 'teacher', 'reason': '复核', 'at': 'now'})
        api = FakeGitHub(self.submission, previous)
        api.issue['body'] = api.issue['body'].replace('"pressure_mpa": 2.4', '"pressure_mpa": 2400')
        grade_remote(api, 1, {'_event_name': 'issues'})
        self.assertEqual(api.saved['score'], 90)
        self.assertIsNone(api.saved['manual_review'])
        self.assertEqual(api.saved['history'][-1]['score'], 95)

    def test_concurrent_edit_never_publishes_old_score(self):
        api = FakeGitHub(self.submission)
        api.change_during_grading = True
        with self.assertRaises(ValueError):
            grade_remote(api, 1, {'_event_name': 'issues'})
        self.assertIsNone(api.saved)

    def test_export_flags_modified_body_instead_of_reusing_score(self):
        api = FakeGitHub(self.submission, self.previous)
        api.issue['body'] += '\nchanged'
        with tempfile.TemporaryDirectory() as directory:
            export_remote(api, Path(directory))
            records = json.loads((Path(directory) / 'records.json').read_text(encoding='utf-8'))
            self.assertEqual(records['latest_grades'][0]['status'], 'pending')
            self.assertIsNone(records['latest_grades'][0]['score'])

    def test_ungraded_submission_is_exported_pending(self):
        api = FakeGitHub(self.submission)
        with tempfile.TemporaryDirectory() as directory:
            export_remote(api, Path(directory))
            records = json.loads((Path(directory) / 'records.json').read_text(encoding='utf-8'))
            self.assertEqual(records['all_submissions'][0]['status'], 'pending')

    def test_student_cannot_exclude_submission_with_teacher_test_title(self):
        api = FakeGitHub(self.submission)
        api.issue['title'] = '[教师测试] 伪装'
        with tempfile.TemporaryDirectory() as directory:
            export_remote(api, Path(directory))
            records = json.loads((Path(directory) / 'records.json').read_text(encoding='utf-8'))
            self.assertEqual(len(records['all_submissions']), 1)


if __name__ == '__main__':
    unittest.main()
