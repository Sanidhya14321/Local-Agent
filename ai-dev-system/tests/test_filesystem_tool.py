from tools.filesystem_tool import FilesystemTool


def test_write_and_read(tmp_path):
    fs = FilesystemTool(str(tmp_path))
    fs.write_file("src/app.py", "print('ok')\n")

    content = fs.read_file("src/app.py")
    assert content == "print('ok')\n"
