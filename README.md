# html2md

将网页文章一键转成 Markdown 的转载工具，专为 [bupt.online](https://www.bupt.online) （VuePress 2）设计。

## 特性

- **CLI 优先**：`html2md <url>` 一条命令拿到 `.md` 文件
- **多平台适配**：针对知乎、CSDN、掘金、博客园、Medium 做了正文提取优化，其它站点回退到 readability 通用算法
- **图片本地化**：默认把远程图片下载到 `assets/` 目录，写相对路径到 Markdown，彻底解决防盗链问题
- **VuePress 2 front matter**：自动生成 `title` / `date` / `category` / `tag` / `author` / `original_url`
- **代码块语言识别**：保留原文的语言高亮标记
- **可配置**：通过 `~/.html2md/config.toml` 自定义输出目录、图片策略、UA 等

## 安装

```bash
# 需要 Python 3.11+
uv sync          # 或 pip install -e .
```

## 用法

```bash
# 最简
html2md https://zhuanlan.zhihu.com/p/123456789

# 指定输出目录
html2md https://juejin.cn/post/xxx -o ./posts

# 自定义文件名（默认从标题生成 slug）
html2md https://xxx -o ./posts -n my-article

# 不下载图片，保留原始 URL
html2md https://xxx --no-download-images

# 只输出正文，不要 front matter
html2md https://xxx --no-front-matter

# 指定分类和标签
html2md https://xxx -c 技术 -t python -t 爬虫
```

## 输出结构

```
posts/
├── my-article.md
└── assets/
    └── my-article/
        ├── 01.png
        └── 02.jpg
```

Markdown 顶部 front matter 示例：

```yaml
---
title: 文章标题
date: 2026-04-30
category:
  - 转载
tag:
  - python
author: 原作者
original_url: https://zhuanlan.zhihu.com/p/123456789
---
```

## 配置文件

`~/.html2md/config.toml`（可选）：

```toml
output_dir = "F:/blog/src/posts"
download_images = true
image_dir = "assets"            # 相对于 output_dir
default_category = "转载"
user_agent = "Mozilla/5.0 ..."
timeout = 30
```

## 平台支持情况

| 平台     | 正文提取         | 图片 | 代码块 | 备注                            |
| -------- | ---------------- | ---- | ------ | ------------------------------- |
| 知乎专栏 | ✅               | ✅   | ✅     | 自动展开 figure、跳过付费墙提示 |
| CSDN     | ✅               | ✅   | ✅     | 去除官方水印、推广模块          |
| 掘金     | ✅               | ✅   | ✅     |                                 |
| 博客园   | ✅               | ✅   | ✅     |                                 |
| Medium   | ✅               | ✅   | ✅     | 需登录的付费墙文章无法抓取      |
| 其它     | ⚠️ readability | ✅   | ✅     | 通用提取，效果视站点而定        |

## 不做的事

- 不绕过付费墙、不模拟登录
- 不抓取 JS 动态渲染内容（如有需要后续可加 Playwright 后端）
- 不做版权判断，转载请自行确认授权并保留原作者信息

## License

MPL 2.0
