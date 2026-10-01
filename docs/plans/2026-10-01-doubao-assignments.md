# Doubao Coursework Implementation Plan

**Goal:** Add six course-related Doubao Work assignments with attachments, GitHub submissions, deterministic grading, named records, teacher review and export, with recoverable releases.

**Architecture:** Keep GitHub Pages as the public course entry. Issue forms collect identity, structured JSON results and optional evidence. Trusted GitHub Actions grade JSON without executing student code or downloading arbitrary URLs; records are kept on a teacher-writable `course-grades` branch. A teacher-only dispatch exports CSV/XLSX and supports score overrides.

**Tech Stack:** Static HTML/CSS/JavaScript, Python 3.12 standard library, GitHub Issues/Actions/REST API.

The user approved direct implementation and publication, GitHub accounts and public submissions. This plan is executed in the isolated clone in this chat without further readiness prompts.

## 1. Preserve the baseline

- Save tag `backup/pre-doubao-assignments-20261001-e9b5264` pointing to `e9b5264eefa152a5387614c612acdc4ec4e1c9ea`.
- Save a complete Git bundle outside the repository.
- Add `scripts/course_release.ps1` which snapshots the remote main commit before every release or restoration and refuses a release if remote main has moved.
- Restore by creating a new commit with the selected release tree; never force-push main or delete history.

## 2. Publish task material

- Create `assignments/tasks.json`, six fixture sets and JSON submission templates.
- Generate six Issue forms from the task catalog with `scripts/build_course_forms.py`.
- Cover Prompt, RAG, Function Call, context engineering, capability selection and Skill/Harness.
- Set no invented deadline; teacher can configure a UTC deadline per task.
- Explain that 80 points assess structured results and 20 assess presence of prompt records, not proof of tool use or report quality.

## 3. Collect and grade

- Create `scripts/course_grading.py`, `scripts/course_github.py` and `.github/workflows/course-grade.yml`.
- Test correct/wrong answers, missing/null/boolean/non-finite values, duplicate JSON keys, forged identities/scores, edited submissions, authorization, malformed input, and CSV formula injection.
- Trust the issue author's GitHub account and fetch current issue content. Never use student-supplied scores or execute their code. Limit output size; sanitize displayed text.
- Persist current result and bounded history by issue number; repeated grading of identical input must not create duplicate records/comments.
- On manual override require a teacher-triggered workflow dispatch, a reason and a score in [0,100].

## 4. Teacher export

- Create `.github/workflows/course-export.yml`; export all submissions and one latest submission per GitHub account/task, flag changed ungraded submissions, preserve manual review reasons.
- Generate UTF-8 BOM CSV, standard XLSX without additional dependencies, and JSON. Protect spreadsheet cells against formulas.
- Explain artifact expiration; persistent records stay in `course-grades`, and exports can be regenerated.

## 5. Student and teacher pages

- Add `assignments/index.html`, `assignments/course.css` and `assignments/course.js`.
- Add home navigation and a matching task section without changing lectures/projects.
- Provide task details, input attachments, template downloads, optional local JSON preview, submit buttons, records links and teacher workflow/export links.
- Preview is advisory and not the authoritative recorded score.
- Test desktop/mobile layout, theme, keyboard accessibility, all downloads and GitHub links.

## 6. Verify and release

- Run grading tests, catalog/form validation and JavaScript syntax checks locally.
- Publish only after checks pass, through the snapshotting release script.
- Confirm GitHub Pages deployed the expected commit.
- Create one explicitly labelled instructor smoke-test submission, confirm automated feedback and record, run teacher export and inspect CSV/XLSX; close test issue afterward and exclude test records from student exports.
- Save rollback instructions and deliverable links.
