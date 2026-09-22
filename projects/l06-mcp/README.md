# L06 MCP：本地资源与工具服务器

这是一个不依赖 SDK 的 MCP 形状教学样例。`LocalMCPServer.dispatch` 展示初始化、资源列表/读取、工具列表和工具调用；`--stdio` 模式使用每行一个 JSON 请求，便于观察协议数据。生产项目可以把这些处理器迁移到官方 Python SDK。

```powershell
cd outputs/ai-literacy-projects
python projects/l06-mcp/main.py
python projects/l06-mcp/main.py --stdio
# 可选：安装官方 SDK 后做进一步改写
pip install "mcp>=1.0"
pytest projects/l06-mcp
```

示例资源是 `energy://sensors` 和 `energy://procedures/pressure-drop`；示例工具是 `query_sensor`、`calculate_pressure_drop`。数据均为合成教学数据。
