"""
该模块用于"升级" .env 文件。

功能：根据包含用户修改的 .env 文件和 .env 示例文件生成一个新的 .env 文件

合并规则：
1. 优先使用用户的修改
2. 在示例文件中不存在的变量将写入到新文件的末尾，且按字母顺序排序
"""

import argparse
import os


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


def generate_env(dist_path, old_file_path, new_file_path):
    """生成新的 .env 文件"""
    dist_vars, dist_lines = parse_env_file(dist_path)
    old_vars, _ = parse_env_file(old_file_path)

    new_lines = []

    # 1. 遍历 dist，优先使用旧 env 文件中的修改值
    for raw_line, key, val in dist_lines:
        if key is None:
            # 注释或空行
            new_lines.append(raw_line)
        else:
            # 使用旧 env 文件的值，如果有修改
            new_val = old_vars.get(key, val)
            new_lines.append(f"{key}={new_val}\n")

    # 2. 添加旧 env 文件中存在，但 dist 没有的变量，并按字母顺序排序
    extra_keys = sorted(set(old_vars.keys()) - set(dist_vars.keys()))
    if extra_keys:
        new_lines.append("\n# 示例文件中不存在的变量\n")
        for key in extra_keys:
            new_lines.append(f"{key}={old_vars[key]}\n")

    # 3. 写入新的 .env
    with open(new_file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"已生成新的 .env 文件: {new_file_path}")


def handle_action(args):
    """处理 update_env 命令"""
    dist_path = args.dist
    old_file_path = args.old
    new_file_path = args.new

    if not os.path.exists(dist_path):
        print("示例文件不存在")
        return 1

    if not os.path.exists(old_file_path):
        print("旧文件不存在")
        return 1

    # 检查新旧文件不能同名
    if old_file_path == new_file_path:
        print("错误：新文件和旧文件不能同名！")
        return 1

    if os.path.exists(new_file_path):
        if not args.force:
            overwrite = input(
                f"{new_file_path} 文件已经存在，是否覆盖? (输入 yes 确认): "
            )
            if overwrite.lower() != "yes":
                print("取消操作。")
                return 1

    generate_env(dist_path, old_file_path, new_file_path)
    return 0


def register(subparsers):
    """注册 update_env 子命令"""
    parser = subparsers.add_parser(
        "update_env_file",
        help="升级 .env 文件",
        description="根据示例文件和旧文件生成新的 .env 文件，保留用户修改",
    )
    parser.add_argument(
        "-d",
        "--dist",
        required=True,
        help="示例 .env 文件路径",
    )
    parser.add_argument(
        "-o",
        "--old",
        required=True,
        help="旧的 .env 文件路径",
    )
    parser.add_argument(
        "-n",
        "--new",
        required=True,
        help="新的 .env 文件路径",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="强制覆盖已存在的新文件",
    )
    parser.set_defaults(func=handle_action)


if __name__ == "__main__":
    # 作为独立脚本运行时的兼容代码
    parser = argparse.ArgumentParser(
        description="升级 .env 文件：根据示例文件和旧文件生成新的 .env 文件"
    )
    parser.add_argument("-d", "--dist", required=True, help="示例 .env 文件路径")
    parser.add_argument("-o", "--old", required=True, help="旧的 .env 文件路径")
    parser.add_argument("-n", "--new", required=True, help="新的 .env 文件路径")
    parser.add_argument(
        "-f", "--force", action="store_true", help="强制覆盖已存在的新文件"
    )
    args = parser.parse_args()
    exit(handle_action(args))
