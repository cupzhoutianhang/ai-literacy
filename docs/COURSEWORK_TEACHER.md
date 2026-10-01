# 豆包工作课程任务：教师说明

课程入口：<https://cupzhoutianhang.github.io/ai-literacy/assignments/>

本系统全部使用 GitHub：Pages 展示，Issue 表单收集，Actions 自动检查，`course-grades` 分支持久保存成绩。学生需登录 GitHub，姓名或课堂代号由教师核对。公开仓库里的作业、附件、分数和导出文件对有相应访问权限的人可见，当前课程仓库是公开的；不提供个人成绩隐私隔离。

## 第一批任务

| 编号 | 任务 | 相关讲次 |
|---|---|---|
| A01 | 工艺日报结构化 | L02、L03 |
| A02 | 安全规程带证据问答 | L04 |
| A03 | 只读工具调用与泵功率 | L05、L06、L07 |
| A04 | 长对话任务记忆 | L08 |
| A05 | 最小够用的 AI 能力选择 | L09、L10 |
| A06 | 能源日报 Skill 设计 | L11 |

每题有教学合成附件、题面说明、JSON 成果模板和附件 ZIP。不要求使用实际企业数据。第一版没有课程作业截止日期；A04 附件中的日期是该题需要提取的模拟事实。

每题满分100：题目结果检查合计80分，process.first_prompt 与 process.revision_prompt 各10分（每条至少30个非空白字符）。过程分仅检查记录完整性，不证明用了豆包工作，不评价提示词质量；可结合截图、完整成果及课堂表现复核。自动规则公开，定位为形成性练习，不是防作弊考试系统。A06 自动分检查元数据，完整 SKILL.md 质量需要教师检查。

## 学生提交与重新提交

1. 在任务页下载附件和 answer-template.json。
2. 用豆包工作完成任务，人工核对后填模板。将两条实际提示词写入 process。
3. 点本题提交，填姓名或课堂代号，粘贴完整 JSON；附件可拖入补充附件框。
4. 等待 Issue 下的自动检查回复。完整成果 JSON 是自动评分输入，附件供复核，不会被自动下载或执行。
5. 修改时编辑原 Issue 正文，保存后重评；评论中的新答案不触发重评。关闭后仍可查看记录，需要继续时重新打开。

名字不能替代身份验证，汇总身份以 GitHub 账号为准。建议课前收集“学生姓名或课堂代号 ↔ GitHub账号”名单，避免一人多个账号和代填姓名。

## 查看与导出成绩

