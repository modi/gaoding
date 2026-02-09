# 该脚本可用于“升级” .env 文件，功能为：根据包含用户修改的 .env 文件和 .env 示例文件生成一个新的 .env 文件
# 合并规则：（1）优先使用用户的修改（2）在示例文件中不存在的变量将写入到新文件的末尾，且按字母顺序排序
# 使用方法：`python update_env_file.py example.env old.env new.env`

import os
import sys


def parse_env_file(filepath):
    """
    解析 .env 文件
    返回：
        var_dict: {key: value}
        lines: [(raw_line, key, value)]  # key, value 为 None 表示注释或空行
    """
    vars_dict = {}
    lines = []
    if not os.path.exists(filepath):
        return vars_dict, lines
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#") or "=" not in line:
                lines.append((line, None, None))
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            vars_dict[key] = val
            lines.append((line, key, val))
    return vars_dict, lines


def generate_env(example_path, old_file_path, new_file_path):
    example_vars, example_lines = parse_env_file(example_path)
    old_vars, _ = parse_env_file(old_file_path)

    new_lines = []

    # 1. 遍历 example，优先使用旧 env 文件中的修改值
    for raw_line, key, val in example_lines:
        if key is None:
            # 注释或空行
            new_lines.append(raw_line)
        else:
            # 使用旧 env 文件的值，如果有修改
            new_val = old_vars.get(key, val)
            new_lines.append(f"{key}={new_val}\n")

    # 2. 添加旧 env 文件中存在，但 example 没有的变量，并按字母顺序排序
    extra_keys = sorted(set(old_vars.keys()) - set(example_vars.keys()))
    if extra_keys:
        new_lines.append("\n# 示例文件中不存在的变量\n")
        for key in extra_keys:
            new_lines.append(f"{key}={old_vars[key]}\n")

    # 3. 写入新的 .env
    with open(new_file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"已生成新的 .env 文件: {new_file_path}")


if __name__ == "__main__":
    EXAMPLE = sys.argv[1]
    OLD_FILE = sys.argv[2]
    NEW_FILE = sys.argv[3]

    if not os.path.exists(EXAMPLE):
        print("示例文件不存在")
        sys.exit(1)

    if not os.path.exists(OLD_FILE):
        print("旧文件不存在")
        sys.exit(1)

    # 检查新旧文件不能同名
    if OLD_FILE == NEW_FILE:
        print("错误：新文件和旧文件不能同名！")
        sys.exit(1)

    if os.path.exists(NEW_FILE):
        overwrite = input(f"{NEW_FILE} 文件已经存在，是否覆盖? (输入 yes 确认): ")
        if overwrite.lower() != "yes":
            print("取消操作。")
            sys.exit(1)

    generate_env(EXAMPLE, OLD_FILE, NEW_FILE)
