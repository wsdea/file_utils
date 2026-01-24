import glob
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "remove_duplicates.py")
)


def copy_fixtures_dir():
    src = os.path.join(os.path.dirname(__file__), "fixtures", "duplicates")
    temp_dir = tempfile.mkdtemp()
    shutil.copytree(src, temp_dir, dirs_exist_ok=True)
    return temp_dir


def test_detect_duplicates_without_removal():
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(
            os.path.join(os.path.dirname(__file__), "fixtures", "duplicates"),
            temp_dir,
            dirs_exist_ok=True,
        )
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        assert "Would remove" in output
        assert "file1_copy.txt" in output
        assert "file3_copy.txt" in output
        assert "file1.txt" not in output


def test_remove_duplicates_with_go_flag():
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(
            os.path.join(os.path.dirname(__file__), "fixtures", "duplicates"),
            temp_dir,
            dirs_exist_ok=True,
        )
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir, "--go"],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        assert "removed" in output
        assert os.path.exists(os.path.join(temp_dir, "file1.txt"))
        assert os.path.exists(os.path.join(temp_dir, "file2.txt"))
        assert not os.path.exists(os.path.join(temp_dir, "file1_copy.txt"))
        subdir = os.path.join(temp_dir, "subdir")
        assert os.path.exists(os.path.join(subdir, "file3.txt"))
        assert not os.path.exists(os.path.join(subdir, "file3_copy.txt"))


def test_empty_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        assert "Would remove" not in result.stdout


def test_no_duplicates():
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "a.txt"), "w") as f:
            f.write("a")
        with open(os.path.join(temp_dir, "b.txt"), "w") as f:
            f.write("b")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        assert "Would remove" not in result.stdout


def test_nested_directories():
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = os.path.join(temp_dir, "nested", "sub")
        os.makedirs(nested_dir)
        file_a = os.path.join(nested_dir, "a.txt")
        file_a_copy = os.path.join(nested_dir, "a_copy.txt")
        with open(file_a, "w") as f:
            f.write("data")
        with open(file_a_copy, "w") as f:
            f.write("data")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        assert "Would remove" in output
        assert "a_copy.txt" in output


def test_zero_byte_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        a = os.path.join(temp_dir, "a.txt")
        b = os.path.join(temp_dir, "b.txt")
        open(a, "w").close()
        open(b, "w").close()
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        assert "Would remove" in result.stdout


def test_same_size_different_content():
    with tempfile.TemporaryDirectory() as temp_dir:
        a = os.path.join(temp_dir, "a.txt")
        b = os.path.join(temp_dir, "b.txt")
        with open(a, "w") as f:
            f.write("aa")
        with open(b, "w") as f:
            f.write("bb")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        assert "Would remove" not in result.stdout


def test_binary_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        a = os.path.join(temp_dir, "a.bin")
        b = os.path.join(temp_dir, "b.bin")
        with open(a, "wb") as f:
            f.write(b"\x00\x01\x02")
        with open(b, "wb") as f:
            f.write(b"\x00\x01\x02")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        assert "Would remove" in result.stdout


def test_special_character_filenames():
    with tempfile.TemporaryDirectory() as temp_dir:
        a = os.path.join(temp_dir, "sp éçïål.txt")
        b = os.path.join(temp_dir, "sp éçïål_copy.txt")
        with open(a, "w") as f:
            f.write("x")
        with open(b, "w") as f:
            f.write("x")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        assert "Would remove" in result.stdout


def test_invalid_path():
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "does_not_exist"],
        capture_output=True,
        text=True,
    )
    assert "Processing directory" in result.stdout
    assert "Would remove" not in result.stdout


def test_multiple_duplicate_groups():
    with tempfile.TemporaryDirectory() as temp_dir:
        for name in ["a.txt", "a_copy.txt", "b.txt", "b_copy.txt"]:
            with open(os.path.join(temp_dir, name), "w") as f:
                f.write(name[0])
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, temp_dir],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        assert "a_copy.txt" in output
        assert "b_copy.txt" in output
