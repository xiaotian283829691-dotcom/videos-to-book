# videos-to-book

> 把视频课程/访谈/讲座 **变成可读的书**。yt-dlp 抓字幕 + AI 重排为结构化 markdown + 多出口适配器（本地/Obsidian/飞书/Notion）。

## 这是什么 · Why this exists

视频学习有三个老问题：
1. **跳着看找不到重点**——想复习某个知识点要反复拉进度条
2. **做笔记太累**——边听边记容易漏，记完没上下文
3. **回头复习全忘**——视频没有可检索的文本

市面上已有的工具要么只下载（yt-dlp），要么只做摘要（Eightify/Glarity，SaaS 且只出精简版），**"保留讲师完整原话 + 按语义结构化重排 + 书籍式可读"这个定位目前没有成熟开源方案**。

本项目填这个坑。核心假设：**视频字幕本身就是好内容的原料，只需要一个懂"删口语+补标点+归纳结构+保留个性"的编辑**。AI 是这个编辑。

## 它能干什么 · Scope

**支持**：
- 🎓 **单门课程** → 书（如 B 站某编剧课 91 集 → 可读长书）
- 🌏 **英文视频** → 中文书（如 Lex Fridman 访谈 → 中文长文）
- 📊 **创作者频道** → 周报（如 10 个 YouTube AI 博主 → 每周情报摘要）

**支持的站点**（继承自 yt-dlp）：B 站 / YouTube / Vimeo / TikTok / Twitch / 1700+ 站点

**不做的事**：
- ❌ 不做视频摘要（已有一堆工具）
- ❌ 不下载视频文件本身（只抓字幕+元数据）
- ❌ 不搞反爬黑魔法（站点不支持就不支持）

## 快速开始 · Quickstart

### 前置依赖
```bash
# 1. 安装 yt-dlp
pip install yt-dlp

# 2. 浏览器登录 B 站/YouTube（cookie 会自动从浏览器读）

# 3. clone 本项目
git clone https://github.com/YOUR_USERNAME/videos-to-book.git
cd videos-to-book
pip install -r requirements.txt

# 4. 复制配置文件
cp config.example.yaml config.yaml
# 编辑 config.yaml 按注释改你需要的部分
```

### 三种典型用法

#### 场景 1：B 站课程转书（A1）
```bash
# 抓 91 集字幕到本地
python core/fetch.py --url "https://www.bilibili.com/video/BV1eE411F73t" --out ./tmp/charlie

# 用 Claude Code 让 AI 重排（读 SKILL.md 交互式执行）
claude
> 帮我把 ./tmp/charlie/ 里的 srt 文件按 prompts/zh-lecture-to-book.md 的规则重排成书籍式 markdown，输出到 ./output/
```

#### 场景 2：英文访谈转中文书（A2）
```bash
python core/fetch.py --url "https://www.youtube.com/watch?v=XYZ" --out ./tmp/lex
claude
> 按 prompts/en-to-zh-book.md 重排，中英双栏输出
```

#### 场景 3：创作者情报周报（B4）
```bash
# 批量抓最近一周的新视频字幕
python core/fetch.py --channels config/channels.yaml --since 7d --out ./tmp/weekly

# 生成周报
claude
> 按 prompts/creator-weekly.md 生成本周 AI 创业者动态周报，走 lark adapter 发到飞书群
```

## 核心设计 · Architecture

```
          字幕抓取              AI 重排                 出口
        ┌─────────┐          ┌─────────┐          ┌──────────┐
  URL ─▶│ yt-dlp  │──srt──▶ │ 重排引擎 │──md──▶ │ 多出口选  │
        └─────────┘          └─────────┘          │          │
                                  ↑                │  local   │
                             prompt 模板库         │  obsidian│
                                                   │  飞书    │
                                                   │  notion  │
                                                   └──────────┘
```

- **core/**：抓取 + 清洗（纯 Python，无 AI 依赖）
- **prompts/**：AI 重排的 prompt 模板（核心 know-how）
- **adapters/**：不同出口（可插拔，按 config 启用）
- **skills/**：Claude Code skill 格式，直接交互式调用

## 目录结构 · Layout

```
videos-to-book/
├── core/
│   ├── fetch.py              # yt-dlp 封装（抓字幕/元数据）
│   ├── srt2md.py             # srt → 粗 markdown
│   └── restructure.py        # 调用 AI 重排（可选，直接用 SKILL 更简单）
├── prompts/
│   ├── zh-lecture-to-book.md # 中文讲课 → 书（核心，已在 91 集实战）
│   ├── en-to-zh-book.md      # 英文 → 中文书
│   └── creator-weekly.md     # 创作者周报
├── adapters/
│   ├── local.py              # 默认出口：本地 md 文件 ✅
│   ├── obsidian.py           # 写入 Obsidian vault ✅
│   ├── lark.py               # 创建飞书云文档 + 可选群通知 ✅
│   └── notion.py             # 写入 Notion（TODO）
├── skills/
│   └── videos-to-book/
│       └── SKILL.md          # Claude Code skill 入口
├── examples/
│   └── P03-查理编剧课-劝学.md  # 中文讲课样板（来自 91 集实战）
├── config.example.yaml
├── requirements.txt
└── README.md
```

## 样板产出 · Samples

看 `examples/` 里的样板，对比原始字幕和重排后的可读性差异。核心目标不是"短"，是"好读"。

**重排前**（AI 字幕节选）：
```
你知道这个学学习这件事
就是我跟你们说啊
其实没那么简单你想想看对吧
```

**重排后**（样板）：
```markdown
### 学习没那么简单

学习这件事其实没那么简单。你想想看。
```

## 使用我们自己的样板 prompt？

`prompts/zh-lecture-to-book.md` 是我们跑了 91 集《查理的编剧课》B 站课程打磨出来的。**你可以直接用，也可以改成你领域的风格**（技术分享、商业访谈、学术讲座格式都不一样）。

## 贡献 · Contributing

**欢迎**：
- 新 adapter（Discord/Slack/Teams/etc）
- 新 prompt 风格（技术类、学术类、商业类）
- 新站点的 cookie 处理优化

**暂不接**：反爬绕过、代理池、SaaS 化——这些要么脏、要么超出工具定位。

## 作者 · Author

[袁啸天 · OnceLab](https://oncelab.cn) · 做 AI 时代营销工具的产品经理。
本项目是 [OnceLab](https://oncelab.cn) 基础设施开源的一部分。

## License

MIT
