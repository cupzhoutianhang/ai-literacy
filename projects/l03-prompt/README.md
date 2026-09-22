# L03 · 工艺日报结构化 Prompt

这个项目把一段工艺日报交给大模型，并要求它只返回一个 JSON 结构。`pydantic` 会在边界处校验日期、装置、指标、告警和行动项。默认推荐先跑 `--mock`，再通过 SSH 隧道连接课程服务器上的 OpenAI 兼容 vLLM。

## 运行

从项目根目录 `outputs/ai-literacy-projects` 执行：

```bash
python projects/l03-prompt/main.py --mock
python projects/l03-prompt/main.py --input projects/l03-prompt/data/sample_report.json
```

真实模式需要设置 `LLM_BASE_URL`、`LLM_MODEL`（默认为 `http://127.0.0.1:18002/v1` 和 `main`），并安装 `openai`。如果服务器返回 Markdown 代码围栏，程序会自动提取其中的 JSON 再校验。

## Prompt 要点

1. 先定义角色与输入字段；
2. 明确要求“只输出 JSON，不要解释”；
3. 给出完整 schema 与单位；
4. 把结果交给 Pydantic，而不是直接信任模型输出。

## 测试

```bash
pytest tests -q
```

