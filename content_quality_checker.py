"""
content_quality_checker.py
---------------------------
Reads a .txt file and outputs a content quality report flagging:
  - Overused words (appears more than N times)
  - Inconsistent capitalization of key terms
  - Sentences that are too long (readability flag)
  - Mixed language signals (PT-BR vs EN words in the same doc)
  - Profanity / flagged terms (EN and PT-BR, shown redacted)

Zero API cost. Works offline. Pure Python standard library only.

Usage:
    python content_quality_checker.py <file.txt> [options]

Options:
    --threshold N       Overuse threshold (default: 5)
    --max-words N       Max words per sentence before flagging (default: 40)
    --top N             Show top N overused words (default: 10)

Examples:
    python content_quality_checker.py transcript.txt
    python content_quality_checker.py chapter.txt --threshold 8 --max-words 35
"""

import re
import sys
import argparse
from collections import Counter


# ─────────────────────────────────────────────
# Language signal word lists
# ─────────────────────────────────────────────

PT_BR_SIGNALS = {
    "que", "não", "para", "com", "uma", "por", "isso", "mais",
    "mas", "como", "ele", "ela", "eles", "elas", "seu", "sua",
    "também", "quando", "onde", "ainda", "então", "sobre",
    "depois", "antes", "sempre", "nunca", "muito", "pouco",
    "aqui", "ali", "agora", "já", "pelo", "pela", "pelos",
    "pelas", "num", "numa", "nele", "nela", "disso", "nisso",
    "isso", "aquilo", "este", "esta", "esse", "essa",
}

EN_SIGNALS = {
    "the", "and", "that", "have", "for", "not", "with", "you",
    "this", "but", "his", "her", "they", "from", "she", "will",
    "one", "all", "would", "there", "their", "what", "about",
    "which", "when", "your", "said", "each", "how", "also",
    "into", "than", "then", "could", "these", "those", "been",
    "has", "had", "was", "were", "are", "our", "out", "if",
}

# Words to skip when checking overuse (articles, prepositions, etc.)
STOPWORDS_PT = {
    "a", "o", "as", "os", "de", "do", "da", "dos", "das", "e",
    "em", "no", "na", "nos", "nas", "um", "uma", "por", "para",
    "com", "que", "se", "ao", "à", "aos", "às", "eu", "ele",
    "ela", "nós", "mas", "ou", "já",
}

STOPWORDS_EN = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "as", "is", "it", "its",
    "be", "by", "from", "that", "this", "was", "are", "were",
    "he", "she", "we", "they", "i", "my", "you", "your",
}

STOPWORDS = STOPWORDS_PT | STOPWORDS_EN


# ─────────────────────────────────────────────
# Profanity / flagged terms (EN + PT-BR)
# ─────────────────────────────────────────────

PROFANITY_EN = {
    "fuck", "fucker", "fucking", "fucked", "fucks",
    "shit", "shitty", "shitting", "bullshit",
    "bitch", "bitches", "bitchy",
    "ass", "asshole", "assholes", "asses",
    "damn", "damned", "dammit",
    "crap", "crappy",
    "dick", "dicks", "cock", "cocks",
    "bastard", "bastards",
    "hell", "piss", "pissed", "pussy",
    "cunt", "whore", "slut",
    "motherfucker", "motherfucking",
}

PROFANITY_PT = {
    "porra", "caralho", "foda", "foder", "fodase",
    "merda", "bosta",
    "viado", "viadinho",
    "buceta", "xoxota",
    "puta", "putinha", "prostituta",
    "filho da puta", "filha da puta",
    "cu", "cuzão", "cuzinho",
    "cacete", "pau", "rola",
    "idiota", "imbecil", "otário", "otária",
    "babaca", "corno", "corna",
}

PROFANITY_ALL = PROFANITY_EN | PROFANITY_PT


# ─────────────────────────────────────────────
# Core analysis functions
# ─────────────────────────────────────────────

