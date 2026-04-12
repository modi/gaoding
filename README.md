# gaoding

“搞定”一些小事情。

## 安装

```bash
pip install gaoding
```

## 命令

### update_env_file - 升级 .env 文件

根据示例文件和旧文件生成新的 .env 文件，保留用户修改。

**合并规则：**
1. 优先使用用户的修改
2. 在示例文件中不存在的变量将写入到新文件的末尾，且按字母顺序排序

```bash
gaoding update_env_file -d .env.dist -o .env -n .env.new
```

参数：
- `-d, --dist` - 示例 .env 文件路径
- `-o, --old` - 旧的 .env 文件路径
- `-n, --new` - 新的 .env 文件路径
- `-f, --force` - 强制覆盖已存在的新文件

### migrate - 数据库迁移管理

基于 [golang-migrate](https://github.com/golang-migrate/migrate) 的数据库迁移管理工具。

```bash
# 创建新迁移
gaoding migrate create add_users_table

# 执行迁移
gaoding migrate up

# 回滚迁移
gaoding migrate down

# 查看版本
gaoding migrate version

# 强制设置版本
gaoding migrate force 20240101000000
```

参数：
- `-c, --config` - JSON 配置文件路径（默认为当前目录的 migration-config.json）
- `--db` - 数据库配置 key（默认：default）

**配置文件示例 (migration-config.json)：**
```json
{
  "databases": {
    "default": {
      "database_url": "postgres://user:pass@localhost:5432/dbname?sslmode=disable",
      "migrations_dir": "./migrations"
    }
  }
}
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## 许可证

[Apache License 2.0](LICENSE)
