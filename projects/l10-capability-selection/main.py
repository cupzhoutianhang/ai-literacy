from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Decision:
    capability: str
    reason: str
    risks: list[str]
    next_step: str


def choose_capability(requirement: str) -> Decision:
    text = requirement.lower()
    if any(word in text for word in ("规程", "文献", "手册", "资料", "依据")):
        return Decision("RAG", "问题需要引用私有或时效性资料", ["资料过期", "召回不全"], "整理文档并建立可追溯索引")
    if any(word in text for word in ("查询实时", "传感器", "计算", "调用", "数据库")):
        return Decision("Function Call", "问题需要读取数据或执行确定性计算", ["参数校验", "权限边界"], "定义 JSON Schema 和工具白名单")
    if any(word in text for word in ("多步", "自动巡检", "反复", "分解任务", "自主")):
        return Decision("Agent", "问题包含多步决策和工具编排", ["循环失控", "错误操作"], "先限制最大步数并记录审计日志")
    if any(word in text for word in ("接入系统", "协议", "多个工具", "mcp")):
        return Decision("MCP", "问题需要统一接入外部工具与资源", ["工具权限", "版本兼容"], "先设计 Server 的 resources/tools/prompts")
    if any(word in text for word in ("固定格式", "日报", "改写", "总结", "提取")):
        return Decision("Prompt", "任务主要是稳定的语言变换", ["格式漂移", "输入越界"], "写出角色、输入、约束和输出格式")
    if any(word in text for word in ("风格", "术语习惯", "大量样例", "训练")):
        return Decision("Fine-tuning", "任务需要稳定改变模型行为或风格", ["数据偏差", "过拟合", "维护成本"], "先做 Prompt/RAG 基线再决定是否微调")
    return Decision("Prompt", "当前需求信息不足，先用最小方案验证", ["需求理解偏差"], "补充输入、输出、资料和工具四类约束")


def main() -> int:
    parser = argparse.ArgumentParser(description="第十讲：从需求选择 AI 能力")
    parser.add_argument("requirement", nargs="+", help="自然语言需求")
    args = parser.parse_args()
    print(json.dumps(asdict(choose_capability(" ".join(args.requirement))), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

