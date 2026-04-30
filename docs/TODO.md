# TODO

按优先级排列。完成后划掉、移到底部"Done"。

## P0 ｜ 平台适配（按你的使用频率）

- [ ] 掘金（juejin.cn）适配器
  - 选择器探查：`#article-root` / `h1.article-title` / 作者卡片 / 标签
  - 代码块：`<pre><code class="hljs language-xxx">`
  - fixture + 测试
- [ ] CSDN（blog.csdn.net）适配器
  - 选择器探查：`#content_views` / `.title-article` / 作者 / 标签
  - 去除官方水印模块、推广卡片、文末打赏
  - fixture + 测试
- [ ] 知乎专栏（zhuanlan.zhihu.com）适配器
  - 选择器：`.Post-RichTextContainer` / `.Post-Title` / 作者
  - `<figure>` + `<figcaption>` 还原成 `![alt](src)`
  - 跳过付费墙提示节点
  - fixture + 测试
- [ ] Medium 适配器
  - 选择器：`article` / `h1` / `[data-testid='authorName']`
  - 付费墙文章直接报错退出（不绕过）
  - fixture + 测试

## P1 ｜ 转换质量

- [ ] Cleaner 阶段（在 Extractor 之后、Converter 之前）
  - 裁掉博客园文末"本文版权归作者和博客园共有..."固定话术（关键字+位置双约束）
  - 通用：删除 `<script>` `<style>` `<iframe>` 残留
  - 通用：合并连续空行
- [ ] 表格转换打磨：markdownify 默认输出对部分 VuePress 主题不友好（首列是空的、对齐符号缺失），需要自定义 `convert_table`
- [ ] 数学公式：识别 `<span class="math">` / KaTeX 节点，转成 `$...$` / `$$...$$`
- [ ] 代码块语言识别兜底：`hljs language-*` / `prettyprint lang-*` / `highlight-source-*`

## P1 ｜ 图片

- [ ] 图片宽度上限（PIL/Pillow，默认 1600px）+ 可选无损压缩
- [ ] 失败重试：单张图 403 时换 UA / 去掉 Referer 重试一次
- [ ] 已存在的同名文件不要覆盖（带 `--force` 才覆盖）
- [ ] svg / webp 保留原扩展名（已实现，加测试）

## P1 ｜ 工程

- [ ] 配置文件 `~/.html2md/config.toml` 加载真实生效（已实现框架，缺端到端验证）
- [ ] CLI 增加 `--dry-run`：只打印结果不落盘
- [ ] CLI 增加 `--print-only`：直接 stdout 输出 markdown
- [ ] 自动从 `<link rel="canonical">` 解析最终 URL（避免短链/带参数的污染）
- [ ] 异常处理：网络失败、403 防盗链、解析失败的友好错误消息

## P2 ｜ 体验

- [ ] rich 进度条（图片下载、长文章转换）
- [ ] `html2md batch urls.txt` 批量转换
- [ ] 与 VuePress 博客直接联动：`--blog-root <path>` 自动放到 `docs/posts/`、自动从 git 仓库读默认作者
- [ ] 转完后可选自动 `git add` 到博客仓库
- [ ] 浏览器书签 / 一键转换页（远期）

## P2 ｜ 平台扩展

- [ ] 微信公众号（mp.weixin.qq.com）—— 图片防盗链需要 Referer，前端有水印 svg 要清理
- [ ] 简书 / SegmentFault / 思否 / V2EX
- [ ] Substack / dev.to / Hashnode
- [ ] GitHub README（直接拿 raw markdown）

## P3 ｜ 远期

- [ ] Playwright 后端（仅在 generic 失败时启用，处理 SPA）
- [ ] 自动识别"转载的转载"，记录到 `source_url` 字段（当前按用户决定不做）

---

## Done

- [x] 项目骨架：fetcher / converter / images / frontmatter / pipeline / cli
- [x] 通用 readability extractor
- [x] 博客园 extractor（含摘要单独提取到 front matter `description`）
- [x] VuePress 2 front matter（无引号日期标量）
- [x] 离线 fixture 测试框架（tests/fixtures/*.html）
- [x] 中文标题 → 拼音 slug
