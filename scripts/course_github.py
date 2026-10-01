"""Trusted GitHub worker for coursework records and exports; stdlib only."""
from __future__ import annotations

import base64
import csv
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from course_grading import apply_override, feedback, grade_issue, load_catalog, submission_hash

BRANCH = 'course-grades'


class GitHub:
    def __init__(self, repository=None, token=None):
        self.repository = repository or os.environ['GITHUB_REPOSITORY']
        self.token = token or os.environ['GH_TOKEN']

    def api(self, path, method='GET', payload=None):
        url = 'https://api.github.com/repos/' + self.repository + '/' + path
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        request = urllib.request.Request(url, data=data, method=method, headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json', 'User-Agent': 'ai-literacy-coursework'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=35) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as error:
                if error.code in (429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise

    def pages(self, path):
        values, page = [], 1
        while True:
            items = self.api(path + ('&' if '?' in path else '?') + 'per_page=100&page=' + str(page))
            values.extend(items)
            if len(items) < 100:
                return values
            page += 1
            if page > 200:
                raise ValueError('记录数量过大，请按学期归档')

    def ensure_branch(self):
        try:
            self.api('git/ref/heads/' + BRANCH)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            sha = self.api('git/ref/heads/main')['object']['sha']
            try:
                self.api('git/refs', 'POST', {'ref': 'refs/heads/' + BRANCH, 'sha': sha})
            except urllib.error.HTTPError as create_error:
                if create_error.code != 422:
                    raise
                self.api('git/ref/heads/' + BRANCH)

    def read_record(self, number):
        try:
            item = self.api('contents/records/issue-' + str(number) + '.json?ref=' + BRANCH)
            return json.loads(base64.b64decode(item['content'])), item['sha']
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None, None
            raise

    def save_record(self, record, old_sha):
        encoded = base64.b64encode((json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8')).decode('ascii')
        payload = {'message': 'Record ' + record['task_id'] + ' submission #' + str(record['issue_number']), 'branch': BRANCH, 'content': encoded}
        if old_sha:
            payload['sha'] = old_sha
        # Different submissions can update this branch concurrently; retry ref conflicts.
        for attempt in range(4):
            try:
                return self.api('contents/records/issue-' + str(record['issue_number']) + '.json', 'PUT', payload)
            except urllib.error.HTTPError as error:
                if error.code not in (409, 422) or attempt == 3:
                    raise
                _, current_sha = self.read_record(record['issue_number'])
                if current_sha:
                    payload['sha'] = current_sha
                time.sleep(2 ** attempt)

    def post_feedback(self, record):
        comments = self.pages('issues/' + str(record['issue_number']) + '/comments')
        bot = next((comment for comment in reversed(comments) if comment['user']['login'] == 'github-actions[bot]' and comment['body'].startswith('<!-- course-grade:v1 -->')), None)
        body = feedback(record)
        if bot:
            if bot['body'] != body:
                self.api('issues/comments/' + str(bot['id']), 'PATCH', {'body': body})
        else:
            self.api('issues/' + str(record['issue_number']) + '/comments', 'POST', {'body': body})


def grade_remote(api, number, event, manual_score='', reason=''):
    api.ensure_branch()
    issue = api.api('issues/' + str(number))
    if 'pull_request' in issue:
        raise ValueError('只能对课程 Issue 提交评分')
    label_names = [label['name'] for label in issue['labels']]
    if 'course-submission' not in label_names and not issue.get('title', '').startswith('[作业 A') and not issue.get('title', '').startswith('[教师测试]'):
        print('Not a coursework issue; skipped')
        return
    catalog = load_catalog()
    previous, sha = api.read_record(number)
    record = grade_issue(issue, catalog)
    if previous and previous['submission_hash'] == record['submission_hash']:
        # Reviewing an older submission must not turn it into the latest submission.
        record['submitted_at'] = previous['submitted_at']
    owner = api.repository.split('/')[0]
    record['is_test'] = issue['user']['login'].lower() == owner.lower() and issue.get('title', '').startswith('[教师测试]')
    if manual_score:
        if event.get('_event_name') != 'workflow_dispatch':
            raise ValueError('人工改分只能由教师主动触发工作流')
        actor = event.get('sender', {}).get('login', '')
        permission = api.api('collaborators/' + urllib.parse.quote(actor, safe='') + '/permission')['permission']
        if permission not in ('admin', 'maintain', 'write'):
            raise ValueError('当前账号没有教师改分权限')
        apply_override(record, manual_score, reason, actor)
    if previous and previous['submission_hash'] == record['submission_hash'] and previous.get('task_version') == record['task_version'] and not manual_score:
        # Keep any teacher review on unchanged submissions; repair a failed feedback post.
        api.post_feedback(previous)
        print('Submission unchanged; existing record preserved')
        return
    if previous:
        record['history'] = (previous.get('history', []) + [{key: previous.get(key) for key in ('submission_hash', 'submitted_at', 'graded_at', 'score', 'auto_score', 'manual_review', 'task_version', 'status')}])[-20:]
    else:
        record['history'] = []
    # Do not publish a result from a body that changed during processing.
    current = api.api('issues/' + str(number))
    if submission_hash(current) != record['submission_hash']:
        raise ValueError('提交正在修改，请稍后重试；此次未写入旧分数')
    api.save_record(record, sha)
    api.post_feedback(record)
    output = Path('course-output')
    output.mkdir(exist_ok=True)
    (output / ('issue-' + str(number) + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Recorded issue', number, 'status', record['status'], 'score', record['score'])


HEADERS = [('task_id', '任务编号'), ('name', '姓名或课堂代号'), ('class_name', '班级'), ('github_login', 'GitHub账号'), ('score', '最终分数'), ('auto_score', '自动分数'), ('maximum', '满分'), ('status', '状态'), ('late', '迟交'), ('submitted_at', '提交时间UTC'), ('graded_at', '评分时间UTC'), ('issue_number', '提交编号'), ('issue_url', '提交链接'), ('review_by', '复核教师'), ('review_reason', '复核原因'), ('error', '说明')]


def spreadsheet_cell(value):
    value = '' if value is None else str(value)
    if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
        return "'" + value
    return ''.join(c for c in value if ord(c) >= 32 or c == '\n')


def export_rows(records):
    rows = []
    for record in records:
        row = dict(record)
        review = record.get('manual_review') or {}
        row['review_by'], row['review_reason'] = review.get('by', ''), review.get('reason', '')
        rows.append([spreadsheet_cell(row.get(key)) for key, _ in HEADERS])
    return [[label for _, label in HEADERS]] + rows


def excel_column(number):
    value = ''
    while number:
        number, remainder = divmod(number - 1, 26)
        value = chr(65 + remainder) + value
    return value


def write_xlsx(path, sheets):
    """OOXML workbook: trusted grade columns numeric, identity columns plain text."""
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        workbook = '<workbook xmlns="' + ns + '" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        for index, (name, rows) in enumerate(sheets, 1):
            types += '<Override PartName="/xl/worksheets/sheet' + str(index) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            workbook += '<sheet name="' + escape(name) + '" sheetId="' + str(index) + '" r:id="rId' + str(index) + '"/>'
            rels += '<Relationship Id="rId' + str(index) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + str(index) + '.xml"/>'
            dimension = 'A1:' + excel_column(len(rows[0])) + str(len(rows))
            xml = '<worksheet xmlns="' + ns + '"><dimension ref="' + dimension + '"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><sheetData>'
            for row_number, values in enumerate(rows, 1):
                xml += '<row r="' + str(row_number) + '">'
                for column, value in enumerate(values, 1):
                    coordinate = excel_column(column) + str(row_number)
                    if row_number > 1 and column in (5, 6, 7, 12) and re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', str(value)):
                        xml += '<c r="' + coordinate + '" t="n"><v>' + str(value) + '</v></c>'
                    else:
                        xml += '<c r="' + coordinate + '" t="inlineStr"><is><t xml:space="preserve">' + escape(str(value)) + '</t></is></c>'
                xml += '</row>'
            xml += '</sheetData><autoFilter ref="A1:' + excel_column(len(rows[0])) + str(len(rows)) + '"/></worksheet>'
            archive.writestr('xl/worksheets/sheet' + str(index) + '.xml', xml)
        archive.writestr('[Content_Types].xml', types + '</Types>')
        archive.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        archive.writestr('xl/workbook.xml', workbook + '</sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', rels + '</Relationships>')


def latest_records(records):
    selected = {}
    for record in sorted(records, key=lambda item: (item['submitted_at'], item['issue_number'])):
        selected[(record['github_login'].lower(), record['task_id'])] = record
    return list(selected.values())


def export_remote(api, output):
    try:
        ref = api.api('git/ref/heads/' + BRANCH)
        tree = api.api('git/trees/' + ref['object']['sha'] + '?recursive=1')
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        tree = {'tree': []}
    if tree.get('truncated'):
        raise ValueError('成绩树过大，请归档后导出')
    issues = {item['number']: item for item in api.pages('issues?state=all&labels=course-submission') if 'pull_request' not in item}
    records = []
    for item in tree['tree']:
        if not item['path'].startswith('records/issue-') or not item['path'].endswith('.json'):
            continue
        blob = api.api('git/blobs/' + item['sha'])
        record = json.loads(base64.b64decode(blob['content']))
        if record.get('is_test'):
            continue
        issue = issues.get(record['issue_number'])
        if issue is None:
            try:
                issue = api.api('issues/' + str(record['issue_number']))
            except urllib.error.HTTPError as error:
                if error.code not in (404, 410):
                    raise
        if issue is None:
            record.update(status='unavailable', score=None, error='原提交已不可访问，需教师核对')
        elif submission_hash(issue) != record['submission_hash']:
            record.update(status='pending', score=None, auto_score=None, error='提交已修改，等待重新评分', submitted_at=issue['updated_at'])
        records.append(record)
    recorded = {record['issue_number'] for record in records}
    for number, issue in issues.items():
        is_teacher_test = issue['user']['login'].lower() == api.repository.split('/')[0].lower() and issue.get('title', '').startswith('[教师测试]')
        if number in recorded or is_teacher_test:
            continue
        record = grade_issue(issue)
        record.update(status='pending', score=None, auto_score=None, error='自动评分尚未写入记录')
        records.append(record)
    records.sort(key=lambda item: (item['task_id'], item['github_login'].lower(), item['submitted_at'], item['issue_number']))
    latest = latest_records(records)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in [('all-submissions', records), ('latest-grades', latest)]:
        with (output / (name + '.csv')).open('w', encoding='utf-8-sig', newline='') as file:
            csv.writer(file).writerows(export_rows(data))
    write_xlsx(output / 'course-grades.xlsx', [('最新成绩', export_rows(latest)), ('全部提交', export_rows(records))])
    (output / 'records.json').write_text(json.dumps({'exported_at': datetime.now(timezone.utc).isoformat(), 'all_submissions': records, 'latest_grades': latest}, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'README.txt').write_text('latest-grades.csv：同一GitHub账号同一任务的最后一次提交；未完成评分的最新提交不沿用旧分。\nall-submissions.csv：全部提交。course-grades.xlsx：两张工作表。\n时间为UTC（北京时间加8小时）。pending=待评分；invalid=格式无效；unavailable=原提交不可访问。教师测试不计入。缺交学生需与教师自己的名单核对，系统不能从未提交的账号推断姓名。\n', encoding='utf-8')
    print('Exported', len(records), 'submissions and', len(latest), 'latest grades')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['grade', 'export'])
    args = parser.parse_args()
    api = GitHub()
    if args.operation == 'export':
        export_remote(api, Path('course-output'))
        return
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    event['_event_name'] = os.environ['GITHUB_EVENT_NAME']
    number = event.get('issue', {}).get('number') or int(os.environ['COURSE_ISSUE_NUMBER'])
    grade_remote(api, number, event, os.environ.get('COURSE_MANUAL_SCORE', ''), os.environ.get('COURSE_REVIEW_REASON', ''))


if __name__ == '__main__':
    main()
