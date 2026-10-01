"""Generate JSON-compatible YAML issue forms from the assignment catalog."""
import json
from pathlib import Path
from course_grading import load_catalog

ROOT = Path(__file__).resolve().parents[1]


def forms():
    catalog = load_catalog()
    result = {}
    for task in catalog['tasks']:
        if not task['published']:
            continue
        issue_form = {'name': task['id'] + ' · ' + task['title'], 'description': '豆包工作课程任务：成果与过程记录提交', 'title': '[作业 ' + task['id'] + '] ', 'labels': ['course-submission'], 'body': [
            {'type': 'markdown', 'attributes': {'value': '请先阅读[任务与附件](https://cupzhoutianhang.github.io/ai-literacy/assignments/?task=' + task['id'] + ')。此为公开提交：姓名或课堂代号、GitHub账号、成果、截图和分数会被其他人看到。不要填写身份证、电话或账号密钥。'}},
            {'type': 'input', 'id': 'task', 'attributes': {'label': '任务编号', 'value': task['id'], 'description': '请保留此任务编号'}, 'validations': {'required': True}},
            {'type': 'input', 'id': 'student', 'attributes': {'label': '姓名或课堂代号', 'description': '填写教师认可的姓名或课堂代号，用于记录成绩'}, 'validations': {'required': True}},
            {'type': 'input', 'id': 'class', 'attributes': {'label': '班级（可选）'}, 'validations': {'required': False}},
            {'type': 'textarea', 'id': 'answer', 'attributes': {'label': '成果 JSON', 'description': '粘贴 answer-template.json 填好后的全文，包括 process 中两条提示词。不要粘贴下载链接。', 'render': 'json', 'placeholder': '{"process": {"first_prompt": "…", "revision_prompt": "…"}, "其他成果字段": "按本题模板填写"}'}, 'validations': {'required': True}},
            {'type': 'textarea', 'id': 'attachments', 'attributes': {'label': '补充附件（可选）', 'description': '可以拖入成果文件、截图、Skill ZIP 等。自动评分读取上方 JSON，不读取或执行此处附件；附件供教师复核。'}, 'validations': {'required': False}},
            {'type': 'checkboxes', 'id': 'consent', 'attributes': {'label': '提交确认', 'options': [{'label': '我理解此提交及成绩公开可见，已检查内容不含敏感信息，并保留了豆包工作过程记录。', 'required': True}]}}
        ]}
        result[task['id'].lower() + '.yml'] = json.dumps(issue_form, ensure_ascii=False, indent=2) + '\n'
    return result


if __name__ == '__main__':
    import sys
    directory = ROOT / '.github/ISSUE_TEMPLATE'
    generated = forms()
    if '--check' in sys.argv:
        for name, text in generated.items():
            if not (directory / name).exists() or (directory / name).read_text(encoding='utf-8') != text:
                raise SystemExit('需要重新生成表单：' + name)
        print('Task catalog and issue forms verified')
    else:
        directory.mkdir(parents=True, exist_ok=True)
        for name, text in generated.items():
            (directory / name).write_text(text, encoding='utf-8')
        print('Created', len(generated), 'issue forms')
