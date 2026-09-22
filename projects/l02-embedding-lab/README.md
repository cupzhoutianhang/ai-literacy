# L02 · 能源术语 Embedding 实验室

使用共享模块 `../../shared/embeddings.py` 调用本地 `BAAI/bge-small-zh-v1.5`，计算能源术语与查询的余弦相似度，并用 KMeans 做一个小型聚类。模型第一次运行会从 Hugging Face 下载，之后使用本地缓存；程序本身不会下载教学数据。

## 安装与运行

```bash
pip install -e ../../[dev]
python main.py --query "锅炉温度异常" --top-k 5 --clusters 3
```

如果尚未安装 `sentence-transformers`，程序会明确提示 `pip install sentence-transformers`。在无网络环境中，请先把模型缓存到本地，并通过 `EMBEDDING_MODEL` 指向模型目录。

## 示例数据

`data/energy_terms.csv` 只有少量能源领域术语，便于课堂快速运行。可替换为自己的 CSV（列名需包含 `term`，可选 `category`）。

## 测试

测试使用假的向量，不会触发模型下载：

```bash
pytest tests -q
```