def load_text(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            return f.read()


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on . ! ? endings."""
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]


def tokenize_words(text: str) -> list[str]:
    """Extract lowercase alphabetic words only."""
    return re.findall(r"\b[a-záàãâéêíóôõúçñü]+\b", text.lower())


def check_overused_words(words: list[str], threshold: int, top_n: int) -> list[tuple]:
    """Return words that appear more than `threshold` times, excluding stopwords."""
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    counts = Counter(filtered)
    overused = [(word, count) for word, count in counts.most_common(top_n * 3)
                if count >= threshold]
    return overused[:top_n]


def check_capitalization(text: str) -> list[dict]:
    """
    Find key terms used with inconsistent capitalization.
    e.g. 'Podcast' vs 'podcast' vs 'PODCAST' in the same doc.
    """
    raw_words = re.findall(r"\b[A-Za-z]{3,}\b", text)
    grouped = {}
    for w in raw_words:
        key = w.lower()
        if key in STOPWORDS:
            continue
        grouped.setdefault(key, set()).add(w)

    inconsistent = []
    for base, variants in grouped.items():
        if len(variants) > 1:
            # Only flag if there's a meaningful mix (not just sentence-start cap)
            non_title = [v for v in variants if not v.istitle() and not v.isupper()]
            title     = [v for v in variants if v.istitle()]
            upper     = [v for v in variants if v.isupper() and len(v) > 1]
            if (title and non_title) or (upper and non_title) or (title and upper):
                inconsistent.append({
                    "term":     base,
                    "variants": sorted(variants),
                })

    return sorted(inconsistent, key=lambda x: x["term"])


def check_long_sentences(sentences: list[str], max_words: int) -> list[dict]:
    """Flag sentences that exceed the max word count threshold."""
    flagged = []
    for i, sentence in enumerate(sentences, 1):
        word_count = len(sentence.split())
        if word_count > max_words:
            preview = sentence[:90] + "..." if len(sentence) > 90 else sentence
            flagged.append({
                "sentence_num": i,
                "word_count":   word_count,
                "preview":      preview,
            })
    return flagged


def check_language_mix(words: list[str]) -> dict:
    """
    Detect PT-BR vs EN word signals and flag if both are significantly present.
    Returns counts and a dominant language guess.
    """
    pt_hits = [w for w in words if w in PT_BR_SIGNALS]
    en_hits = [w for w in words if w in EN_SIGNALS]

    pt_count = len(pt_hits)
    en_count = len(en_hits)
    total    = pt_count + en_count

    if total == 0:
        dominant = "Undetermined"
        mix_flag = False
    elif pt_count == 0:
        dominant = "English"
        mix_flag = False
    elif en_count == 0:
        dominant = "Portuguese (PT-BR)"
        mix_flag = False
    else:
        pt_pct   = pt_count / total
        dominant = "Portuguese (PT-BR)" if pt_pct >= 0.5 else "English"
        # Flag if the minority language makes up more than 15% of signals
        mix_flag = min(pt_pct, 1 - pt_pct) > 0.15

    return {
        "pt_count": pt_count,
        "en_count": en_count,
        "dominant": dominant,
        "mix_flag": mix_flag,
    }


def redact(word: str) -> str:
    """Redact middle characters of a word: 'fuck' → 'f**k'"""
    if len(word) <= 2:
        return word[0] + "*"
    return word[0] + "*" * (len(word) - 2) + word[-1]


def check_profanity(text: str) -> list[dict]:
    """
    Scan for profanity in both EN and PT-BR.
    Returns each hit with its line number, redacted form, and surrounding context.
    """
    hits = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, 1):
        # Tokenize preserving original casing for context
        tokens = re.findall(r"\b[\w'áàãâéêíóôõúçñü]+\b", line, re.IGNORECASE)
        for token in tokens:
            if token.lower() in PROFANITY_ALL:
                # Grab up to 60 chars of context around the word
                start  = max(line.lower().find(token.lower()) - 20, 0)
                snippet = line[start:start + 60].strip()
                if len(snippet) == 60:
                    snippet += "..."
                hits.append({
                    "line":    line_num,
                    "word":    token,
                    "redacted": redact(token),
                    "context": snippet,
                })

    return hits


# ─────────────────────────────────────────────
# Report printer
# ─────────────────────────────────────────────

def print_report(
    filepath:    str,
    text:        str,
    overused:    list,
    cap_issues:  list,
    long_sents:  list,
    lang_mix:    dict,
    profanity:   list,
    threshold:   int,
    max_words:   int,
) -> None:
    sentences  = split_sentences(text)
    words      = tokenize_words(text)
    char_count = len(text)

    div  = "─" * 58
    div2 = "═" * 58

    print(f"\n{div2}")
    print(f"  📄  CONTENT QUALITY REPORT")
    print(f"  File : {filepath}")
    print(f"{div2}")
    print(f"  Words      : {len(words):,}")
    print(f"  Sentences  : {len(sentences):,}")
    print(f"  Characters : {char_count:,}")
    print(f"{div2}\n")

    # ── 1. Overused Words ──────────────────────────────
    print(f"{div}")
    print(f"  🔁  OVERUSED WORDS  (threshold: ≥ {threshold} uses)")
    print(f"{div}")
    if overused:
        for word, count in overused:
            bar = "█" * min(count, 30)
            print(f"  {word:<20} {count:>4}x  {bar}")
    else:
        print(f"  ✅  No overused words found.")
    print()

    # ── 2. Capitalization ──────────────────────────────
    print(f"{div}")
    print(f"  ⚠️   INCONSISTENT CAPITALIZATION")
    print(f"{div}")
    if cap_issues:
        for item in cap_issues[:15]:   # cap output at 15 terms
            variants_str = ",  ".join(f'"{v}"' for v in item["variants"])
            print(f"  {item['term']:<20} → {variants_str}")
    else:
        print(f"  ✅  No capitalization inconsistencies found.")
    print()

    # ── 3. Long Sentences ─────────────────────────────
    print(f"{div}")
    print(f"  📏  LONG SENTENCES  (threshold: > {max_words} words)")
    print(f"{div}")
    if long_sents:
        for item in long_sents:
            print(f"  Sentence #{item['sentence_num']}  [{item['word_count']} words]")
            print(f"  ↳ {item['preview']}")
            print()
    else:
        print(f"  ✅  All sentences within the {max_words}-word limit.")
    print()

    # ── 4. Language Mix ───────────────────────────────
    print(f"{div}")
    print(f"  🌐  LANGUAGE DETECTION")
    print(f"{div}")
    total_signals = lang_mix["pt_count"] + lang_mix["en_count"]
    if total_signals > 0:
        pt_pct = round(lang_mix["pt_count"] / total_signals * 100)
        en_pct = 100 - pt_pct
        print(f"  Dominant language : {lang_mix['dominant']}")
        print(f"  PT-BR signals     : {lang_mix['pt_count']}  ({pt_pct}%)")
        print(f"  EN signals        : {lang_mix['en_count']}  ({en_pct}%)")
        if lang_mix["mix_flag"]:
            print(f"\n  ⚠️  Mixed language detected — both PT-BR and EN content")
            print(f"      present in significant amounts. Review for consistency.")
        else:
            print(f"\n  ✅  Language appears consistent.")
    else:
        print(f"  ⚠️  Could not determine language (too few signal words).")
    print()

    # ── 5. Profanity ──────────────────────────────────
    print(f"{div}")
    print(f"  🤬  PROFANITY / FLAGGED TERMS")
    print(f"{div}")
    if profanity:
        for hit in profanity:
            print(f"  Line {hit['line']:<6} {hit['redacted']:<15}  ↳ ...{hit['context']}...")
    else:
        print(f"  ✅  No profanity or flagged terms found.")
    print()

    # ── Summary ───────────────────────────────────────
    print(f"{div2}")
    issues = sum([
        len(overused) > 0,
        len(cap_issues) > 0,
        len(long_sents) > 0,
        lang_mix["mix_flag"],
        len(profanity) > 0,
    ])
    if issues == 0:
        print(f"  ✅  All checks passed. Content looks clean!")
    else:
        print(f"  ⚠️   {issues} issue category(s) flagged. Review report above.")
    print(f"{div2}\n")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Content quality checker for .txt files."
    )
    parser.add_argument("file",          help="Path to the .txt file to analyze")
    parser.add_argument("--threshold",   type=int, default=5,  help="Overuse word threshold (default: 5)")
    parser.add_argument("--max-words",   type=int, default=40, help="Max words per sentence (default: 40)")
    parser.add_argument("--top",         type=int, default=10, help="Top N overused words to show (default: 10)")

    args = parser.parse_args()

    text      = load_text(args.file)
    words     = tokenize_words(text)
    sentences = split_sentences(text)

    overused   = check_overused_words(words, args.threshold, args.top)
    cap_issues = check_capitalization(text)
    long_sents = check_long_sentences(sentences, args.max_words)
    lang_mix   = check_language_mix(words)
    profanity  = check_profanity(text)

    print_report(
        filepath   = args.file,
        text       = text,
        overused   = overused,
        cap_issues = cap_issues,
        long_sents = long_sents,
        lang_mix   = lang_mix,
        profanity  = profanity,
        threshold  = args.threshold,
        max_words  = args.max_words,
    )


if __name__ == "__main__":
    main()
