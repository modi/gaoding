#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


default_config_dir = os.getcwd()


def ensure_migrate_exists():
    """检查 golang-migrate 是否可用（跨平台）"""
    migrate_cmd = "migrate.exe" if sys.platform.startswith("win") else "migrate"
    if not shutil.which(migrate_cmd):
        print("未安装 golang-migrate")
        print("下载地址：https://github.com/golang-migrate/migrate/releases")
        sys.exit(1)
    return migrate_cmd


def mask_password(input_str):
    """隐藏数据库 URL 中的密码"""
    return re.sub(r":[^\/]*@", ":***@", input_str)


def load_config(config_loc):
    """加载配置文件"""
    config_path = Path(config_loc)
    if not config_path.exists():
        print(f"未找到配置文件：{config_path}")
        sys.exit(1)

    with config_path.open() as f:
        return json.load(f)


def get_db_config(config, db_key):
    """获取数据库配置"""
    if db_key not in config.get("databases", {}):
        print(f"未找到数据库配置: {db_key}")
        sys.exit(1)

    db_conf = config["databases"].get(db_key, {})

    database_url = db_conf.get("database_url")
    if not database_url:
        print(f"{db_key} 配置中缺少 database_url")
        sys.exit(1)
    masked_url = mask_password(database_url)
    print(f"[{db_key}] 目标数据库：{masked_url}")

    migrations_dir = db_conf.get("migrations_dir", "")
    if not os.path.isabs(migrations_dir):
        migrations_dir = os.path.join(default_config_dir, migrations_dir)
    migrations_dir = Path(migrations_dir)
    if not migrations_dir.exists():
        print(f"{migrations_dir} 目录不存在")
        sys.exit(1)
    migrations_dir = str(migrations_dir).replace("\\", "/")
    print(f"[{db_key}] 迁移目录：{migrations_dir}")

    return database_url, migrations_dir


def run_migrate(migrate_cmd, cmd_args):
    """执行迁移命令"""
    cmd = [migrate_cmd]
    cmd.extend(cmd_args)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {mask_password(str(e))}")
        sys.exit(1)


def handle_action(args):
    """处理迁移操作"""
    migrate_cmd = ensure_migrate_exists()
    config = load_config(args.config)
    database_url, migrations_dir = get_db_config(config, args.db)
    action = args.action
    extra_args = args.extra

    if action == "create":
        if not extra_args:
            print("请指定 migration 名称")
            sys.exit(1)
        migration_name = extra_args[0]
        run_migrate(
            migrate_cmd,
            ["create", "-ext", "sql", "-dir", migrations_dir, "-seq", migration_name],
        )

    elif action in ("up", "down", "force", "version"):
        run_migrate(
            migrate_cmd,
            ["-database", database_url, "-path", migrations_dir, action] + extra_args,
        )

    else:
        print("操作类型无效，可选：create、up、down、force、version")
        sys.exit(1)


def register(subparsers):
    """注册迁移子命令"""
    parser = subparsers.add_parser(
        "migrate",
        help="管理数据库迁移，基于 golang-migrate",
        description="管理数据库迁移，基于 golang-migrate",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=os.path.join(default_config_dir, "migration-config.json"),
        metavar="FILE",
        help="JSON 配置文件路径（默认为当前目录的 migration-config.json）",
    )
    parser.add_argument(
        "--db",
        type=str,
        default="default",
        help="数据库配置 key，对应配置文件中 databases 下的 key",
    )
    parser.add_argument(
        "action",
        choices=["create", "up", "down", "force", "version"],
        help="迁移操作类型",
    )
    parser.add_argument(
        "extra",
        nargs="*",
        help="额外参数，如 create 时的 migration 名称，force 的版本号等",
    )
    parser.set_defaults(func=handle_action)


if __name__ == "__main__":
    # 作为独立脚本运行时的兼容代码
    parser = argparse.ArgumentParser(description="管理数据库迁移，基于 golang-migrate")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=os.path.join(default_config_dir, "migration-config.json"),
        help="JSON 配置文件路径（默认为当前目录的 migration-config.json）",
    )
    parser.add_argument(
        "--db",
        type=str,
        default="default",
        help="数据库配置 key，对应配置文件中 databases 下的 key",
    )
    parser.add_argument(
        "action",
        choices=["create", "up", "down", "force", "version"],
        help="迁移操作类型",
    )
    parser.add_argument(
        "extra",
        nargs="*",
        help="额外参数，如 create 时的 migration 名称，force 的版本号等",
    )
    args = parser.parse_args()
    handle_action(args)
