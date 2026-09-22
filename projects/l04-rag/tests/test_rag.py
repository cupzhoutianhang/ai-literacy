from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parents[1]))
spec = importlib.util.spec_from_file_location("l04_main", Path(__file__).parents[1] / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
Chunk, chunk_markdown, format_context = main.Chunk, main.chunk_markdown, main.format_context


def test_chunk_markdown_preserves_source_and_bounds():
    chunks = chunk_markdown("# 标题\n\n第一段。\n\n第二段。", source="demo.md", max_chars=20)
    assert chunks
    assert all(chunk.source == "demo.md" for chunk in chunks)
    assert all(len(chunk.text) <= 20 for chunk in chunks)


def test_format_context_has_source_markers():
    context = format_context([Chunk("a.md", 0, "温度上升"), Chunk("a.md", 1, "检查风机")])
    assert "[S1] 温度上升" in context
    assert "[S2] 检查风机" in context
