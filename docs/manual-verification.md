# 手动验证记录

本文记录 `amap-cli` 在本地环境中的手动验证结果，覆盖安装、帮助、配置读写以及从 CLI 主入口到业务 handler 的命令链路。

## 验证环境

- 日期：2026-09-17
- 系统：macOS
- 项目路径：`/Users/wengjing/vscode/amap_cli`
- Python/运行方式：`uv`

## 验证项

### 1. 本地安装与帮助命令

执行：

```bash
uv sync
uv run amap-cli --help
uv run python -m amap_cli --help
```

结果：

- `uv sync` 成功完成本地安装
- `amap-cli --help` 正确显示 `config`、`geocode`、`distance`、`route`、`search-poi` 五个子命令
- `python -m amap_cli --help` 与脚本入口行为一致

### 2. `geocode` 典型输入通过 CLI 主入口走通到 handler

说明：

- 使用 `amap_cli.cli.main(...)` 作为 CLI 主入口
- 通过 monkeypatch 将 `amap_cli.geocode_command.AmapApiClient` 替换为假 client
- 仍然走真实参数解析、handler 与统一 JSON 输出

验证输入：

```bash
geocode --address 北京南站
```

假 client 返回：

- `/v3/geocode/geo`：北京南站的坐标与标准化地址

结果：

- CLI 返回 `success=true`
- `state.address` 正确保留原始查询
- `geocode.location` 返回坐标数组
- `geocode.formattedAddress` 正确透传

### 3. `distance` 坐标输入走本地直线距离计算

执行：

```bash
uv run amap-cli distance --from 116.397,39.909 --to 116.407,39.904
```

结果：

- CLI 返回 `success=true`
- 无需配置 API Key 也可执行成功
- `state.mode=straight_line`
- `summary.distance` 返回两点之间的直线距离（米）

### 4. 配置写入与自动读取

为避免污染真实用户配置，验证时使用隔离 `HOME`：

```bash
TMP_HOME=$(mktemp -d)
HOME="$TMP_HOME" uv run amap-cli config set --api-key test-demo-key --timeout-seconds 12
HOME="$TMP_HOME" uv run amap-cli config show
```

结果：

- 成功写入配置文件
- macOS 下配置落在 `~/Library/Application Support/amap-cli/config.json`
- 再次执行 `config show` 时可自动读取刚写入的配置
- `api_key` 输出已脱敏

### 5. `route` 典型输入通过 CLI 主入口走通到 handler

说明：

- 使用 `amap_cli.cli.main(...)` 作为 CLI 主入口
- 通过 monkeypatch 将 `amap_cli.route.AmapApiClient` 替换为假 client
- 仍然走真实参数解析、地理编码解析、路径规划 handler 与统一 JSON 输出

验证输入：

```bash
route --from 北京南站 --to 天安门 --type driving
```

假 client 返回：

- `/v3/geocode/geo`：北京南站、天安门的坐标
- `/v3/direction/driving`：一条示例驾车路径

结果：

- CLI 返回 `success=true`
- `state.type=driving`
- 起终点地名与坐标正确进入输出
- `summary.distance`、`summary.time`、`summary.steps` 正常生成

### 6. `search-poi` 典型输入通过 CLI 主入口走通到 handler

说明：

- 使用 `amap_cli.cli.main(...)` 作为 CLI 主入口
- 通过 monkeypatch 将 `amap_cli.search_poi.AmapApiClient` 替换为假 client
- 仍然走真实参数解析、handler 与统一 JSON 输出

验证输入：

```bash
search-poi --keyword 星巴克 --city 北京 --pageSize 1
```

假 client 返回：

- `/v3/place/text`：1 条示例 POI 数据

结果：

- CLI 返回 `success=true`
- `state.keyword`、`state.city`、分页参数正确
- `pois[0]` 的名称、坐标、地址、照片链接正确归一化

## 验证中发现并修复的问题

### `output.write_json()` 默认输出流绑定过早

问题现象：

- 原实现将 `sys.stdout` 作为函数默认参数
- 在 `redirect_stdout` 等场景下，CLI 输出无法被正确捕获

影响：

- Agent 进程内调用时，不利于稳定收集 JSON 输出
- 手动验证和嵌入式调用体验不一致

修复方式：

- 将 `write_json(payload, stream=sys.stdout)` 改为 `write_json(payload, stream=None)`
- 在函数内部按调用时机解析 `sys.stdout`

结论：

- 当前六项手动验证均已通过
- CLI 主入口已完成 `geocode`、`distance`、`route`、`search-poi` 整合
