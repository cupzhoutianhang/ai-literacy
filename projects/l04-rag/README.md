# L04 · 安全规程 RAG 助手

这个项目把本地 Markdown 规程切成小块，使用共享的本地 BGE Embedding 建立 Chroma 向量库，再检索最相关的片段交给大模型回答。回答末尾会列出 `[S1]` 这样的来源标记，方便回到原文核对。

## 运行

从 `outputs/ai-literacy-projects` 目录执行：

```bash
pip install -e ".[rag]"
python projects/l04-rag/main.py --query "排烟温度升高应该先检查什么？"
```

首次运行会在 `data/chroma/` 建立本地持久化索引，可能需要下载 BGE 模型。可以用 `--rebuild` 重建。需要 `sentence-transformers`、`chromadb` 和 `openai`；缺少任一组件时程序会给出安装命令，不会静默失败。

想在没有大模型的情况下检查分块和检索流程，可以使用 `--mock-llm`；该模式仍需要 Embedding 与 Chroma。

```bash
python main.py --query "冷却水流量异常" --mock-llm
```

## 测试

单元测试只覆盖 Markdown 分块、上下文拼接和来源编号，不会下载模型或创建向量库：

```bash
pytest tests -q
```

