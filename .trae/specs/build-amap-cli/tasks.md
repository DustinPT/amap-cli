# Tasks

- [x] Task 1: 搭建基于 `uv` 的 Python CLI 项目骨架
  - [x] SubTask 1.1: 初始化 `pyproject.toml`、源码目录与 CLI 入口
  - [x] SubTask 1.2: 配置本地可安装的命令名与依赖管理方式
  - [x] SubTask 1.3: 确认安装后可通过帮助命令看到基础用法

- [x] Task 2: 实现高德 API 配置管理
  - [x] SubTask 2.1: 设计配置文件结构与操作系统路径解析策略
  - [x] SubTask 2.2: 实现配置写入、读取与缺失校验
  - [x] SubTask 2.3: 提供命令行配置入口，并输出可读结果

- [x] Task 3: 实现统一请求与输出基础能力
  - [x] SubTask 3.1: 封装高德 API 请求客户端与公共错误处理
  - [x] SubTask 3.2: 实现统一的 JSON 输出结构
  - [x] SubTask 3.3: 处理坐标、地名等公共参数逻辑

- [x] Task 4: 实现路径规划命令
  - [x] SubTask 4.1: 按官方 CLI 风格定义 `route` 参数接口
  - [x] SubTask 4.2: 对接高德路径规划相关 API
  - [x] SubTask 4.3: 输出包含摘要与步骤信息的结果结构

- [x] Task 5: 实现 POI 搜索命令
  - [x] SubTask 5.1: 按官方 CLI 风格定义 `search-poi` 参数接口
  - [x] SubTask 5.2: 对接高德 POI 搜索相关 API
  - [x] SubTask 5.3: 输出包含 POI 列表与分页信息的结果结构

- [x] Task 6: 编写 Agent 配套使用文档
  - [x] SubTask 6.1: 编写 skill 文档中的安装与配置说明
  - [x] SubTask 6.2: 编写路径规划与 POI 搜索的调用示例
  - [x] SubTask 6.3: 补充统一输出格式与常见错误说明

- [x] Task 7: 完成命令行手动验证
  - [x] SubTask 7.1: 验证本地安装与帮助命令
  - [x] SubTask 7.2: 验证配置写入与自动读取
  - [x] SubTask 7.3: 验证路径规划命令的典型输入
  - [x] SubTask 7.4: 验证 POI 搜索命令的典型输入

## Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1 and Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 3
- Task 6 depends on Task 4 and Task 5
- Task 7 depends on Task 2, Task 4, Task 5, and Task 6
