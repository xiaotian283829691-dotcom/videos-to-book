---
name: videos-to-book
description: Turn video lectures, interviews, or channels into book-style markdown using yt-dlp + AI restructuring. Supports Chinese lecture→book, English→Chinese translation book, and creator weekly digest modes.
---

# videos-to-book

当用户想把**视频课程/访谈/频道内容变成可读的书/长文/周报**时，调用本 skill。

## 触发场景

- "帮我把这个 B 站合集做成书"
- "把 Lex Fridman 这期访谈转成中文长文"
- "每周跟踪这几个 YouTube AI 博主，出周报"
- 任何"视频 → 可读文本"的需求（不是做摘要，是保留全文 + 结构化）

## 三种模式

### 模式 1: 中文讲课转书（zh-lecture）
**输入**：中文讲师的视频课程/演讲（通常是 B 站）
**流程**：
1. 用 `core/fetch.py` 抓 AI 字幕
2. 用 `core/srt2md.py` 机械转 md
3. 按 `prompts/zh-lecture-to-book.md` 的规则 AI 重排
4. 按用户 config 写到 local / obsidian / lark

**参考样板**：`examples/P03-查理编剧课-劝学.md`

### 模式 2: 英文→中文书（en-to-zh）
**输入**：YouTube 英文访谈/播客
**流程**：
1. 抓 en 字幕
2. 按 `prompts/en-to-zh-book.md` 翻译+结构化
3. 默认输出中文精华版，用户明确要求时输出中英对照

### 模式 3: 创作者周报（creator-weekly）
**输入**：一批订阅频道的 URL 列表
**流程**：
1. 抓本周所有新视频的字幕
2. 按 `prompts/creator-weekly.md` 生成情报周报
3. 默认推送到飞书，也可写 obsidian

## 关键原则（从 91 集查理编剧课实战沉淀）

1. **保留讲者原话 100%**——不做摘要、不压缩、不美化
2. **删口语填充词 + 补标点 + 归纳结构**——三件事都做，让文档可读
3. **保留讲者个人故事/脏话/比喻**——这是风格命脉
4. **用讲者语气起小标题**——不要"第一节·鼓励学习"这种正式报告风
5. **金句用引用块凸显**

## 执行流程

### Step 1: 解析用户需求
从用户消息中提取：
- URL 或频道列表
- 输出语言（中文/中英对照）
- 输出目标（本地目录/Obsidian/飞书群）

### Step 2: 检查前置
- yt-dlp 已安装？`yt-dlp --version`
- config.yaml 存在？不存在用 config.example.yaml
- 浏览器 cookie 可用？（B 站/YouTube 都需要登录）

### Step 3: 执行抓取
```bash
python core/fetch.py --url <URL> --out ./tmp/<session>
```

### Step 4: 机械转 md
```bash
python core/srt2md.py --input ./tmp/<session> --out ./tmp/<session>-md
```

### Step 5: AI 重排（**这是本 skill 的核心**）
逐个读取 md 文件，按对应 prompt 重排：
- 中文讲课 → `prompts/zh-lecture-to-book.md`
- 英文视频 → `prompts/en-to-zh-book.md`
- 创作者周报 → `prompts/creator-weekly.md`

**重排时严格遵守 prompt 里的"必做/必不做"清单**。

### Step 6: 出口
按 config.yaml 的 output 配置，调用对应 adapter：
- `adapters/local.py` → 写本地
- `adapters/obsidian.py` → 写 Obsidian vault（如果用户配了）
- `adapters/lark.py` → 发飞书（如果用户配了）

## 常见问题

**Q: 91 集视频能一次跑完吗？**
A: 可以批量抓字幕（yt-dlp 一次跑完合集），但 AI 重排需要逐集进行（上下文不够），建议每批 5-10 集向用户汇报进度。

**Q: B 站 412 / YouTube 被封怎么办？**
A: 切海外代理节点 → 重试。cookie 过期 → 浏览器重新登录 → 重跑。

**Q: 没字幕的视频怎么办？**
A: 本 skill 不处理，需要先用 Whisper / 腾讯云 ASR 补字幕再接入流水线。

## 反模式（别做）

- ❌ **别帮用户做视频摘要**——这个项目不做摘要，做"保留全文 + 结构化"
- ❌ **别擅自"美化"讲者口吻**——脏话和啰嗦都是风格
- ❌ **别跳过"个人故事"段落**——它们是讲者风格的命脉
