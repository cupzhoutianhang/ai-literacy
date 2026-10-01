"""Deterministic coursework grading. Never execute submitted code or fetch URLs."""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSING = object()
MAX_BODY = 60000
MAX_JSON = 24000


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('JSON 中有重复字段：' + key)
        value[key] = item
    return value


def strict_json(text):
    def invalid_constant(value):
        raise ValueError('不支持非有限数字：' + value)
    if len(text) > MAX_JSON:
        raise ValueError('成果 JSON 超过 24000 字符，请精简内容')
    try:
        result = json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (json.JSONDecodeError, RecursionError) as error:
        raise ValueError('成果 JSON 格式错误，请检查引号、逗号和括号') from error
    if not isinstance(result, dict):
        raise ValueError('成果 JSON 顶层必须是对象')
    return result


def load_catalog():
    catalog = json.loads((ROOT / 'assignments/tasks.json').read_text(encoding='utf-8'))
    ids = set()
    for task in catalog['tasks']:
        if not re.fullmatch(r'A\d{2}', task['id']) or task['id'] in ids:
            raise ValueError('任务编号格式错误或重复')
        ids.add(task['id'])
        if sum(rule['points'] for rule in task['rubric']) + task['process_points'] != 100:
            raise ValueError('每题评分之和必须为100')
        if task['process_points'] != 20:
            raise ValueError('本版过程记录共20分')
        for rule in task['rubric']:
            if rule['points'] <= 0 or not re.fullmatch(r'[\w-]+(?:\.[\w-]+)*', rule['path']):
                raise ValueError('评分路径或分值无效')
        for relative in [task['template'], task['id'].lower() + '/task-attachments.zip'] + [item['path'] for item in task['attachments']]:
            path = (ROOT / 'assignments' / relative).resolve()
            if not path.is_relative_to(ROOT / 'assignments') or not path.is_file():
                raise ValueError('附件不存在或路径越界')
        if task.get('deadline'):
            timestamp(task['deadline'])
    return catalog


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('截止日期必须有时区，如 2026-10-15T15:59:59Z')
    return parsed


def sections(body):
    if not isinstance(body, str) or len(body) > MAX_BODY:
        raise ValueError('提交内容为空或过长')
    # Ignore heading-like text inside a fenced JSON block.
    parts, current, lines, fence = {}, None, [], False
    for line in body.splitlines():
        if line.startswith('```'):
            fence = not fence
        heading = re.fullmatch(r'### (.+)', line) if not fence else None
        if heading:
            if current is not None:
                if current in parts:
                    raise ValueError('表单字段重复：' + current)
                parts[current] = '\n'.join(lines).strip()
            current, lines = heading.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        if current in parts:
            raise ValueError('表单字段重复：' + current)
        parts[current] = '\n'.join(lines).strip()
    return parts


def clean_field(value, maximum=80):
    text = ' '.join(str(value).split())
    if text in ('', '_No response_'):
        return ''
    if len(text) > maximum or any(ord(c) < 32 for c in text):
        raise ValueError('姓名或班级字段过长')
    return text


