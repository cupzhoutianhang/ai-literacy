'use strict';
(function () {
  const repo = 'https://github.com/cupzhoutianhang/ai-literacy';
  let tasks = [];
  const $ = id => document.getElementById(id);
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safePath = value => typeof value === 'string' && /^(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]+$/.test(value) && !value.split('/').includes('..');
  const submitUrl = task => repo + '/issues/new?template=' + task.id.toLowerCase() + '.yml';
  function deadline(task) {
    if (!task.deadline) return '开放练习 · 未设截止';
    return '截止 ' + new Date(task.deadline).toLocaleString('zh-CN', {timeZone:'Asia/Shanghai', hour12:false}) + '（北京时间）';
  }
  function renderTasks() {
    $('task-count').textContent = tasks.length + ' 项任务 · 每题 100 分';
    $('task-list').innerHTML = tasks.map(task => '<article class="task-card" data-task="' + esc(task.id) + '"><span class="task-id">' + esc(task.id) + ' / 豆包工作</span><h3>' + esc(task.title) + '</h3><p>' + esc(task.brief) + '</p><div class="meta">相关讲次 ' + task.lessons.map(n => 'L' + String(n).padStart(2,'0')).join(' / ') + ' · 约 ' + esc(task.minutes) + ' 分钟<br>' + esc(deadline(task)) + '</div><button class="button" type="button" data-open="' + esc(task.id) + '">查看题目与附件 →</button></article>').join('');
    $('preview-task').innerHTML = tasks.map(task => '<option value="' + esc(task.id) + '">' + esc(task.id + ' · ' + task.title) + '</option>').join('');
  }
  function showTask(id, scroll) {
    const task = tasks.find(item => item.id === id);
    if (!task) return;
    const panel = $('task-detail');
    panel.innerHTML = '<div class="detail-header"><div><p class="eyebrow">' + esc(task.id) + ' / TASK BRIEF</p><h2>' + esc(task.title) + '</h2><p class="muted">' + esc(deadline(task)) + '</p></div><button class="quiet" type="button" id="close-task" aria-label="关闭任务详情">关闭 ×</button></div><div class="detail-grid"><div><p>' + esc(task.brief) + '</p><h3>要完成的工作</h3><ol>' + task.instructions.map(line => '<li>' + esc(line) + '</li>').join('') + '</ol><h3>题目附件</h3><ul class="files">' + task.attachments.map(file => '<li><a href="' + esc(file.path) + '" download>↓ ' + esc(file.name) + '</a></li>').join('') + '<li><a href="' + esc(task.template) + '" download>↓ answer-template.json · 成果模板</a></li><li><a href="' + task.id.toLowerCase() + '/task-attachments.zip" download>↓ 题目与附件 ZIP</a></li></ul><div class="actions"><a class="button primary" href="' + submitUrl(task) + '">提交 ' + esc(task.id) + ' 作业 ↗</a><a class="button" href="#submission">查看提交说明</a></div></div><aside class="rubric"><h3>评分细则 / 100 分</h3><ul>' + task.rubric.map(rule => '<li>' + esc(rule.label) + ' · ' + rule.points + ' 分</li>').join('') + '<li>首次提示词记录完整 · 10 分</li><li>修订提示词记录完整 · 10 分</li></ul><p class="muted">每条提示词至少 30 个非空白字符。过程分不证明实际使用了豆包。JSON 自动检查；补充附件供教师复核。</p><p class="muted">修改时编辑原 Issue 正文。提交后稍候查看自动回复；正式分数以自动反馈或教师复核为准。</p></aside></div>';
    panel.hidden = false;
    $('preview-task').value = id;
    document.querySelectorAll('.task-card').forEach(card => card.classList.toggle('selected', card.dataset.task === id));
    const url = new URL(location.href); url.searchParams.set('task', id); history.replaceState(null, '', url);
    $('close-task').addEventListener('click', () => {
      panel.hidden = true;
      document.querySelectorAll('.task-card').forEach(card => card.classList.remove('selected'));
      const next = new URL(location.href); next.searchParams.delete('task'); history.replaceState(null, '', next);
      document.querySelector('[data-open="' + id + '"]').focus();
    });
    if (scroll) { panel.scrollIntoView({block:'start'}); panel.focus({preventScroll:true}); }
  }
  function getPath(object, path) {
    return path.split('.').reduce((value,key) => value && typeof value === 'object' && Object.hasOwn(value,key) ? value[key] : undefined, object);
  }
  $('theme').addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('theme', theme); } catch (error) {}
  });
  $('task-list').addEventListener('click', event => {
    const button = event.target.closest('[data-open]');
    if (button) showTask(button.dataset.open, true);
  });
  $('record-search').addEventListener('submit', event => {
    event.preventDefault();
    const login = $('github-name').value.trim();
    if (!/^[A-Za-z0-9-]{1,39}$/.test(login)) return;
    location.href = repo + '/issues?q=' + encodeURIComponent('is:issue label:course-submission author:' + login);
  });
  $('preview-check').addEventListener('click', () => {
    const status = $('preview-result');
    try {
      const raw = $('preview-json').value;
      if (raw.length > 24000) throw new Error('JSON 过长，请控制在 24000 字符以内。');
      const value = JSON.parse(raw);
      if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error('顶层必须是 JSON 对象。');
      const task = tasks.find(item => item.id === $('preview-task').value);
      if (!task) throw new Error('请选择任务。');
      const missing = task.rubric.filter(rule => getPath(value, rule.path) === undefined).map(rule => rule.path);
      if (missing.length) throw new Error('缺少字段：' + missing.join('、'));
      for (const key of ['first_prompt','revision_prompt']) {
        const prompt = getPath(value, 'process.' + key);
        if (typeof prompt !== 'string' || prompt.replace(/\s/g,'').length < 30) throw new Error('process.' + key + ' 至少需要 30 个非空白字符。');
      }
      status.classList.remove('error');
      status.textContent = 'JSON 可以解析，必需字段与过程记录已填写。尚未检查答案正确性、重复字段或文件证据；请提交后以 GitHub 的正式反馈为准。';
    } catch (error) {
      status.classList.add('error'); status.textContent = error instanceof SyntaxError ? 'JSON 语法错误，请检查双引号、逗号和括号。' : error.message;
    }
  });
  fetch('tasks.json', {cache:'no-cache'}).then(response => {
    if (!response.ok) throw new Error('任务目录暂时无法读取');
    return response.json();
  }).then(catalog => {
    tasks = catalog.tasks.filter(task => task.published);
    tasks.forEach(task => {
      if (!/^A\d{2}$/.test(task.id) || !safePath(task.template) || task.attachments.some(file => !safePath(file.path))) throw new Error('任务配置需要教师检查');
    });
    renderTasks();
    const id = new URL(location.href).searchParams.get('task');
    if (id) showTask(id, false);
  }).catch(error => {
    $('task-count').textContent = error.message + '，请稍后刷新。';
    $('task-list').innerHTML = '<p><a href="' + repo + '/tree/main/assignments">在 GitHub 直接阅读题目与附件 ↗</a></p>';
  });
}());
