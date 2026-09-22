# L07 Agent：受限设备巡检 Agent

Agent loop 被拆成规划、工具白名单、执行、失败处理和审计日志。默认 deterministic planner 让课堂和测试可复现；`--llm` 可用共享的 OpenAI 兼容客户端生成计划，但 JSON 计划仍会经过白名单、参数和最大步数限制。

```powershell
cd outputs/ai-literacy-projects
python projects/l07-agent/main.py "检查泵 A 温度是否异常"
python projects/l07-agent/main.py "检查泵 A 温度是否异常" --llm --max-steps 4
pytest projects/l07-agent
```

`create_ticket` 只生成状态为 `draft` 的教学工单，不会触发真实系统操作。所有数据都在 `data/inspection.csv` 中。
