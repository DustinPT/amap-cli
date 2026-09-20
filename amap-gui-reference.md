# 高德开放平台 CLI 参考手册
> 最后更新时间: 2026年04月01日

我们提供一系列标准化的命令行指令，使 AI Agent 能够精确控制地图状态、搜索兴趣点 (POI) 和进行路线规划

## 前置条件
### 安装 amap-gui
```bash
npm install -g @amap-lbs/amap-gui
```

### 获取高德地图 API Key
成为开发者并创建 key
为了正常调用 API ，请先注册成为高德开放平台开发者，并申请 web 平台（JS API）的 key 和安全密钥，点击 具体操作。

## 使用方法
### 设置环境变量
```bash
# macOS / Linux:
export AMAP_KEY=your_amap_web_js_key
export AMAP_SECURITY_KEY=your_amap_security_key

# Windows (PowerShell):
# $env:AMAP_KEY="your_amap_web_js_key"
# $env:AMAP_SECURITY_KEY="your_amap_security_key"
```

### 打开地图
```bash
amap-gui start
```

## 核心命令
使用方法 help
```bash
# amap-gui --help
Usage:
  amap-gui status                           Check if GUI is running
  amap-gui start                            Start GUI (blocks until ready)
  amap-gui stop                             Stop GUI
  amap-gui getLastEvent                     Get last user interaction event

  amap-gui mapState [options]               Map view control
    --json '<JSON>'                           Full JSON input (takes priority)
    --action <get|set>                        Action (default: get)
    --center <lng,lat>                        Center coordinate (lng,lat only)
    --zoom <3-20>                             Zoom level
    --rotation <0-360>                        Rotation angle
    --pitch <0-83>                            Pitch angle
    --style <name>                            Map style (normal|dark|light|...)

  amap-gui route [options]                  Route planning
    --json '<JSON>'                           Full JSON input (takes priority)
    --from <place|lng,lat>                    Origin (place name or coordinate)
    --from-name <name>                        Origin display name
    --to <place|lng,lat>                      Destination (place name or coordinate)
    --to-name <name>                          Destination display name
    --type <mode>                             driving|walking|riding|transit
    --waypoints <p1,p2,...>                   Comma-separated waypoints (driving only)
    --policy <policy>                         Driving: fastest|least_fee|shortest|...
    --strategy <strategy>                     Transit: fastest|least_cost|least_walk|...
    --city <city>                             City name (required for transit)

  amap-gui searchPOI [options]              POI search
    --json '<JSON>'                           Full JSON input (takes priority)
    --keyword <text>                          Search keyword
    --city <city>                             City name
    --center <lng,lat>                        Nearby search center (lng,lat only)
    --radius <meters>                         Search radius (default: 3000)
    --pageSize <n>                            Results per page (default: 10)
    --pageIndex <n>                           Page number (default: 1)
```

> Note: --json takes priority when used with other options.

### Examples
```bash
amap-gui mapState --action set --center 116.397,39.909 --zoom 15 --style dark
amap-gui route --from 北京南站 --to 天安门 --type driving
amap-gui searchPOI --keyword 星巴克 --city 北京
amap-gui searchPOI --keyword 咖啡 --center 120.15,30.28 --radius 1000
```

## 地图生命周期
```bash
# amap-gui status                           获取地图容器状态
# amap-gui start                            启动地图容器
# amap-gui stop                             关闭地图容器
```

## 地图状态控制 mapState
```bash
# amap-gui mapState [options]                  地图状态控制
#    --action <get|set>                        操作类型，默认 get  'get'|'set'
#    --center <lng,lat>                        中心点坐标 [number,number]
#    --zoom <3-20>                             缩放级别 number
#    --rotation <0-360>                        旋转角度 number
#    --pitch <0-83>                            俯仰角度 number
#    --style <name>                            地图样式 (normal|dark|light|whitesmoke|fresh|grey|graffiti|macaron|blue|darkblue|wine)
```

