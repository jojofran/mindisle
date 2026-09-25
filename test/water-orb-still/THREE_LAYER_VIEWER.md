# 水球 2.5D 静止图层预览

这是独立的静止状态预览，不修改主 App、Unity 或 WebGL 产品入口。

在项目根目录启动静态文件服务后打开：

```bash
python3 -m http.server 4173
```

然后访问 `http://127.0.0.1:4173/test/water-orb-still/three-layer-viewer.html`。

预览按 `2p5d-composite-v1/composite_manifest.json` 的顺序加载正式 v1 的 12 个 RGBA 图层，并使用 v1 的画布和球体参数建立固定正面视图及圆形命中区域。浏览器控制台可读取 `window.waterOrbViewer.inspect()`；点击球体会派发 `water-orb-hit` 事件。

当前范围只有 `still`：没有 moving、计时器、音乐、状态机或 Unity 接入。
