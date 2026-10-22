"""Analyze framework bloat from probe transcripts, and statically across the rules.

Two independent signals, both read-only. Neither grades correctness, and
neither decides a rule is unnecessary. A rule that was read but never
mentioned is a *candidate* for review: the run may simply not have reached
the situation the rule covers.

  python3 tests/workflow/analyze_context.py <result.jsonl> [more.jsonl ...]
  python3 tests/workflow/analyze_context.py --duplicates
"""
import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOPWORDS = set("""a an the and or of to in is are be for on at by with as it its this that
these those from into not no but if then than so such can may must shall should will do does
did done have has had each any all other more most only own same too very just also which
who whom what when where why how use used using per each one two three when while
never always before after during without within across between under over above below
more less least most such same both either neither per""".split())


# ---------------------------------------------------------------- transcripts

def load(path):
    """Return (reasoning_corpus, reads).

    The reasoning corpus deliberately EXCLUDES the text of framework files
    that the agent read. Otherwise every rule block would "hit" simply by
    having been printed into the context, and the bloat signal would be
    worthless. What stays is what the agent itself said and wrote.
    """
    reasoning, reads = [], []
    with open(path) as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            kind = event.get("type")
            if kind == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        reasoning.append(block.get("text", ""))
                    elif block.get("type") == "thinking":
                        reasoning.append(block.get("thinking", ""))
                    elif block.get("type") == "tool_use" and block.get("name") == "Read":
                        reads.append((block.get("input", {}).get("file_path"),
                                      block.get("input", {}).get("offset"),
                                      block.get("input", {}).get("limit")))
                    elif block.get("type") == "tool_use" and block.get("name") == "Skill":
                        # The Skill tool injects the whole SKILL.md into context
                        # without a Read call. Count it as read, or the "never
                        # read" metric understates what the agent paid for.
                        skill = (block.get("input", {}) or {}).get("skill")
                        if skill:
                            reads.append((".claude/skills/%s/SKILL.md" % skill, None, None))
            # Tool results, including Skill and shell output, are context
            # supplied to the agent. They are not the agent's own citations.
    return reasoning, reads


def repo_relative(path):
    """Transcript paths point into the disposable project; map back to .claude/..."""
    if not path:
        return None
    marker = ".claude/"
    index = path.find(marker)
    return path[index:] if index >= 0 else path


def rule_blocks(path):
    lines = path.read_text().splitlines()
    blocks, current = [], None
    for number, line in enumerate(lines, 1):
        if line.startswith("#"):
            if current:
                blocks.append(current)
            current = {"heading": line.lstrip("#").strip(), "start": number, "lines": []}
        elif current is not None:
            current["lines"].append(line)
    if current:
        blocks.append(current)
    for block in blocks:
        block["end"] = block["start"] + len(block["lines"])
    return blocks


def distinctive_terms(block, corpus_freq, threshold):
    words = [w.strip("`.,:;()[]*_'\"").lower() for w in " ".join(block["lines"]).split()]
    seen, terms = set(), []
    for word in words:
        if len(word) < 5 or word in STOPWORDS or word in seen:
            continue
        seen.add(word)
        if corpus_freq.get(word, 0) <= threshold:
            terms.append(word)
    return terms[:14]