### example
```bash
amap-gui mapState --action set --center 116.397,39.909 --zoom 15 --style dark
```

#### 返回结果
```json
{
 "success": true,
 "data": {
   "center": [116.397428, 39.90923],
   "zoom": 15,
   "rotation": 0,
   "pitch": 0,
   "style": "normal",
   "bounds": {
     "southWest": [116.384258, 39.902195],
     "northEast": [116.410598, 39.916265]
   }
 },
 "error": null
}
```

## 路径规划 route
| 参数 | 类型 | 是否必传 | 描述 |
| ---- | ---- | ---- | ---- |
| --json '&lt;JSON&gt;' | string | No | 完整 JSON 输入（优先级最高） |
| --from &lt;地名\|lng,lat&gt; | 地名\|lng,lat | Yes | 起点（地名或坐标） |
| --from-name &lt;name&gt; | string | No | 起点显示名称（配合坐标使用） |
| --to &lt;地名\|lng,lat&gt; | 地名\|lng,lat | Yes | 终点（地名或坐标） |
| --to-name &lt;name&gt; | string | No | 终点显示名称（配合坐标使用） |
| --type &lt;mode&gt; | driving\|walking\|riding\|transit | Yes | 出行方式 |
| --waypoints &lt;p1+p2+..&gt; | string | No | 加号分隔的途经点（仅 driving，最多 16 个） |
| --policy &lt;policy&gt; | fastest\|least_fee\|shortest\|no_highway\|avoid_jam | No | 驾车策略 |
| --strategy &lt;strategy&gt; | fastest\|least_cost\|least_walk\|most_comfort\|no_subway | No | 公交策略 |
| --city &lt;city&gt; | string | transit 必填 | 城市名（公交模式必须指定） |

### example
```bash
amap-gui route --from 中关村  --to 北京大学东门 --type driving
```

#### 返回结果
```json
{
  "success": true,
  "data": {
    "state": {
      "from": {
        "name": "中关村",
        "position": [
          116.321669,
          39.985266
        ]
      },
      "to": {
        "name": "北京大学东门",
        "position": [
          116.315811,
          39.992127
        ]
      },
      "waypoints": [],
      "type": "driving"
    },
    "summary": {
      "distance": 2090,
      "time": 391,
      "steps": [
        {
          "instruction": "沿北四环西路辅路向东行驶474米左转调头",
          "road": "北四环西路辅路",
          "distance": 474,
          "time": 119,
          "action": "左转调头"
        },
        {
          "instruction": "沿北四环西路辅路向西行驶915米右转",
          "road": "北四环西路辅路",
          "distance": 915,
          "time": 136,
          "action": "右转"
        },
        {
          "instruction": "沿中关村北大街向北行驶701米到达目的地",
          "road": "中关村北大街",
          "distance": 701,
          "time": 136,
          "action": ""
        }
      ],
      "tolls": 0
    }
  },
  "error": null
}
```

## POI 搜索 searchPOI
| 参数 | 类型 | 是否必传 | 描述 |
| ---- | ---- | ---- | ---- |
| --json '&lt;JSON&gt;' | string | No | 完整 JSON 输入（优先级最高） |
| --keyword &lt;text&gt; | string | Yes | 搜索关键词 |
| --city &lt;city&gt; | string | No | 搜索城市 |
| --center &lt;lng,lat&gt; | lng,lat | No | 周边搜索中心坐标（仅支持坐标格式） |
| --radius &lt;meters&gt; | number | No | 搜索半径（米），默认 3000 |
| --pageSize &lt;n&gt; | number | No | 每页数量，默认 10 |
| --pageIndex &lt;n&gt; | number | No | 页码，默认 1 |

### example
```bash
amap-gui searchPOI --keyword 星巴克 --city 北京 --pageSize 1
```

