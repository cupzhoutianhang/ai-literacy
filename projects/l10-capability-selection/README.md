# L10 AI 能力选择决策树

输入一个能源场景需求，项目根据“是否需要资料、工具、多个步骤、固定格式或风格适配”选择 Prompt、RAG、Function Call、MCP、Agent 或 Fine-tuning，并输出理由、风险和下一步。

```powershell
python main.py "请根据安全规程回答储罐泄漏的应急步骤"
python main.py "自动巡检传感器并解释异常"
```

这是确定性决策树，便于课堂上修改规则、讨论能力边界，再与大模型方案比较。