def parse_submission(body):
    fields = sections(body)
    task_id = fields.get('任务编号', '').strip()
    if not re.fullmatch(r'A\d{2}', task_id):
        raise ValueError('请保留表单中的任务编号，如 A01')
    name = clean_field(fields.get('姓名或课堂代号', ''))
    if not name:
        raise ValueError('请填写姓名或教师认可的课堂代号')
    raw = fields.get('成果 JSON', '').strip()
    if raw.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*\n([\s\S]*?)\n```', raw)
        if not match:
            raise ValueError('请只粘贴一个完整的 JSON 对象，不要加入下载链接或额外代码块')
        raw = match.group(1)
    answers = strict_json(raw)
    if not re.search(r'^- \[[xX]\]', fields.get('提交确认', ''), re.MULTILINE):
        raise ValueError('请勾选公开提交确认')
    return {'task_id': task_id, 'name': name, 'class_name': clean_field(fields.get('班级（可选）', '')), 'answers': answers}


def at_path(value, path):
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def equal(actual, expected, rule=None):
    rule = rule or {}
    if actual is MISSING:
        return False
    if expected is None:
        return actual is None
    if isinstance(expected, bool):
        return type(actual) is bool and actual == expected
    if isinstance(expected, (int, float)):
        return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-8, abs_tol=rule.get('tolerance', 1e-6))
    if isinstance(expected, str):
        return isinstance(actual, str) and actual.strip() == expected
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        if rule.get('unordered'):
            # Multiset comparison, retaining duplicate checks and strict types.
            remaining = list(actual)
            for wanted in expected:
                index = next((i for i, item in enumerate(remaining) if equal(item, wanted)), None)
                if index is None:
                    return False
                remaining.pop(index)
            return True
        return all(equal(item, wanted) for item, wanted in zip(actual, expected))
    return type(actual) is type(expected) and actual == expected


def score_answers(task, answers):
    checks = []
    for rule in task['rubric']:
        passed = equal(at_path(answers, rule['path']), rule['expected'], rule)
        checks.append({'label': rule['label'], 'points': rule['points'], 'earned': rule['points'] if passed else 0, 'passed': passed})
    for key, label in [('first_prompt', '首次提示词记录完整'), ('revision_prompt', '修订提示词记录完整')]:
        value = at_path(answers, 'process.' + key)
        passed = isinstance(value, str) and len(re.sub(r'\s', '', value)) >= 30
        checks.append({'label': label, 'points': 10, 'earned': 10 if passed else 0, 'passed': passed})
    return sum(check['earned'] for check in checks), checks


def submission_hash(issue):
    return hashlib.sha256((issue.get('body') or '').encode('utf-8')).hexdigest()


def grade_issue(issue, catalog=None):
    catalog = catalog or load_catalog()
    record = {'schema_version': 1, 'issue_number': issue['number'], 'issue_url': issue['html_url'], 'github_login': issue['user']['login'], 'submission_hash': submission_hash(issue), 'submitted_at': issue['updated_at'], 'graded_at': datetime.now(timezone.utc).isoformat(), 'task_id': '', 'task_version': None, 'name': '', 'class_name': '', 'status': 'invalid', 'score': None, 'auto_score': None, 'maximum': 100, 'checks': [], 'late': False, 'manual_review': None, 'error': ''}
    # Invalid submissions still retain safely parsed identity/task fields for exports.
    try:
        fields = sections(issue.get('body') or '')
        record['name'] = clean_field(fields.get('姓名或课堂代号', ''))
        record['class_name'] = clean_field(fields.get('班级（可选）', ''))
        candidate = fields.get('任务编号', '').strip()
        if re.fullmatch(r'A\d{2}', candidate):
            record['task_id'] = candidate
        parsed = parse_submission(issue.get('body') or '')
        task = next((item for item in catalog['tasks'] if item['id'] == parsed['task_id'] and item['published']), None)
        if task is None:
            raise ValueError('任务不存在或尚未发布')
        record.update(task_id=task['id'], task_version=task['version'], name=parsed['name'], class_name=parsed['class_name'])
        if task.get('deadline'):
            record['late'] = timestamp(issue['updated_at']) > timestamp(task['deadline'])
        score, checks = score_answers(task, parsed['answers'])
        record.update(status='graded', score=score, auto_score=score, checks=checks)
    except (ValueError, OverflowError, RecursionError) as error:
        record['error'] = str(error)[:240]
    return record


def apply_override(record, score, reason, actor):
    if record['status'] != 'graded':
        raise ValueError('格式无效的提交不能直接改分，请先修复提交')
    if isinstance(score, bool) or not math.isfinite(float(score)) or not 0 <= float(score) <= 100:
        raise ValueError('复核分数必须在0至100之间')
    reason = clean_field(reason, 500)
    if not reason:
        raise ValueError('教师复核必须填写原因')
    record['score'] = float(score)
    record['manual_review'] = {'by': actor, 'reason': reason, 'at': record['graded_at']}
    return record


def markdown_text(text):
    value = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_{}\[\]()#+.!|@])', r'\\\1', value).replace('\n', ' ')


def feedback(record):
    marker = '<!-- course-grade:v1 -->'
    if record['status'] != 'graded':
        return marker + '\n## 提交需要修正\n\n' + markdown_text(record['error']) + '\n\n请编辑本 Issue 的正文；保存后会重新检查。此次记录为格式无效，不记作零分。'
    text = marker + '\n## ' + record['task_id'] + ' 自动检查结果：' + str(record['score']) + ' / 100\n\n'
    text += '姓名或课堂代号：' + markdown_text(record['name']) + ' · GitHub：' + markdown_text(record['github_login']) + '\n\n'
    text += '| 检查项目 | 得分 | 结果 |\n|---|---:|---|\n'
    for check in record['checks']:
        text += '| ' + markdown_text(check['label']) + ' | ' + str(check['earned']) + '/' + str(check['points']) + ' | ' + ('通过' if check['passed'] else '需核对') + ' |\n'
    text += '\n过程分只检查提示词记录长度，不证明使用了豆包工作或评价文字质量。请保留成果和过程证据供教师复核。编辑本 Issue 可重新评分；同一账号同一任务以最后一次提交记录汇总，教师可人工改分。\n'
    if record['late']:
        text += '\n该提交标记为迟交；自动分数未额外扣分，由教师决定。\n'
    if record['manual_review']:
        review = record['manual_review']
        text += '\n教师复核：' + str(record['score']) + '/100；自动分：' + str(record['auto_score']) + '/100。原因：' + markdown_text(review['reason']) + '。\n'
    text += '\n提交校验：`' + record['submission_hash'][:12] + '`；任务版本：' + str(record['task_version']) + '。'
    return text
