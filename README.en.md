# videos-to-book

> Turn video courses, interviews, and talks **into a readable book**. yt-dlp for subtitles + AI restructuring into structured markdown + pluggable output adapters (local / Obsidian / Feishu / Notion).

[🇨🇳 中文文档 README.md](./README.md)

## Why this exists

Learning from video has three classic problems:
1. **Hard to skim** — scrubbing the timeline to find a specific point is painful
2. **Note-taking is exhausting** — scribbling while watching misses context
3. **Nothing to review** — videos aren't text, so you can't search or re-read

There are tools that download videos (yt-dlp), and tools that summarize them (Eightify / Glarity, SaaS-only and summary-focused). But **"preserve the speaker's full words + restructure by semantics + make it readable as a book"** — there's no mature open-source solution for this. That's what this project does.

Core assumption: **video subtitles are already great raw content**. They just need an editor who knows how to "strip filler words + add punctuation + organize structure + preserve personality". AI is that editor.

## What it does

**Three modes**:
- 🎓 **Single course → book** (e.g. a 91-episode B station screenwriting course → one long readable book)
- 🌏 **English video → Chinese book** (e.g. Lex Fridman interview → long-form Chinese essay)
- 📊 **Creator channels → weekly digest** (e.g. 10 YouTube indie dev channels → intelligence report each week)

