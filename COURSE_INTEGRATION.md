# 课程项目集成说明

## 运行架构

课程项目默认把 Embedding 放在运行项目的机器上，把文本生成交给 SSH 隧道后的服务器 vLLM：

```text
项目 -> 127.0.0.1:18002/v1 -> SSH tunnel -> server:8002/v1 -> Qwen3-32B / LoRA
项目 -> BAAI/bge-small-zh-v1.5 (local) -> Chroma (local)
```

服务器上的模型名可以通过 `/v1/models` 查看；当前推荐使用 `main`。如需切换模型，只修改 `.env` 的 `LLM_MODEL`。

## Windows 初始化

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev,rag,mcp,web]"
Copy-Item .env.example .env
```

另开一个 PowerShell 窗口保持隧道：

```powershell
ssh -N -L 18002:127.0.0.1:8002 010
```

检查依赖和模型连接：

```powershell
python scripts/check_env.py
python scripts/check_llm.py
```

## 设计约定

- 项目默认提供确定性或 `--mock` 模式，便于没有网络和 API 的课堂演示。
- 真实大模型调用都通过 `shared/llm_client.py`，不在项目中写死 URL 或密钥。
- 真实设施数据不能直接放入示例目录；样例数据必须是合成数据或脱敏数据。
- 每个项目 README 需要说明资源、运行命令、预期输出和失败排查方法。

