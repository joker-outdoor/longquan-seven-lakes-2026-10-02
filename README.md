# 龙泉七湖连穿

[打开路线可视化](https://joker-outdoor.github.io/longquan-seven-lakes-2026-10-02/)

参照 [贡嘎100 三线赛道](https://github.com/joker-outdoor/gongga100-2026) 的深色 3D 地形呈现，为龙泉七湖连穿制作独立路线页面。

- 3D 卫星地形：拖动旋转、滚轮缩放、右键平移，支持全景 / 俯视 / 自动旋转、高度夸张与地形遮挡段。
- 七湖顺序：飞龙湖 → 百工堰 → 毛家口 → 罗家湾 → 山门寺 → 猫猫沟 → 玉带湖（李家沟水库）。点击标签或侧栏聚焦；名称与顺序由 Joker 提供。
- 海拔剖面：鼠标悬停、触屏滑动或方向键定位，地图白点同步到对应轨迹点。
- 手机布局、WebGL 不可用时的卫星俯视图、可下载的精简 GPX。

页面制作日期：**2026-10-02**。用户提供的原始 GPX 记录日期：**2025-11-02**，不是本次活动记录。

## 数据口径

1698 个轨迹点，球面距离测算 **18.554 km**；原文件扩展字段记录 **18.803 km**。剖面海拔范围 **443.57–735.23 m**。累计爬升 **1015.24 m**、下降 **1031.76 m**、记录用时 **7h17m** 沿用原文件扩展字段，不将逐点海拔噪声累加为正式爬升。

湖泊位置通过卫星影像与路线顺序作概略对照，再吸附到最近轨迹点；并非测绘湖心或核验过的精确入口。标签、剖面和侧栏的里程表示邻近轨迹点的累计距离。GPX 本身未提供命名路点。3D 路线贴合 DEM，剖面保留原轨迹海拔，两者可能存在差异。地形高度默认夸张 3 倍，可调回 1 倍。

公开 GPX 仅包含轨迹名、坐标与海拔；未上传原文件中的作者、账号 ID、头像 ID、照片 ID 或逐点时间。

## 本地预览与验证

无需构建；全部运行依赖、卫星图和地形网格均已存储在仓库中，浏览器不调用地图 API，也不需要 API key。

```sh
python3 -m http.server 8080
```

打开 `http://localhost:8080`；兼容俯视版可加 `?view=2d`。ES modules / fetch 需要 HTTP 服务，不支持直接以 `file://` 打开。

```sh
node --check app.js
python3 scripts/check_data.py
```

重新生成数据需 Python 3 与 Pillow，输入为用户原始 GPX（含扩展统计），不是下载用的精简 GPX：

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build_data.py /path/to/original.gpx --output data
```

`build_data.py` 专用于本条路线；七湖位置是与本条轨迹及固定卫星裁切对应的人工概略定位，不是自动识别其它路线的算法。

## 来源与许可

- 轨迹：用户提供的 `2025-11-02龙泉七湖连穿.gpx`。
- 卫星影像：[Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer)，© Esri, Maxar, Earthstar Geographics, and the GIS User Community。使用缩放级别 14 的本区域裁切影像；影像版权归提供者，不授予再许可。
- 地形：[Mapzen Terrain Tiles / Tilezen](https://github.com/tilezen/joerd)，SRTM 等公开数据，Terrarium 编码；原始数据源署名与许可见 [Tilezen attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)。页面采用 WGS84 坐标、Web Mercator 图像投影及局部地面尺度。
- 渲染：[Three.js 0.160.0](https://github.com/mrdoob/three.js/tree/r160)，MIT，完整许可证在 `vendor/LICENSE`。`vendor/` 保留官方文件原文。
