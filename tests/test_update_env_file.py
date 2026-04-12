import textwrap
from pathlib import Path

import pytest

from gaoding.update_env_file import generate_env, parse_env_file


def _normalize_content(content: str) -> str:
    """去除首行换行和缩进"""
    if not content:
        return content
    # 去除第一个换行符
    content = content[1:] if content.startswith("\n") else content
    # 去除每行的公共缩进
    return textwrap.dedent(content)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_env_file(tmp_path):
    """创建临时 .env 文件，写入指定内容，测试完成后自动清理"""

    def _create_file(content: str = "") -> Path:
        file_path = tmp_path / ".env"
        if content:
            file_path.write_text(_normalize_content(content))
        return file_path

    return _create_file


@pytest.fixture
def env_file_set(tmp_path):
    """创建一组 env 文件（dist、old、new），测试完成后自动清理"""

    class EnvFileSet:
        def __init__(self, tmp_dir: Path):
            self.dist = tmp_dir / ".env.dist"
            self.old = tmp_dir / ".env.old"
            self.new = tmp_dir / ".env.new"
            self.tmp_dir = tmp_dir

        def setup(self, dist_content: str = "", old_content: str = ""):
            """设置文件内容"""
            if dist_content:
                self.dist.write_text(_normalize_content(dist_content))
            if old_content:
                self.old.write_text(_normalize_content(old_content))
            return self

        def run_generate(self):
            """执行生成操作"""
            generate_env(str(self.dist), str(self.old), str(self.new))
            return self.new.read_text()

    return EnvFileSet(tmp_path)


# =============================================================================
# 参数化测试：parse_env_file 边界情况
# =============================================================================


@pytest.mark.parametrize(
    "content,expected_vars,expected_lines",
    [
        ("", {}, []),
        ("# 注释\n", {}, [("# 注释\n", None, None)]),
        (
            """
KEY1=value1
""",
            {"KEY1": "value1"},
            [("KEY1=value1\n", "KEY1", "value1")],
        ),
    ],
)
def test_parse_env_file_edge_cases(
    temp_env_file, content, expected_vars, expected_lines
):
    """测试解析 .env 文件的边界情况"""
    file_path = temp_env_file(content)
    vars_dict, lines = parse_env_file(str(file_path))
    assert vars_dict == expected_vars
    assert lines == expected_lines


# =============================================================================
# parse_env_file 测试
# =============================================================================


def test_parse_env_file(temp_env_file):
    """测试解析 .env 文件"""
    content = """
# 注释
KEY1=value1
KEY2=value2

# 另一个注释
KEY3=value3
"""
    file_path = temp_env_file(content)
    vars_dict, lines = parse_env_file(str(file_path))
    assert vars_dict == {"KEY1": "value1", "KEY2": "value2", "KEY3": "value3"}
    assert len(lines) == 6  # 包括注释和空行（去掉了三引号的首行空行）


def test_parse_env_file_nonexistent():
    """测试解析不存在的 .env 文件"""
    vars_dict, lines = parse_env_file("/nonexistent/file.env")
    assert vars_dict == {}
    assert lines == []


# =============================================================================
# 参数化测试：基本生成行为
# =============================================================================


@pytest.mark.parametrize(
    "dist_content,old_content,expected_in_new",
    [
        pytest.param(
            """
KEY1=dist_value1
KEY2=dist_value2
""",
            """
KEY1=old_value1
KEY2=old_value2
KEY3=old_value3
""",
            ["KEY1=old_value1", "KEY2=old_value2", "KEY3=old_value3"],
            id="旧值优先-保留额外变量",
        ),
        pytest.param(
            """
KEY1=value1
""",
            """
KEY1=old_value1
EXTRA_VAR=extra_value
""",
            ["KEY1=old_value1", "EXTRA_VAR=extra_value"],
            id="保留额外变量",
        ),
    ],
)
def test_generate_env_basic_behavior(
    env_file_set, dist_content, old_content, expected_in_new
):
    """测试基本的 .env 文件生成行为"""
    new_content = env_file_set.setup(dist_content, old_content).run_generate()
    for expected in expected_in_new:
        assert expected in new_content


# =============================================================================
# generate_env 特定功能测试
# =============================================================================


def test_generate_env_preserves_comments(env_file_set):
    """测试保留注释"""
    dist_content = """
# 这是注释
KEY1=value1
"""
    old_content = """
KEY1=old_value1
"""
    new_content = env_file_set.setup(dist_content, old_content).run_generate()
    assert "# 这是注释" in new_content
    assert "KEY1=old_value1" in new_content


def test_generate_env_extra_keys_sorted(env_file_set):
    """测试额外的变量按字母顺序排序"""
    dist_content = """
KEY1=value1
"""
    old_content = """
KEY1=old_value1
KEY3=value3
KEY2=value2
"""
    new_content = env_file_set.setup(dist_content, old_content).run_generate()
    lines = new_content.split("\n")
    key2_idx = next(i for i, line in enumerate(lines) if "KEY2=" in line)
    key3_idx = next(i for i, line in enumerate(lines) if "KEY3=" in line)
    assert key2_idx < key3_idx


def test_generate_env_new_vars_appended(env_file_set):
    """测试旧文件中存在但 dist 文件中不存在的变量被追加到末尾"""
    dist_content = """
KEY1=value1
"""
    old_content = """
KEY1=old_value1
EXTRA_VAR=extra_value
"""
    new_content = env_file_set.setup(dist_content, old_content).run_generate()
    assert "KEY1=old_value1" in new_content
    assert "EXTRA_VAR=extra_value" in new_content
    key1_idx = new_content.index("KEY1=")
    extra_idx = new_content.index("EXTRA_VAR=")
    assert extra_idx > key1_idx
