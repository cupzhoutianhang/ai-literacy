# 课程导入视频

- 展示标题：从现在看过去：AI 简史
- 原标题：震惊瘫坐！Opus 5.5生成-从现在看过去-AI简史
- 来源：https://www.bilibili.com/video/BV1H8av6HEYs/
- UP 主：[铼夏LAYccc](https://space.bilibili.com/60729919)
- 添加日期：2026-10-03
- 时长：6 分 29 秒

`ai-history-BV1H8av6HEYs-1080p.mp4` 是用于网页播放的压缩版本，保留完整画面、声音、原有字幕和水印。编码为 H.264 / AAC，1920 × 1080，30 fps；启用 MP4 faststart，并通过页面的 `preload="none"` 避免打开主页即下载整段视频。

`ai-history-poster.jpg` 截取自原视频。视频及封面均为外部来源素材，不属于本站原创课件；请保留原作者署名和来源链接。

网页版本生成参数：

```sh
ffmpeg -y -hide_banner -i ORIGINAL.mp4 -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -crf 23 -preset medium -maxrate 1600k -bufsize 3200k \
  -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart \
  ai-history-BV1H8av6HEYs-1080p.mp4
```
