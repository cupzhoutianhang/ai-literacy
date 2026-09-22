# L08 Context Engineering：记忆选择与中间丢失

项目把上下文工程拆成 `memory.write`、Embedding 相似度 `select`、预算约束下的 `compress`、标签范围 `isolate`，并输出 token 估算和“中间丢失”对比。实现通过 `../../shared/embeddings.py` 调用本地 `BAAI/bge-small-zh-v1.5`；模型不可用时默认退回可重复的 hashing 向量，便于课堂先跑通流程。

```powershell
cd outputs/ai-literacy-projects
python projects/l08-context-engineering/main.py
# 强制要求本地模型（未下载时会给出清晰错误）
python projects/l08-context-engineering/main.py --local
pytest projects/l08-context-engineering
```

安装本地模型依赖：`pip install -e .`。首次运行会按 Sentence-Transformers 的缓存策略加载模型；也可以预先下载到离线缓存。实验数据是合成句子，不含真实工艺资料。
