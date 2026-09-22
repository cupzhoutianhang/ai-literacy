# L05 Function Call：装置传感器工具回路

这个项目把“自然语言问题 → JSON Schema 工具选择 → 参数校验 → 函数执行 → 结果解释”拆成六步。它默认使用透明的规则路由，因此没有大模型也能演示工具调用；加 `--llm` 后才让共享的 vLLM 客户端生成一句解释。

```powershell
cd outputs/ai-literacy-projects
python projects/l05-function-call/main.py "请查询泵 A 的压降"
python projects/l05-function-call/main.py "请查询泵 A 的温度" --llm
pytest projects/l05-function-call
```

`data/sensors.csv` 是教学用合成数据，不包含真实生产信息。大模型只负责解释已经执行的结果，不负责直接访问文件或执行任意函数。
