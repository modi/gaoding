import argparse

from gaoding import migrate, update_env_file


def main():
    parser = argparse.ArgumentParser(
        prog="gaoding",
        description="搞定一些小事情",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 注册各子命令
    migrate.register(subparsers)
    update_env_file.register(subparsers)

    args = parser.parse_args()

    # 统一调度
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.error("No command specified")


if __name__ == "__main__":
    main()
