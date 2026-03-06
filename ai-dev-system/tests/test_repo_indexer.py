from tools.repo_indexer import RepoIndexer


def test_repo_search_returns_list(tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("def hello_world():\n    return 'hello'\n", encoding="utf-8")

    indexer = RepoIndexer(str(tmp_path))
    results = indexer.search("hello world")

    assert isinstance(results, list)
    assert results
