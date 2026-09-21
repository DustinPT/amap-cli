---
name: amap-cli
description: Use amap-cli for terminal-based Amap geocoding, distance calculation, route planning, and POI search. Use when the user needs machine-readable map results in this project. Do not use for GUI-based map interaction.
---

# Amap CLI

在需要高德地图地理编码、直线距离计算、路径规划或 POI 搜索时，直接调用 `amap-cli`。

## 操作规则

- 统一使用 `uvx amap-cli` 调用命令
- 优先返回和解析 JSON 结果，不依赖自然语言输出
- 在执行 `geocode`、`route` 或 `search-poi` 前，先确认高德 API Key 已配置
- 在执行 `distance` 前，若起终点包含地名，也需要先确认高德 API Key 已配置
- 如果返回 `MISSING_CONFIG`，先执行配置命令，再继续业务调用

## 初始化

先确认命令可用：

```bash
uvx amap-cli --help
```

首次使用时先配置高德 API Key：

```bash
uvx amap-cli config set --api-key <YOUR_AMAP_KEY>
```

如需查看当前配置：

```bash
uvx amap-cli config show
```

## Geocode

需要将结构化地址或地标名称解析为坐标时，使用 `geocode`：

```bash
uvx amap-cli geocode --address 北京南站
```

如果需要缩小解析范围，可追加城市：

```bash
uvx amap-cli geocode --address 软件园二期 --city 厦门
```

关键参数：

- `--address`：必填，结构化地址、地标性名胜景区或建筑物名称
- `--city`：可选，用于缩小地理编码范围

关键约束：

- 地理编码仅支持详细的结构化地址，以及地标性名胜景区、建筑物名称
- 返回结果中的 `geocode.location` 为 `[经度, 纬度]`
- 返回结果中的 `geocode.formattedAddress` 可用于判断解析是否符合预期
- 对于较模糊的名称，优先补充更完整的地址信息或追加 `--city`

## Route

需要路径规划时，使用 `route`：

```bash
uvx amap-cli route \
  --from 北京南站 \
  --to 天安门 \
  --type driving
```

如果起点或终点是坐标，直接传 `经度,纬度`：

```bash
uvx amap-cli route \
  --from 116.397,39.909 \
  --to 116.407,39.904 \
  --type walking
```

关键参数：

- `--from`：起点，支持结构化地址、地标性名胜景区/建筑物名称或 `经度,纬度`
- `--to`：终点，支持结构化地址、地标性名胜景区/建筑物名称或 `经度,纬度`
- `--type`：必填，可选 `driving`、`walking`、`riding`、`transit`
- `--from-name` / `--to-name`：坐标输入时可选，用于指定显示名称
- `--waypoints`：驾车途经点，使用 `+` 分隔，仅 `driving` 支持
- `--policy`：驾车策略，仅 `driving` 支持
- `--strategy`：公交策略，仅 `transit` 支持
- `--city`：公交规划城市，`transit` 时必填

关键约束：

- `--type transit` 必须显式传 `--city`
- `--waypoints` 和 `--policy` 只能和 `--type driving` 一起使用
- `--strategy` 只能和 `--type transit` 一起使用
- 地理编码仅支持详细的结构化地址，以及地标性名胜景区、建筑物名称
- 当输入为上述名称时，可从 `state.from.formattedAddress`、`state.to.formattedAddress` 以及 `state.waypoints[*].formattedAddress` 判断解析是否符合预期
- 对于其他较模糊的名称，先使用 `search-poi` 获取目标坐标，再调用 `route`

## Distance

需要计算两个地点之间的直线距离时，使用 `distance`：

```bash
uvx amap-cli distance \
  --from 116.397,39.909 \
  --to 116.407,39.904
```

如果输入的是结构化地址或地标名称，也可以直接传：

```bash
uvx amap-cli distance \
  --from 北京南站 \
  --to 天安门
```

关键参数：

- `--from`：起点，支持结构化地址、地标性名胜景区/建筑物名称或 `经度,纬度`
- `--to`：终点，支持结构化地址、地标性名胜景区/建筑物名称或 `经度,纬度`
- `--from-name` / `--to-name`：坐标输入时可选，用于指定显示名称

关键约束：

- 当 `--from` 和 `--to` 都是坐标时，直接本地计算，不依赖 API Key
- 任一输入为结构化地址或地标性名胜景区、建筑物名称时，会先调用地理编码接口解析坐标
- 当输入为上述名称时，可从 `state.from.formattedAddress` / `state.to.formattedAddress` 判断地理编码是否符合预期
- 对于其他较模糊的名称，先使用 `search-poi` 获取目标坐标，再调用 `distance`
- 结果中的 `summary.distance` 单位为米

## Search-POI

按城市关键词搜索时：

```bash
uvx amap-cli search-poi \
  --keyword 星巴克 \
  --city 北京 \
  --pageSize 5
```

按坐标范围搜索时：

```bash
uvx amap-cli search-poi \
  --keyword 咖啡 \
  --center 120.155,30.274 \
  --radius 1000
```

关键参数：

- `--keyword`：必填，搜索关键词
- `--city`：城市关键词搜索时使用
- `--center`：周边搜索中心，格式为 `经度,纬度`
- `--radius`：周边搜索半径，仅在传入 `--center` 时使用
- `--pageSize`：每页数量
- `--pageIndex`：页码

关键约束：

- 传入 `--center` 时执行周边搜索
- 未传入 `--center` 时执行关键词搜索
- `--radius` 只有在传入 `--center` 时才应该使用

## 输出约定

所有命令都返回 JSON，按统一结构解析：

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

失败时读取 `error.code` 和 `error.message` 进行分支处理。

常见错误：

- `MISSING_CONFIG`：未配置 API Key，先执行 `config set`
- `INVALID_ARGUMENT`：参数不合法，检查必填项、坐标格式和命令参数组合
- `API_REQUEST_ERROR`：请求失败或超时，可重试并检查网络
- `API_RESPONSE_ERROR`：高德 API 返回业务错误，检查输入地点、城市或搜索参数
