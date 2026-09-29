"""Unit tests for filesystem and tool operations."""

from ace.tools.file_ops import write_file, read_file, list_files, apply_diff

def test_file_write_and_read(tmp_path):
    rel_path = "src/calculator.py"
    content = "def add(a, b):\n    return a + b\n"
    
    res = write_file(rel_path, content, base_dir=tmp_path)
    assert res["is_new"] is True
    assert res["file_path"] == rel_path
    
    read_back = read_file(rel_path, base_dir=tmp_path)
    assert read_back == content

def test_apply_diff(tmp_path):
    rel_path = "app.py"
    initial_content = "def main():\n    print('old')\n"
    write_file(rel_path, initial_content, base_dir=tmp_path)
    
    success = apply_diff(
        file_path=rel_path,
        search_block="print('old')",
        replace_block="print('new')",
        base_dir=tmp_path
    )
    assert success is True
    assert "print('new')" in read_file(rel_path, base_dir=tmp_path)

def test_list_files_filters_ignored(tmp_path):
    write_file("main.py", "print(1)", base_dir=tmp_path)
    write_file(".venv/bin/python", "binary", base_dir=tmp_path)
    write_file("__pycache__/main.cpython.pyc", "cache", base_dir=tmp_path)
    
    files = list_files(base_dir=tmp_path)
    assert files == ["main.py"]
