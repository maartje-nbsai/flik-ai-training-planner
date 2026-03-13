"""
build_from_db.py

Rebuilds scraped_pages.json from the WordPress database CSV exports.
Replaces the scraper + cleaner pipeline with full, unpaywalled content.

Sources:
    wpmm_posts.csv      — post content, titles, slugs, hierarchy
    wpmm_postmeta.csv   — structured drill fields, prereqs, theory links

Output:
    scraped_pages.json  — same format as before (url, title, text) plus
                          extra fields for drills (prereqs, next_drills,
                          theory_links) for use by future tooling.

Usage:
    python build_from_db.py
"""

import csv
import html
import json
import re
import sys

csv.field_size_limit(10**7)

INPUT_POSTS    = "wpmm_posts.csv"
INPUT_META     = "wpmm_postmeta.csv"
OUTPUT_FILE    = "scraped_pages.json"
BASE_URL       = "https://www.flikulti.com"

# WordPress post types → URL prefix
TYPE_PREFIX = {
    "drills":        "drills",
    "theory":        "theory",
    "sessions":      "sessions",
    "video":         "video",
    "sc":            "sc-dashboard",
    "team-analysis": "theory/analysis",
}


# ---------------------------------------------------------------------------
# HTML stripping
# ---------------------------------------------------------------------------