**Supported sites** (inherited from yt-dlp): bilibili, YouTube, Vimeo, TikTok, Twitch, and [1700+ other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

**Non-goals**:
- ❌ Not a summarizer (many tools already do that)
- ❌ Does not download the video files themselves (subtitles + metadata only)
- ❌ No anti-scraping hacks — if a site isn't supported by yt-dlp, it isn't supported here either

## Quickstart

### Prerequisites
```bash
# 1. Install yt-dlp
pip install yt-dlp

# 2. Log into bilibili/YouTube in your browser (cookies will be read from browser)

# 3. Clone the project
git clone https://github.com/xiaotian283829691-dotcom/videos-to-book.git
cd videos-to-book
pip install -r requirements.txt

# 4. Set up config
cp config.example.yaml config.yaml
# Edit config.yaml per the comments
```

### Three typical workflows

#### 1. Chinese course → book (zh-lecture)
```bash
# Fetch subtitles for a bilibili playlist
python core/fetch.py --url "https://www.bilibili.com/video/BV1xxxxxx" --out ./tmp/course

# Let Claude Code restructure via SKILL.md
claude
> Use skills/videos-to-book/SKILL.md to restructure ./tmp/course/ srts per
> prompts/zh-lecture-to-book.md rules into book-style markdown at ./output/
```

#### 2. English video → Chinese long-form (en-to-zh)
```bash
python core/fetch.py --url "https://www.youtube.com/watch?v=XYZ" --out ./tmp/lex
claude
> Restructure per prompts/en-to-zh-book.md, output bilingual
```

#### 3. Creator weekly digest
```bash
# Batch fetch new videos from the past week
python core/fetch.py --channels config/channels.yaml --since 7d --out ./tmp/weekly

# Generate digest
claude
> Per prompts/creator-weekly.md, generate this week's indie dev digest,
> route through lark adapter to my Feishu channel
```

## Architecture

```
           Subtitle fetch       AI restructure        Output
        ┌─────────────┐       ┌─────────────┐     ┌──────────┐
  URL ─▶│   yt-dlp    │──srt─▶│  restructure│──md▶│ adapters │
        └─────────────┘       └─────────────┘     │          │
                                     ↑             │  local   │
                              prompt templates     │  obsidian│
                                                   │  lark    │
                                                   │  notion  │
                                                   └──────────┘
```

- **core/** — fetch + cleanup (pure Python, no AI dependency)
- **prompts/** — AI restructure prompt templates (the real know-how)
- **adapters/** — output targets (pluggable, enabled via config)
- **skills/** — Claude Code skill format for interactive use

## Layout

```
videos-to-book/
├── core/
│   ├── fetch.py              # yt-dlp wrapper
│   ├── srt2md.py             # srt → plain markdown
│   └── restructure.py        # AI restructuring (optional, SKILL is simpler)
├── prompts/
│   ├── zh-lecture-to-book.md # Chinese lecture → book (battle-tested on 91-episode course)
│   ├── en-to-zh-book.md      # English → Chinese book
│   └── creator-weekly.md     # Creator intel weekly digest
├── adapters/
│   ├── local.py              # Default: local md file ✅
│   ├── obsidian.py           # Obsidian vault ✅
│   ├── lark.py               # Create Feishu docx + optional chat notification ✅
│   └── notion.py             # Notion (TODO)
├── skills/
│   └── videos-to-book/
│       └── SKILL.md          # Claude Code skill entry
├── examples/                 # Real restructured samples (3 typical scenarios)
├── config.example.yaml
├── requirements.txt
└── README.md
```

## Samples

`examples/` contains three real end-to-end runs covering typical scenarios:

| Scenario | Sample | Prompt |
|---|---|---|
| Chinese lecture → book | `examples/P03-查理编剧课-劝学-样板.md` | `prompts/zh-lecture-to-book.md` |
| English interview → Chinese long-form | `examples/youtube-Greg-Isenberg-Obsidian-Claude-Code-样板.md` | `prompts/en-to-zh-book.md` |
| Chinese dialog/podcast restructure | `examples/bilibili-一麦三连-EP17-快乐-样板.md` | `prompts/zh-lecture-to-book.md` |

The goal is not "shorter"; the goal is **"readable"**.

Quick before/after:

**Before** (raw AI subtitle):
```
you know this learning learning this thing
is what I'm telling you guys
it's really not that simple think about it right
```

**After** (restructured):
```markdown
### Learning Is Not That Simple

Learning isn't that simple. Think about it.
```

## Using our battle-tested prompts

`prompts/zh-lecture-to-book.md` was forged through restructuring 91 episodes of a Chinese screenwriting course + multiple bilibili/YouTube interviews. **You can use it as-is or tune it to your domain** (technical talks, business interviews, academic lectures all differ).

## Known Pitfalls

Gotchas we hit during end-to-end testing — listed here so you don't hit them too.

### 1. bilibili subtitle requires Chrome login

```
WARNING: Subtitles are only available when logged in
```

**Cause**: Chrome bilibili cookie expired or never logged in.
**Fix**: Open Chrome, log into bilibili.com, re-run.
**Alt**: Use the "Get cookies.txt LOCALLY" browser extension to export cookies.txt, then `yt-dlp --cookies path/to/cookies.txt`.

### 2. Python 3.9 compat

Already compatible. All files use `from __future__ import annotations`. If you add a new file, avoid `str | None` (PEP 604 needs 3.10+). Use `Optional[str]`.

### 3. Same video's multi-language subtitles colliding

YouTube often provides both `.en.srt` and `.zh-Hans.srt`. srt2md names outputs `<stem>__<lang>.md` to avoid collision (fixed in early v0.1.x).

### 4. Feishu bot needs `docx:document` scope

The lark adapter creates Feishu docx (not chat messages). The bot needs `docx:document` scope. Without it:

```
Access denied. One of the following scopes is required: [docx:document]
```

Grant it here: `https://open.larkoffice.com/app/<your_app_id>/auth?q=docx:document`

### 5. AI subtitle misrecognition

AI subtitles have transcription errors (Chinese: homophones like "陈/程"; English: "Claude Code" → "Claw Code"). The prompt includes "context-based correction" rules so AI self-corrects.

### 6. Long videos need chunked processing

A single AI call has a max_tokens cap. For 1h+ videos:
- **Interactive**: Let Claude Code restructure chapter by chapter
- **Programmatic**: Modify `core/restructure.py` to split and batch-call

### 7. Chinese paths vs Chinese filenames

yt-dlp handles Chinese paths but some shells don't. Recommendation: use English paths for output dirs (e.g. `./tmp/`); filenames will still be Chinese (yt-dlp uses video title).

## Contributing

**Welcome**:
- New adapters (Discord / Slack / Teams / etc.)
- New prompt styles (technical / academic / business)
- Cookie handling improvements for more sites

**Out of scope**:
- Anti-scraping bypass, proxy pools, SaaS-ification — these are either messy or outside the tool's positioning.

## Author

[Yuan Xiaotian · OnceLab](https://oncelab.cn) — AI-era marketing tool product manager.
This project is part of [OnceLab](https://oncelab.cn)'s open-source infrastructure.

## License

MIT
