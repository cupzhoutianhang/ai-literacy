from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l11_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
discover_skills, load_skill, run_smoke = main.discover_skills, main.load_skill, main.run_smoke


def test_skill_is_discoverable():
    skills = discover_skills()
    assert skills
    assert load_skill(skills[0])["name"] == "energy-report"


def test_smoke_passes():
    result = run_smoke()
    assert result["status"] == "passed"