def strip_html(text: str) -> str:
    """Remove HTML tags, decode entities, collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# PHP serialize parser (for _tips field)
# ---------------------------------------------------------------------------

def parse_php_serialized_strings(value: str) -> list[str]:
    """
    Extract all quoted string values from a PHP serialized array.
    e.g. a:1:{i:0;s:158:"some tip text";}  →  ["some tip text"]
    Handles escaped quotes and multi-entry arrays.
    """
    results = []
    # Find all s:N:"..." entries
    for m in re.finditer(r's:\d+:"(.*?)"(?:;|})', value, re.DOTALL):
        results.append(m.group(1).replace('\\"', '"'))
    return results


# ---------------------------------------------------------------------------
# [link id="N"] resolver
# ---------------------------------------------------------------------------

def resolve_link_tags(text: str, id_to_url: dict, id_to_title: dict) -> str:
    """
    Replace [link id="123"] with "TITLE (URL)" where known,
    or just remove the tag if unknown.
    """
    def replacer(m):
        lid = m.group(1)
        url = id_to_url.get(lid)
        title = id_to_title.get(lid)
        if url and title:
            return f"{title} ({url})"
        elif url:
            return url
        return ""
    return re.sub(r"\[link id=['\"]?(\d+)['\"]?\]", replacer, text)


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------

def build_url(post_id: str, posts: dict) -> str | None:
    """Build the public URL for a post."""
    post = posts.get(post_id)
    if not post:
        return None
    pt = post["post_type"]
    if pt not in TYPE_PREFIX:
        return None

    if pt == "theory":
        # Walk parent chain to build slug path
        parts = []
        current = post
        while current:
            parts.append(current["post_name"])
            parent_id = current["post_parent"]
            if parent_id == "0" or parent_id not in posts:
                break
            current = posts.get(parent_id)
        parts.reverse()
        slug = "/".join(parts)
        return f"{BASE_URL}/theory/{slug}/"
    elif pt == "team-analysis":
        return f"{BASE_URL}/theory/analysis/{post['post_name']}/"
    else:
        prefix = TYPE_PREFIX[pt]
        return f"{BASE_URL}/{prefix}/{post['post_name']}/"


# ---------------------------------------------------------------------------
# Per-type text builders
# ---------------------------------------------------------------------------

def build_drill_text(post: dict, meta: dict, id_to_url: dict, id_to_title: dict) -> dict:
    """Assemble rich text for a drill from postmeta fields."""
    title = post["post_title"]
    intro = meta.get("_intro", "").strip()
    instructions_raw = meta.get("_instructions", "").strip()
    rotation_raw = meta.get("_rotation", "").strip()
    tips_raw = meta.get("_tips", "")

    # Instructions use # as line separator and // as section separator
    instructions = instructions_raw.replace("//", "\n").replace("#", "\n").strip()
    instructions = resolve_link_tags(instructions, id_to_url, id_to_title)

    rotation = rotation_raw.replace("#", "\n").strip()

    tips = parse_php_serialized_strings(tips_raw)

    # Resolve prereq IDs → urls + titles
    prereq_raw = meta.get("_prereq", "null")
    prereq_ids = []
    try:
        prereq_ids = json.loads(prereq_raw) or []
    except (json.JSONDecodeError, TypeError):
        pass

    prereq_links = []
    for pid in prereq_ids:
        pid = str(pid)
        url = id_to_url.get(pid)
        t = id_to_title.get(pid, pid)
        if url:
            prereq_links.append(f"{t} ({url})")

    # Resolve linked theory IDs → urls + titles
    theory_raw = meta.get("_theory-drills", "null")
    theory_ids = []
    try:
        theory_ids = json.loads(theory_raw) or []
    except (json.JSONDecodeError, TypeError):
        pass

    theory_links = []
    for tid in theory_ids:
        tid = str(tid)
        url = id_to_url.get(tid)
        t = id_to_title.get(tid, tid)
        if url:
            theory_links.append(f"{t} ({url})")

    # Build readable text block
    parts = [title]
    if intro:
        parts.append(intro)
    if instructions:
        parts.append("Instructions:\n" + instructions)
    if rotation:
        parts.append("Rotation:\n" + rotation)
    # Strip "username@" author attribution prefix from tips
    tips = [re.sub(r"^\w+@", "", t).strip() for t in tips]
    if tips:
        parts.append("Tips:\n" + "\n".join(f"- {t}" for t in tips))
    if prereq_links:
        parts.append("Prerequisites:\n" + "\n".join(f"- {p}" for p in prereq_links))
    if theory_links:
        parts.append("Related theory:\n" + "\n".join(f"- {l}" for l in theory_links))

    text = "\n\n".join(parts)

    return {
        "text": text,
        "prereqs": prereq_links,
        "theory_links": theory_links,
    }


def build_theory_text(post: dict, meta: dict, id_to_url: dict, id_to_title: dict) -> str:
    """Strip HTML from post_content and resolve internal link tags."""
    content = strip_html(post["post_content"])
    content = resolve_link_tags(content, id_to_url, id_to_title)

    theory_intro = strip_html(meta.get("_theory-intro", "")).strip()
    if theory_intro:
        content = theory_intro + "\n\n" + content

    return content


def build_session_text(post: dict, meta: dict, id_to_url: dict, id_to_title: dict) -> str:
    """Build session text from aims + drill list resolved to titles/urls."""
    aims = meta.get("_aims", "").strip()

    # drills field: "id;minutes//id;minutes//..."
    drills_raw = meta.get("drills", "").strip()
    drill_lines = []
    for entry in drills_raw.split("//"):
        parts = entry.strip().split(";")
        if not parts or not parts[0]:
            continue
        drill_id = parts[0].strip()
        minutes = parts[1].strip() if len(parts) > 1 else "?"
        url = id_to_url.get(drill_id)
        title = id_to_title.get(drill_id, f"Drill {drill_id}")
        line = f"- {title} ({minutes} min)"
        if url:
            line += f" — {url}"
        drill_lines.append(line)

    parts = [post["post_title"]]
    if aims:
        parts.append(aims)
    if drill_lines:
        parts.append("Drills:\n" + "\n".join(drill_lines))

    return "\n\n".join(parts)


def build_video_text(post: dict, meta: dict) -> str:
    """Build video text from post_content + intro."""
    content = strip_html(post["post_content"])
    video_intro = meta.get("_video-intro", "").strip()
    video_text = meta.get("_video-text", "").strip()

    parts = [post["post_title"]]
    if video_intro:
        parts.append(video_intro)
    if video_text:
        parts.append(strip_html(video_text))
    if content:
        parts.append(content)

    return "\n\n".join(parts)


def build_sc_text(post: dict, meta: dict) -> str:
    """Build strength & conditioning text from postmeta."""
    parts = [post["post_title"]]
    sc_intro = meta.get("_sc-intro", "").strip()
    sc_video_text = meta.get("_sc-video-text", "").strip()
    sc_attrs = meta.get("_sc-attributes", "").strip()
    content = strip_html(post["post_content"])

    if sc_intro:
        parts.append(sc_intro)
    if sc_video_text:
        parts.append(strip_html(sc_video_text))
    if sc_attrs:
        parts.append("Attributes: " + sc_attrs)
    if content:
        parts.append(content)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("[build] Loading posts CSV...")
    with open(INPUT_POSTS, encoding="cp1252", errors="replace") as f:
        all_posts = {r["ID"]: r for r in csv.DictReader(f) if r["post_status"] == "publish"}

    print("[build] Loading postmeta CSV...")
    meta_by_post: dict[str, dict] = {}
    with open(INPUT_META, encoding="cp1252", errors="replace") as f:
        for r in csv.DictReader(f):
            pid = r["post_id"]
            if pid not in meta_by_post:
                meta_by_post[pid] = {}
            # Keep last value for each key (avoids duplicates)
            meta_by_post[pid][r["meta_key"]] = r["meta_value"]

    # Build ID → URL and ID → title lookups (for link resolution)
    print("[build] Building URL index...")
    id_to_url: dict[str, str] = {}
    id_to_title: dict[str, str] = {}
    for post_id, post in all_posts.items():
        url = build_url(post_id, all_posts)
        if url:
            id_to_url[post_id] = url
            id_to_title[post_id] = post["post_title"]

    print(f"[build] Indexed {len(id_to_url)} posts with URLs")

    # Build pages
    pages = []
    skipped = 0

    relevant_types = set(TYPE_PREFIX.keys())

    for post_id, post in all_posts.items():
        pt = post["post_type"]
        if pt not in relevant_types:
            continue

        url = id_to_url.get(post_id)
        if not url:
            skipped += 1
            continue

        title = post["post_title"]
        meta = meta_by_post.get(post_id, {})

        extra = {}

        if pt == "drills":
            result = build_drill_text(post, meta, id_to_url, id_to_title)
            text = result["text"]
            extra["prereqs"] = result["prereqs"]
            extra["theory_links"] = result["theory_links"]

        elif pt in ("theory", "team-analysis"):
            text = build_theory_text(post, meta, id_to_url, id_to_title)

        elif pt == "sessions":
            text = build_session_text(post, meta, id_to_url, id_to_title)

        elif pt == "video":
            text = build_video_text(post, meta)

        elif pt == "sc":
            text = build_sc_text(post, meta)

        else:
            skipped += 1
            continue

        if not text.strip():
            skipped += 1
            continue

        page = {"url": url, "title": title, "text": text, "post_type": pt}
        page.update(extra)
        pages.append(page)

    # Sort by URL for stable output
    pages.sort(key=lambda p: p["url"])

    print(f"[build] Built {len(pages)} pages ({skipped} skipped — no URL or empty content)")

    # Summary by type
    from collections import Counter
    counts = Counter(p["post_type"] for p in pages)
    for t, n in sorted(counts.items()):
        print(f"  {t:20s} {n}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"\n[build] Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
