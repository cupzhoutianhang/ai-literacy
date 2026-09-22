from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def discover_skills(root: Path = ROOT / "skills") -> list[Path]:
    return sorted(path for path in root.glob("*/SKILL.md") if path.is_file())


def load_skill(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.parent.name)
    sections = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    return {"name": path.parent.name, "title": title, "sections": sections, "path": str(path)}


def run_smoke() -> dict[str, object]:
    skills = discover_skills()
    loaded = [load_skill(path) for path in skills]
    return {"skills_found": len(loaded), "skills": loaded, "status": "passed" if loaded else "failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description="第十一讲：Skill/Harness/Plugin 最小工程样例")
    parser.add_argument("--smoke", action="store_true", help="运行 Skill 发现和加载 smoke test")
    args = parser.parse_args()
    result = run_smoke()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
