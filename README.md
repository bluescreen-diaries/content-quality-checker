# 🔍 Content Quality Checker

> A zero-dependency Python CLI tool that reads any `.txt` file and outputs a structured quality report — built for content operations workflows involving Portuguese (PT-BR) and English text.

---

🤖 A Note on How This Was Built

This project was developed collaboratively with Claude (Anthropic) as an AI coding assistant. I'm a self-taught career changer transitioning into IT, not a professional developer. I have a working understanding of Python syntax and can read and somewhat modify the code and used Claude to help generate, explain, and refine the code throughout this project.

What I brought to it:

The original idea, use case, and requirements
All architectural decisions
Feature design and command layout
Testing, troubleshooting, and iteration based on real-world results
Understanding the codebase well enough to use, explain, and extend it

What AI helped with:
Writing and debugging Python code beyond my current skill level
Translating my ideas into working implementations
Explaining concepts as we built, so I could learn along the way
I'm sharing this because I believe transparency about AI-assisted development matters, and because knowing how to effectively leverage AI tools is itself a real and valuable skill in 2026.

---

## 🧠 Why This Exists

Content operations teams review large volumes of text — podcast transcripts, ebook drafts, article copy — where quality issues like overused words, inconsistent terminology, or mixed-language content can slip through manual review. This tool automates that first-pass audit, flagging issues before content goes live.

---

## ✅ What It Checks

| Check | What It Flags |
|-------|---------------|
| 🔁 **Overused Words** | Words appearing more than N times (excludes stopwords) |
| ⚠️ **Inconsistent Capitalization** | Same term written as `podcast`, `Podcast`, and `PODCAST` |
| 📏 **Long Sentences** | Sentences exceeding a word-count threshold (readability) |
| 🌐 **Mixed Language** | Significant PT-BR and EN content mixed in the same document |

---

## 🚀 Usage

No installation required — pure Python standard library.

```bash
python content_quality_checker.py <file.txt> [options]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--threshold N` | `5` | Flag words appearing ≥ N times |
| `--max-words N` | `40` | Flag sentences longer than N words |
| `--top N` | `10` | Show top N overused words |

**Examples:**

```bash
# Basic run with defaults
python content_quality_checker.py transcript.txt

# Stricter settings for shorter content
python content_quality_checker.py chapter.txt --threshold 3 --max-words 30

# Looser settings for long-form content
python content_quality_checker.py ebook_draft.txt --threshold 10 --max-words 55 --top 15
```

---

## 📊 Sample Output

```
══════════════════════════════════════════════════════════
  📄  CONTENT QUALITY REPORT
  File : sample_transcript.txt
══════════════════════════════════════════════════════════
  Words      : 282
  Sentences  : 20
  Characters : 1,846
══════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────
  🔁  OVERUSED WORDS  (threshold: ≥ 4 uses)
──────────────────────────────────────────────────────────
  tecnologia              6x  ██████
  como                    6x  ██████
  podcast                 5x  █████
  inteligência            5x  █████
  artificial              5x  █████

──────────────────────────────────────────────────────────
  ⚠️   INCONSISTENT CAPITALIZATION
──────────────────────────────────────────────────────────
  podcast              → "PODCAST",  "Podcast",  "podcast"
  hoje                 → "Hoje",  "hoje"

──────────────────────────────────────────────────────────
  📏  LONG SENTENCES  (threshold: > 45 words)
──────────────────────────────────────────────────────────
  Sentence #14  [61 words]
  ↳ Quando você começa a entender os fundamentos básicos, percebe que muitas das aplicações qu...

──────────────────────────────────────────────────────────
  🌐  LANGUAGE DETECTION
──────────────────────────────────────────────────────────
  Dominant language : Portuguese (PT-BR)
  PT-BR signals     : 34  (77%)
  EN signals        : 10  (23%)

  ⚠️  Mixed language detected — both PT-BR and EN content
      present in significant amounts. Review for consistency.

══════════════════════════════════════════════════════════
  ⚠️   4 issue category(s) flagged. Review report above.
══════════════════════════════════════════════════════════
```

---

## 📂 Project Structure

```
content-quality-checker/
├── content_quality_checker.py   # Main script
├── sample_transcript.txt        # Sample PT-BR podcast transcript for testing
└── README.md
```

---

## 🔧 Requirements

- Python 3.8+
- No external libraries — uses only `re`, `collections`, `argparse` from the standard library

---

---

## 👩‍💻 Author

Built as a portfolio project demonstrating content quality tooling for PT-BR and English digital content operations.
