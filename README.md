# Subway Navigator 后端仓库

本项目旨在实现一个北京地铁线路查询系统，支持的功能有：

- 浏览北京地铁路线图；

- 查询从给定起始站到终点站的最优方案，支持最短时间、最少换乘次数两种模式；

- 增加自定义线路及相关站点；

- 删除原有线路及相关站点；

后端部分基于 Python Flask 框架开发，引入 pypinyin 库实现中文站名的升序排序。

**本项目已部署至阿里云函数计算，前端已部署至 Cloudflare Pages，可通过 https://subway-navigator.org 访问。**

### 本地部署

1. 安装 3.9 以上版本的 [Python](https://www.python.org/)；

2. 克隆该仓库到本地：

    ```
    git clone https://github.com/cheng1559/subway-navigator-backend.git && cd./subway-navigator-backend
    ```

3. 安装依赖项：

    ```
    pip3 install -r requirements.txt
    ```

4. 运行项目：

    启动本地后端（默认监听 `8080` 端口，可在根目录下的`main.py` 文件中更改）：

    ```
    python3 main.py
    ```

### 地铁信息

所有的地铁信息保存在根目录下的 `subway_data.json` 文件中，以下为其中一个例子：

```
{
    "name": "十一号线",
    "speed": 100,
    "stations": ["模式口", "金安桥", "北辛安", "新首钢"],
    "distances": [0, 1366, 850, 689],
    "loop": false
},
```

其中，`name` 为线路名称，`speed` 为线路最高时速 (km/h)，`stations` 为站台名称列表，相邻两站相互连接，`distances` 为每站与上一站之间的距离 (m)，`loop` 表示该线路是否为环线，即首尾两站之间是否互相连接。

要求：
- 若一条线路不为环线，规定 `distances` 的第一个元素，即第一站与上一站之间的距离必须为 `0`；
- `distances` 的每个元素只能为正整数（非环线第一个元素除外）；
- `stations` 中不能出现重复元素，即站名不能重复；
- `speed` 必须大于 `0`；

你可以在文件中修改或添加自定义线路，如：

```
{
    "name": "测试线路",
    "speed": 100,
    "stations": ["测试站1", "测试站2", "测试站3"],
    "distances": [100, 200, 300],
    "loop": true
},
```