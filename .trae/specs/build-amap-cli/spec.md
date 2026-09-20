# 纯命令行高德地图 CLI Spec

## Why

高德官方 CLI 依赖 GUI 容器，不适合 AI Agent 在纯终端或无界面环境下稳定调用。我们需要一个基于高德地图 API 的纯命令行工具，支持本地安装、命令行配置密钥、路径规划和 POI 搜索，并提供配套 skill 文档供 Agent 使用。

## What Changes

- 新建一个使用 Python 开发、可作为本地 CLI 安装的高德地图工具，依赖与项目管理使用 `uv`
- 新增配置命令，支持通过命令行写入并读取高德 API 所需配置，按当前操作系统的用户配置目录规范保存
- 新增 `route` 子命令，接口设计尽量对齐官方 CLI 的路径规划参数风格，但不支持 `--json` 输入
- 新增 `search-poi` 子命令，接口设计尽量对齐官方 CLI 的 POI 搜索参数风格，但不支持 `--json` 输入
- 统一所有命令的机器可读输出格式，便于 Agent 解析和处理错误
- 提供配套的 skill 文档，说明 Agent 如何安装、配置并调用该 CLI

## Impact

- Affected specs: CLI 安装能力、配置管理、路径规划、POI 搜索、Agent 集成
- Affected code: `pyproject.toml`、`src/amap_cli/` 包结构、CLI 入口、配置读写模块、高德 API 客户端、skill 文档

## ADDED Requirements

### Requirement: 本地可安装的纯命令行工具

系统 SHALL 提供一个可在本地安装和调用的纯命令行工具，安装后可直接通过统一命令名执行，不依赖 GUI 进程或浏览器容器。

#### Scenario: 安装后可直接调用

- **WHEN** 用户在本地通过 `uv` 完成项目安装
- **THEN** 终端中可以直接调用 CLI 命令查看帮助信息
- **AND** 工具在执行时不要求额外启动 GUI 服务

### Requirement: 按操作系统规范保存高德 API 配置

系统 SHALL 提供命令行配置能力，用于保存高德 API 配置项，并按当前操作系统的用户配置目录规范持久化保存，在后续请求中自动读取。

#### Scenario: 保存并复用配置

- **WHEN** 用户通过 CLI 写入高德 API Key 与相关配置项
- **THEN** 工具将配置保存到当前操作系统推荐的用户配置目录
- **AND** 后续执行路径规划或 POI 搜索命令时会自动读取该配置

#### Scenario: 缺少配置时返回可读错误

- **WHEN** 用户尚未完成配置就直接调用高德 API 相关命令
- **THEN** CLI 返回明确的错误信息
- **AND** 错误信息提示用户先执行配置命令

### Requirement: 路径规划命令接口对齐官方 CLI 风格

系统 SHALL 提供 `route` 子命令，并尽量复用官方 CLI 的核心参数设计，包括 `--from`、`--from-name`、`--to`、`--to-name`、`--type`、`--waypoints`、`--policy`、`--strategy`、`--city`，但不支持 `--json` 输入。

#### Scenario: 使用地名进行路径规划

- **WHEN** 用户调用 `route --from 北京南站 --to 天安门 --type driving`
- **THEN** CLI 调用高德地图 API 完成路径规划
- **AND** 返回包含起终点、出行方式、距离、预计时间和步骤摘要的 JSON 结果

#### Scenario: 使用坐标进行路径规划

- **WHEN** 用户调用 `route --from 116.397,39.909 --to 116.407,39.904 --type walking`
- **THEN** CLI 可以正确识别坐标输入并完成路径规划

### Requirement: POI 搜索命令接口对齐官方 CLI 风格

系统 SHALL 提供 `search-poi` 子命令，并尽量复用官方 CLI 的核心参数设计，包括 `--keyword`、`--city`、`--center`、`--radius`、`--pageSize`、`--pageIndex`，但不支持 `--json` 输入。

#### Scenario: 按城市关键词搜索 POI

- **WHEN** 用户调用 `search-poi --keyword 星巴克 --city 北京 --pageSize 1`
- **THEN** CLI 调用高德地图 API 执行搜索
- **AND** 返回包含查询状态、POI 列表、分页信息的 JSON 结果

#### Scenario: 按周边范围搜索 POI

- **WHEN** 用户调用 `search-poi --keyword 咖啡 --center 120.155,30.274 --radius 1000`
- **THEN** CLI 可以基于坐标与半径执行周边搜索

### Requirement: 面向 Agent 的稳定 JSON 输出

系统 SHALL 为成功与失败结果提供稳定、可机读的 JSON 输出格式，至少包含 `success`、`data`、`error` 字段，便于 Agent 可靠解析。

#### Scenario: 请求成功时返回统一结构

- **WHEN** 任一业务命令执行成功
- **THEN** CLI 返回 `success=true`
- **AND** 业务结果位于 `data` 字段中
- **AND** `error` 为 `null`

#### Scenario: 请求失败时返回统一结构

- **WHEN** 参数校验失败、配置缺失或高德 API 返回异常
- **THEN** CLI 返回 `success=false`
- **AND** `error` 字段中包含明确错误原因

### Requirement: 提供 Agent 使用说明

系统 SHALL 提供配套的 skill 文档，说明 CLI 的安装方式、配置方式、命令用法、输出约定与常见错误处理方式，便于 AI Agent 直接集成。

#### Scenario: Agent 按文档完成调用

- **WHEN** Agent 按 skill 文档执行安装、配置与命令调用
- **THEN** Agent 可以在无需 GUI 的前提下完成路径规划与 POI 搜索

## MODIFIED Requirements

无

## REMOVED Requirements

无