#### 返回结果
```json
{
  "success": true,
  "data": {
    "state": {
      "keyword": "星巴克",
      "pageSize": 1,
      "pageIndex": 1,
      "extensions": "all",
      "resultCount": 600,
      "city": "北京"
    },
    "pois": [
      {
        "id": "B0FFJGCM9X",
        "name": "星巴克(京汇大厦店)",
        "type": "餐饮服务;咖啡厅;星巴克咖啡",
        "location": [
          116.462991,
          39.906998
        ],
        "address": "北京城区建国路乙118号京汇大厦一层1-105号单元",
        "distance": null,
        "tel": "010-65685868",
        "pname": "北京市",
        "cityname": "北京市",
        "adname": "朝阳区",
        "photo": "https://store.is.autonavi.com/showpic/6e458084419d9144d0b5f1020d7958f0"
      }
    ],
    "total": 600,
    "pageIndex": 1,
    "pageSize": 1
  },
  "error": null
}
```

## 获取用户最后一次地图交互事件 getLastEvent
```bash
amap-gui getLastEvent
```

### example1
```json
{
   "success": true,
   "data": {
     "lastEvent": {
       "hasEvent": true,
       "type": "map_click",
       "position": [
         116.462574,
         39.907429
       ]
     }
   },
   "error": null
}
```

### example2
```json
{
   "success": true,
   "data": {
     "lastEvent": {
       "hasEvent": true,
       "type": "poi_click",
       "title": "星巴克(京汇大厦店)",
       "address": "北京城区建国路乙118号京汇大厦一层1-105号单元",
       "position": [
         116.462991,
         39.906998
       ]
     }
   },
   "error": null
}
```

无需参数，直接调用。返回用户在 GUI 上最后一次交互的事件信息。

### 事件类型
| type | 触发方式 | 返回字段 |
| ---- | ---- | ---- |
| map_click | 点击地图空白处 | position |
| poi_click | 点击地图上的 POI 标记 | title + address + position |
| poi_select | 在左侧搜索结果列表中选中 | title + address + position |

### 返回字段说明
| 字段 | 说明 |
| ---- | ---- |
| lastEvent.hasEvent | 是否有事件记录（false 表示用户尚未操作） |
| lastEvent.type | 事件类型（见上表） |
| lastEvent.title | POI 名称（poi_click / poi_select 时有值） |
| lastEvent.address | POI 地址（poi_click / poi_select 时有值） |
| lastEvent.position | 坐标 [lng, lat]，所有事件类型均有值 |

## 场景示例
### 场景 1：查看某地的地图
```bash
amap-gui status
# → not_running → 先启动
amap-gui start
# → mapReady: true

amap-gui mapState --action set --center 121.491,31.233 --zoom 15 --pitch 45 --style dark
```

### 场景 2：A 到 B 的规划
```bash
amap-gui route --from 北京南站 --to 首都机场T3 --type driving
```

### 场景 3：查找附近的美食
```bash
amap-gui searchPOI --keyword 咖啡 --center 120.155,30.274 --radius 1000
```

### 场景 4：连续操作：搜索后导航
```bash
amap-gui searchPOI --keyword 故宫博物院 --city 北京
# 从结果中取坐标
amap-gui route --from 王府井 --to 116.397029,39.917839 --to-name 故宫博物院 --type walking
```

### 场景 5：点选地图后导航
```bash
# 用户在地图上点选了目的地
amap-gui getLastEvent
# → position: [116.488778, 40.002995], title: "某餐厅"

# 直接用坐标规划路线
amap-gui route --from 北京站 --to 116.488778,40.002995 --to-name 某餐厅 --type driving
```

### 场景 6：完成后停止
```bash
amap-gui stop
```

---
你可以直接全选复制上面全部内容，粘贴到记事本，保存为 `amap-gui-cli.md`，编码选 UTF-8。

要不要我再帮你精简一版（去掉示例JSON，做成极简参考卡片）？