# L11 Agent 工程体系：Skill、Harness、Plugin

这个项目用一个最小可运行样例展示三层结构：Skill 保存可复用方法，Harness 负责发现/加载/运行，Plugin 用 manifest 声明可分发组件。

```powershell
python main.py --smoke
```

先加载 Skill 的标题和章节，再由 Harness 决定何时读取完整内容。这样可以把验证过的能源场景方法沉淀下来，再接入大模型或工具调用。

