# L01 · 下一个词预测实验室

这个小项目用一段很小的能源领域语料演示 token、词频、Bigram（相邻词）统计和“给定前文预测下一个 token”。最后还用 NumPy 计算一个轻量的注意力权重，帮助理解模型如何对上下文位置加权。它不需要 API 或模型下载。

## 运行

从 `outputs/ai-literacy-projects` 目录执行：

```bash
python projects/l01-next-token/main.py
python projects/l01-next-token/main.py --text "锅炉 温度 升高" --top-k 5 --attention
```

## 观察重点

- token 在本项目中是中文单字、英文数字串或标点；生产模型会使用更复杂的子词 tokenizer。
- Bigram 概率来自计数，因此语料很小，只适合课堂演示。
- `--attention` 会输出每个上下文 token 的 softmax 权重，没有调用大模型。

## 测试

```bash
pytest projects/l01-next-token/tests -q
```

