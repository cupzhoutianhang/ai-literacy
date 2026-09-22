from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("l10_main", Path(__file__).parent / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
choose_capability = main.choose_capability


def test_private_documents_choose_rag():
    assert choose_capability("根据实验室规程回答问题").capability == "RAG"


def test_multistep_operation_choose_agent():
    assert choose_capability("自动巡检并分解多步任务").capability == "Agent"
