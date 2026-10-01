"""Teacher-dispatched task form generation with an explicit recovery point."""
import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from build_course_forms import forms
from course_github import GitHub


def publish(api, expected_sha):
    current = api.api('git/ref/heads/main')['object']['sha']
    if current != expected_sha:
        raise ValueError('main 已更新，请重新运行发布工作流；本次未覆盖任何文件')
    generated = forms()
    sha = current[:7]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    tag = 'backup/before-task-publish-' + stamp + '-' + sha
    api.api('git/refs', 'POST', {'ref': 'refs/tags/' + tag, 'sha': current})
    parent = api.api('git/commits/' + current)
    changes = []
    for name, text in generated.items():
        path = '.github/ISSUE_TEMPLATE/' + name
        blob = api.api('git/blobs', 'POST', {'content': text, 'encoding': 'utf-8'})
        changes.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    # Delete obsolete course forms after a task is unpublished, preserving unrelated templates.
    old_tree = api.api('git/trees/' + parent['tree']['sha'] + '?recursive=1')
    if old_tree.get('truncated'):
        raise ValueError('文件树过大，无法安全生成表单')
    import re
    for item in old_tree['tree']:
        if re.fullmatch(r'\.github/ISSUE_TEMPLATE/a\d{2}\.yml', item['path']) and item['path'].rsplit('/', 1)[-1] not in generated:
            changes.append({'path': item['path'], 'mode': '100644', 'type': 'blob', 'sha': None})
    tree = api.api('git/trees', 'POST', {'base_tree': parent['tree']['sha'], 'tree': changes})
    if tree['sha'] != parent['tree']['sha']:
        commit = api.api('git/commits', 'POST', {'message': 'Update coursework submission forms (snapshot ' + tag + ')', 'tree': tree['sha'], 'parents': [current]})
        # Non-force ref update rejects concurrent changes rather than losing teacher edits.
        api.api('git/refs/heads/main', 'PATCH', {'sha': commit['sha'], 'force': False})
    api.api('pages/builds', 'POST', {})
    print('Published task forms. Recovery tag:', tag)


if __name__ == '__main__':
    if os.environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch':
        raise SystemExit('题目发布只能由教师主动触发')
    publish(GitHub(), os.environ['GITHUB_SHA'])
