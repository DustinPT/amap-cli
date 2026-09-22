# amap-cli

`amap-cli` 是一个基于高德开放平台 Web API 的纯命令行工具，面向终端环境和 AI Agent 使用。

## 功能特性

- 纯命令行调用高德地图 API
- 支持命令行写入和读取高德 API Key
- 支持地理编码
- 支持两点直线距离计算
- 支持路径规划
- 支持 POI 搜索
- 所有命令统一返回机器可读 JSON
- 提供配套的 Agent skill，便于在智能体环境中直接调用

## 安装与使用

### 方式一：直接使用 `uvx` 运行

项目发布到 PyPI 后，可以直接执行：

```bash
uvx amap-cli --help
```

配置高德 API Key：

```bash
uvx amap-cli config set --api-key <YOUR_AMAP_KEY>
```

高德免费账号默认限流较严，工具默认会在每次 API 调用结束后 sleep `0.34` 秒；如需调整或关闭，可配置：

```bash
uvx amap-cli config set --request-sleep-seconds 0.34
uvx amap-cli config set --request-sleep-seconds 0
```

地理编码示例：

```bash
uvx amap-cli geocode --address 北京南站
```

路径规划示例：

```bash
uvx amap-cli route \
  --from 北京南站 \
  --to 天安门 \
  --type driving
```

直线距离示例：

```bash
uvx amap-cli distance \
  --from 116.397,39.909 \
  --to 116.407,39.904
```

POI 搜索示例：

```bash
uvx amap-cli search-poi \
  --keyword 星巴克 \
  --city 北京 \
  --pageSize 5
```

### 方式二：安装后使用

如果希望安装到本机工具目录，执行：

```bash
uv tool install amap-cli
```

安装完成后可直接调用：

```bash
amap-cli --help
```

配置和业务命令示例：

```bash
amap-cli config set --api-key <YOUR_AMAP_KEY>
amap-cli geocode --address 北京南站
amap-cli distance --from 116.397,39.909 --to 116.407,39.904
amap-cli route --from 北京南站 --to 天安门 --type driving
amap-cli search-poi --keyword 星巴克 --city 北京
```

## Skill 使用说明

本项目提供了配套的 `amap-cli` skill，适合在支持 skill 的 Agent 环境中使用。

- skill 的目标是让 Agent 直接通过 `uvx amap-cli` 调用本工具
- 使用方式与上面的“直接使用 `uvx` 运行”一致
- 使用前先配置高德 API Key，之后即可发起地理编码、路径规划和 POI 搜索
- `distance` 命令在起终点都为坐标时可直接本地计算，不依赖 API Key
- 建议 Agent 直接解析命令返回的 JSON 结果

如果需要将内置 skill 安装到指定目录，例如 Agent 的 skills 根目录，可以执行：

```bash
amap-cli install-skill --dir ~/.agents/skills
```

执行后会在目标目录下生成：

```text
~/.agents/skills/amap-cli/SKILL.md
```

如果目标目录中已存在同名 skill，可追加 `--force` 覆盖：

```bash
amap-cli install-skill --dir ~/.agents/skills --force
```

## 命令说明

### 配置

写入 API Key：

```bash
amap-cli config set --api-key <YOUR_AMAP_KEY>
```

设置每次高德 API 调用结束后的 sleep 时间：

```bash
amap-cli config set --request-sleep-seconds 0.34
```

关闭该 sleep：

```bash
amap-cli config set --request-sleep-seconds 0
```

查看当前配置：

```bash
amap-cli config show
```

配置会按照当前操作系统规范保存在用户配置目录中。macOS 下默认路径为：

```text
~/Library/Application Support/amap-cli/config.json
```

说明：

- `request_sleep_seconds` 默认为 `0.34`
- 该配置会在每次真实的高德 API 调用结束后执行一次 sleep
- 设置为 `0` 表示关闭节流等待

### 安装 Skill

基础格式：

```bash
amap-cli install-skill --dir <skills目录>
```

可选参数：

- `--force`

说明：

- 会将内置的 `amap-cli` skill 安装到目标目录下的 `amap-cli/` 子目录
- 当目标目录不存在时会自动创建
- 当目标目录中已存在同名 skill 时，默认报错；追加 `--force` 后会覆盖

