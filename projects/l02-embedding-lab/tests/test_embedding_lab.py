from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))
spec = importlib.util.spec_from_file_location("l02_main", Path(__file__).parents[1] / "main.py")
main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = main
spec.loader.exec_module(main)
cosine_similarity, load_terms, rank_terms = main.cosine_similarity, main.load_terms, main.rank_terms


def test_csv_and_cosine_similarity():
    rows = load_terms(Path(__file__).parents[1] / "data/energy_terms.csv")
    assert len(rows) >= 5
    values = cosine_similarity(np.array([[1.0, 0.0], [0.0, 1.0]]), np.array([1.0, 0.0]))
    assert np.allclose(values, [1.0, 0.0])


def test_rank_terms_uses_descending_score():
    result = rank_terms(["a", "b"], "query", np.array([[1.0, 0.0], [0.0, 1.0]]), np.array([0.0, 1.0]), 2)
    assert result[0][0] == "b"