def analyze_transcripts(paths):
    corpus_parts, reads = [], []
    for path in paths:
        parts, file_reads = load(path)
        corpus_parts.extend(parts)
        reads.extend(file_reads)
    corpus = "\n".join(corpus_parts)
    lowered = corpus.lower()
    # Citations may appear in the agent's reasoning only; rule text echoing back
    # would inflate every section's count.
    words = re.findall(r"[a-z0-9_.-]{5,}", lowered)
    corpus_freq = collections.Counter(words)
    threshold = max(20, len(words) // 1000)

    per_file = collections.Counter()
    ranges = collections.defaultdict(list)
    for raw, offset, limit in reads:
        relative = repo_relative(raw)
        if not relative:
            continue
        per_file[relative] += 1
        start = (offset or 0) + 1
        ranges[relative].append((start, start + (limit or 10**9) - 1))

    cited = collections.Counter()
    for match in re.finditer(r"([A-Za-z0-9_./-]+\.md)`?\s*§+\s*([0-9]+(?:\.[0-9]+)*[a-z]?)", corpus):
        cited[(match.group(1).rsplit("/", 1)[-1], match.group(2))] += 1

    blocks = []
    for path in sorted((ROOT / ".claude").rglob("*.md")):
        relative = str(path.relative_to(ROOT))
        for block in rule_blocks(path):
            terms = distinctive_terms(block, corpus_freq, threshold)
            if not terms:
                continue
            hits = sum(1 for term in terms if term in lowered)
            read_in = any(not (block["end"] < low or block["start"] > high)
                          for low, high in ranges.get(relative, []))
            blocks.append({"file": relative, "heading": block["heading"],
                           "start_line": block["start"], "read": read_in, "hits": hits})

    # Nominal file-size exposure, not measured token use or billed context.
    cost = []
    for relative, count in per_file.items():
        target = ROOT / relative
        if not target.exists():
            continue
        size = target.stat().st_size
        cost.append({"file": relative, "loads": count, "bytes": count * size,
                     "file_bytes": size})
    cost.sort(key=lambda c: -c["bytes"])

    read_never = [b for b in blocks if b["read"] and b["hits"] == 0]
    never_read = [b for b in blocks if not b["read"]]
    return {
        "transcripts": [str(p) for p in paths],
        "corpus_chars": len(corpus),
        "read_calls": len(reads),
        "reads_per_file": [{"file": f, "reads": c} for f, c in per_file.most_common()],
        "context_cost": cost,
        "sections_cited": [{"ref": "%s §%s" % (f, s), "mentions": c}
                           for (f, s), c in cited.most_common()],
        "blocks_total": len(blocks),
        "read_but_never_mentioned": ["%s:%d — %s" % (b["file"], b["start_line"], b["heading"])
                                     for b in read_never],
        "never_read": ["%s:%d — %s" % (b["file"], b["start_line"], b["heading"])
                       for b in never_read],
    }


# ------------------------------------------------------------------- static

RULE_LINE = re.compile(r"^\s*(?:\d+\.\s*)?(?:\*\*)?([A-Z][^.\n]{12,140})\.")


def rule_sentences():
    """Pull imperative-looking rule sentences out of every framework file."""
    out = []
    for path in sorted((ROOT / ".claude").rglob("*.md")):
        relative = str(path.relative_to(ROOT))
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip() or line.startswith("#") or line.startswith("|"):
                continue
            match = RULE_LINE.match(line)
            if not match:
                continue
            text = match.group(1).strip()
            words = set(re.findall(r"[a-z]{4,}", text.lower())) - STOPWORDS
            if len(words) >= 5:
                out.append({"file": relative, "line": number, "text": text, "words": words})
    return out


def find_duplicates(threshold=0.55):
    """Rules that say substantially the same thing in more than one file."""
    rules = rule_sentences()
    clusters = []
    for i, rule in enumerate(rules):
        for other in rules[i + 1:]:
            if rule["file"] == other["file"]:
                continue
            union = rule["words"] | other["words"]
            if not union:
                continue
            score = len(rule["words"] & other["words"]) / len(union)
            if score >= threshold:
                clusters.append({"score": round(score, 2),
                                 "a": {k: rule[k] for k in ("file", "line", "text")},
                                 "b": {k: other[k] for k in ("file", "line", "text")}})
    clusters.sort(key=lambda c: -c["score"])
    return clusters


def cross_scenario(paths):
    """Blocks no supplied scenario read.

    A block unread in one run may simply be a step that run never reached.
    An unread block is untested surface, not evidence of redundancy.
    """
    per_run = []
    for path in paths:
        report = analyze_transcripts([path])
        per_run.append({row for row in report["never_read"]})
    shared = set.intersection(*per_run) if per_run else set()
    return {
        "scenarios": [str(p) for p in paths],
        "blocks_never_read_in_every_scenario": sorted(shared),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("transcripts", nargs="*")
    parser.add_argument("--duplicates", action="store_true")
    parser.add_argument("--cross-scenario", action="store_true",
                        help="blocks that NO scenario ever read (real redundancy candidates)")
    parser.add_argument("--json", dest="out")
    args = parser.parse_args()

    payload = {}
    if args.transcripts:
        payload["transcripts"] = analyze_transcripts([Path(p) for p in args.transcripts])
    if args.duplicates or not args.transcripts:
        payload["duplicates"] = find_duplicates()
    if len(args.transcripts) > 1 and args.cross_scenario:
        payload["cross_scenario"] = cross_scenario([Path(p) for p in args.transcripts])

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2))

    if "transcripts" in payload:
        report = payload["transcripts"]
        print("== transcripts ==")
        print("  corpus            : %d chars" % report["corpus_chars"])
        print("  Read calls        : %d" % report["read_calls"])
        print("  rule blocks       : %d" % report["blocks_total"])
        print("  read but unused   : %d" % len(report["read_but_never_mentioned"]))
        print("  never read        : %d" % len(report["never_read"]))
        print("  -- nominal file bytes × loads (not measured context cost) --")
        for row in report["context_cost"][:12]:
            print("     %7d B  %2d loads  %s" % (row["bytes"], row["loads"], row["file"]))
        print("  -- most-cited sections --")
        for row in report["sections_cited"][:12]:
            print("     %3d  %s" % (row["mentions"], row["ref"]))
        print("  -- read into context, never mentioned (candidates) --")
        for row in report["read_but_never_mentioned"][:30]:
            print("     " + row)
        print()
    if "cross_scenario" in payload:
        print("== never read in ANY supplied scenario (untested surface) ==")
        for row in payload["cross_scenario"]["blocks_never_read_in_every_scenario"]:
            print("  " + row)
        print()
    if "duplicates" in payload:
        print("== cross-file near-duplicate rules (jaccard >= 0.55) ==")
        print("  clusters: %d" % len(payload["duplicates"]))
        for cluster in payload["duplicates"][:30]:
            print("  %.2f  %s:%d  <->  %s:%d" % (cluster["score"], cluster["a"]["file"],
                                                cluster["a"]["line"], cluster["b"]["file"],
                                                cluster["b"]["line"]))
            print("        A: " + cluster["a"]["text"][:110])
            print("        B: " + cluster["b"]["text"][:110])


if __name__ == "__main__":
    main()