### 地理编码

基础格式：

```bash
amap-cli geocode --address <结构化地址|地标名称>
```

可选参数：

- `--city`

说明：

- 调用高德地理编码接口，将结构化地址或地标性名胜景区、建筑物名称解析为坐标
- 传入 `--city` 时，会优先在对应城市范围内解析
- 返回结果中的 `geocode.location` 为 `[经度, 纬度]`
- 返回结果中的 `geocode.formattedAddress` 为高德返回的标准化地址
- 对于较模糊的名称，建议补充更完整地址或增加 `--city`

### 路径规划

基础格式：

```bash
amap-cli route \
  --from <结构化地址|地标名称|经度,纬度> \
  --to <结构化地址|地标名称|经度,纬度> \
  --type <driving|walking|riding|transit>
```

可选参数：

- `--from-name`
- `--to-name`
- `--waypoints`
- `--policy`
- `--strategy`
- `--city`

说明：

- `--waypoints` 和 `--policy` 仅 `driving` 支持
- `--strategy` 和 `--city` 仅 `transit` 支持
- 地理编码仅支持详细的结构化地址，以及地标性名胜景区、建筑物名称
- 当起点、终点或途经点使用上述名称并解析成功时，返回结果中的对应节点会附带 `formattedAddress`
- 对于其他较模糊的名称，建议先通过 `search-poi` 获取目标地点坐标，再调用 `route`
- 不支持 `--json` 输入

### 直线距离

基础格式：

```bash
amap-cli distance \
  --from <结构化地址|地标名称|经度,纬度> \
  --to <结构化地址|地标名称|经度,纬度>
```

可选参数：

- `--from-name`
- `--to-name`

说明：

- 当 `--from` 和 `--to` 都是坐标时，直接在本地计算直线距离
- 当任一输入为结构化地址或地标性名胜景区、建筑物名称时，会先调用高德地理编码接口解析坐标，再做本地计算
- 当输入为上述名称时，返回结果中的 `state.from.formattedAddress` / `state.to.formattedAddress` 会带上高德解析出的完整地址
- 对于其他较模糊的名称，建议先通过 `search-poi` 获取目标地点坐标，再调用 `distance`
- 结果中的 `summary.distance` 单位为米
- 不支持 `--json` 输入

### POI 搜索

基础格式：

```bash
amap-cli search-poi --keyword <关键词>
```

可选参数：

- `--city`
- `--center`
- `--radius`
- `--pageSize`
- `--pageIndex`

说明：

- 传入 `--center` 时执行周边搜索
- 未传入 `--center` 时执行关键词搜索
- 不支持 `--json` 输入

## 输出格式

成功时：

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

失败时：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "错误说明",
    "details": {}
  }
}
```

## 本地开发

安装项目依赖：

```bash
uv sync
```

本地运行：

```bash
uv run amap-cli --help
```

## PyPI 发布

### 1. 确认版本号

每次发布前，先更新 `pyproject.toml` 中的 `version`。  
PyPI 不允许重复上传同一个版本号的分发包。

### 2. 构建分发包

```bash
uv build
```

构建成功后会在 `dist/` 目录下生成：

- `*.tar.gz`
- `*.whl`

### 3. 准备 PyPI Token

登录 PyPI 后创建 API Token，推荐通过环境变量传入：

```bash
export UV_PUBLISH_TOKEN="pypi-你的token"
```

### 4. 先发布到 TestPyPI 验证（推荐）

```bash
uv publish \
  --publish-url https://test.pypi.org/legacy/ \
  --check-url https://test.pypi.org/simple/
```

如果只是验证包能否被安装，可以执行：

```bash
uvx --index https://test.pypi.org/simple/ amap-cli --help
```

### 5. 发布到正式 PyPI

确认 TestPyPI 验证通过后，执行：

```bash
uv publish
```

### 6. 发布后验证

发布完成后，推荐优先使用 `uvx` 做一次快速验证：

```bash
uvx amap-cli --help
```

发布后，推荐优先使用 `uvx amap-cli` 进行一次性调用，或使用 `uv tool install amap-cli` 安装到本地。