打开 [Course - Export grades](https://github.com/cupzhoutianhang/ai-literacy/actions/workflows/course-export.yml)，点击 **Run workflow**，使用 main 分支。完成后进入这次运行，在 Artifacts 下载 `course-grades-运行编号`。

包含：

- `latest-grades.csv`：同一 GitHub 账号、同一任务最后一次提交。
- `all-submissions.csv`：全部提交及姓名、班级、分数、时间、提交链接、教师复核信息。
- `course-grades.xlsx`：最新成绩、全部提交两张工作表，可直接用 Excel 打开。
- `records.json`：完整记录。

时间为 UTC，北京时间加8小时。`graded` 是已评分，`pending` 是等待评分，`invalid` 是格式无效，`unavailable` 是原提交不可访问。无效或待评分提交不会记为0分，也不会继续沿用同一任务的旧分。导出先核对原 Issue 正文是否改变，避免导出修改前的旧分数。系统只知道已经提交的学生，缺交名单需与你的学生名册比较。

教师测试标题使用 `[教师测试]`，仅课程仓库所有者创建的测试会被标记并排除。导出包保留30天；原记录保存在 `course-grades` 分支，不依赖下载包长期存在，可随时重新生成。每个 Issue 保留最近20次改分/重交摘要；更早版本仍在该分支的 Git 提交历史中。

## 重新评分与人工改分

打开 [Course - Grade submission](https://github.com/cupzhoutianhang/ai-literacy/actions/workflows/course-grade.yml)，点击 **Run workflow**，填写 `issue_number`，它是 URL 最后的提交编号，不是 A01 这样的任务编号。

- 只重新检查：`manual_score` 和 `review_reason` 留空。
- 教师复核：填写0至100的最终分数，必须填写原因。程序核验调用者拥有仓库写入、维护或管理员权限。
- 原自动分会保留，复核原因和教师账号进入记录与导出。
- 对未改变的成果重新运行会保留教师复核分；学生修改成果或题目版本改变后重新评分，旧复核进入历史，需要教师按新成果决定是否再次复核。
- 修改评分规则后必须提升该任务的 `version`，避免把旧规则得分误认为新规则得分。

## 自己发布新题

你可以在 GitHub 网页操作，不必租服务器或安装数据库：

1. 先在 [提交历史](https://github.com/cupzhoutianhang/ai-literacy/commits/main/) 保存当前提交链接。网页每次保存文件也会保留旧版本；整批发布另有恢复标签。
2. 在 `assignments/` 建立新目录，例如 `a07/`。使用 **Add file → Upload files** 上传公开教学附件、题面和 `answer-template.json`。不要上传真实账号凭证。
3. 编辑 `assignments/tasks.json`，复制现有任务对象，填写新编号（例如 A07）、标题、相关讲次、描述、步骤、附件路径、模板路径。
4. 开始可设 `published:false` 保持草稿。准备完成后改为 true。可配置 deadline，如 `2026-10-15T15:59:59Z` 表示北京时间2026-10-15 23:59:59；不设则填写 null。
5. 配置 rubric：`path` 是提交 JSON 字段路径，`expected` 是标准结果，`points` 是该项分值。总分必须是80，再加固定过程分20。数值可设置 tolerance；列表可设置 unordered:true。必须写能客观检查的字段，报告质量不要硬塞进精确字符串匹配。
6. 本题附件 ZIP 可用你本地压缩包上传到新目录，文件名保持 `task-attachments.zip`。ZIP 应含题面、全部教学附件和成果模板；任务详情固定提供此下载地址。
7. 运行 [Course - Publish assignment forms](https://github.com/cupzhoutianhang/ai-literacy/actions/workflows/course-publish.yml)。它会验证附件/评分配置，先保存 `backup/before-task-publish-*` 标签，再生成 Issue 表单并申请 Pages 构建。成功后刷新任务页，核对附件与提交按钮。

发布新题需要给它编写标准结果；自动评分不会仅凭题目描述自行理解整篇报告。当前匹配器支持数值（容差）、字符串、布尔值、null、列表。提交路径只支持对象键，以点号分隔，列表整体匹配；更复杂代码测试需扩展评分程序并添加测试。

附件会在你保存到公开仓库时公开，不会等到发布工作流才公开。任务目录 JSON 使用 published 控制学生页面与表单，已知 URL 的附件仍可访问。

本地维护可以运行：

```powershell
python scripts/build_course_forms.py
python -m unittest discover -s tests -p 'test_course*.py' -v
node --check assignments/course.js
```

## 发布与回退

实施前原版本为 `e9b5264eefa152a5387614c612acdc4ec4e1c9ea`，标签为 `backup/pre-doubao-assignments-20261001-e9b5264`。此标签保存课件、主页、实验等全部原文件。

代码发布必须先提交本地修改，再用脚本。脚本每次会为远端 main 创建新的恢复标签，检测并发修改；保留 Git 历史，不强制推送。

```powershell
# 发布当前已提交版本
pwsh -File scripts/course_release.ps1 -Mode Publish

# 恢复到增加作业功能前的原版
pwsh -File scripts/course_release.ps1 -Mode Restore -Ref backup/pre-doubao-assignments-20261001-e9b5264
```

回退会生成新提交并触发 Pages 更新，而不是删除历史。恢复到原版后，该版本没有 course_release.ps1，因此请在回退前另存脚本；本次交付已另外保存回退脚本和说明。回退前的版本也有恢复标签，可用另存脚本再次恢复。

网页和工作流回退不会删除学生 Issues、附件和 course-grades 分支；成绩保留。分支恢复需要另行指定，不应与网页回退混在一起。
