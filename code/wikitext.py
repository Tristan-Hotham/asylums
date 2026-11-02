"""Small wikitext helpers: find a template by brace matching, split its parameters, read {{coord}}, years, numbers,
and turn wikitext into plain text (links kept as their label, references, comments, files and templates removed)."""
import re, html as _html


def find_template(text, name_re):
    """Return the body of the first {{name ...}} template (outer braces removed), or None."""
    m = re.search(r"\{\{\s*(" + name_re + r")\b", text, re.I)
    if not m:
        return None
    i, depth = m.start(), 0
    j = i
    while j < len(text) - 1:
        two = text[j:j + 2]
        if two == "{{":
            depth += 1; j += 2; continue
        if two == "}}":
            depth -= 1; j += 2
            if depth == 0:
                return text[i + 2:j - 2]
            continue
        j += 1
    return text[i + 2:]          # cut off by the 6,000 character limit


def split_params(body):
    """Split a template body on top-level pipes into {key: value}; positional parameters get keys 1, 2..."""
    parts, depth, sq, cur = [], 0, 0, []
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two == "{{": depth += 1; cur.append(two); i += 2; continue
        if two == "}}": depth -= 1; cur.append(two); i += 2; continue
        if two == "[[": sq += 1; cur.append(two); i += 2; continue
        if two == "]]": sq -= 1; cur.append(two); i += 2; continue
        c = body[i]
        if c == "|" and depth == 0 and sq == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(c)
        i += 1
    parts.append("".join(cur))
    out, pos = {}, 0
    for p in parts[1:]:
        if "=" in p and re.match(r"\s*[\w ]+\s*=", p):
            k, v = p.split("=", 1); out[k.strip().lower()] = re.sub(r"<!--.*?-->", "", v, flags=re.S).strip()
        else:
            pos += 1; out[str(pos)] = p.strip()
    return out


def coord(text):
    """(lat, lon) from the first {{coord}} in text, decimal or degrees/minutes/seconds; None if absent."""
    b = find_template(text, r"coord")
    if b is None:
        return None
    ps = [p.strip() for p in b.split("|")[1:] if "=" not in p and ":" not in p]
    ps = [p for p in ps if p]
    try:
        if len(ps) >= 2 and all(re.fullmatch(r"-?\d+(\.\d+)?", p) for p in ps[:2]) and not any(p.upper() in ("N", "S") for p in ps):
            lat, lon = float(ps[0]), float(ps[1])
            return (lat, lon) if abs(lat) <= 90 and abs(lon) <= 180 else None
        # D M S N D M S W, D M N D M W, or D N D W
        k = [i for i, p in enumerate(ps) if p.upper() in ("N", "S")][0]
        la = [float(x) for x in ps[:k]]; h1 = ps[k].upper()
        rest = ps[k + 1:]; k2 = [i for i, p in enumerate(rest) if p.upper() in ("E", "W")][0]
        lo = [float(x) for x in rest[:k2]]; h2 = rest[k2].upper()
        dms = lambda v: v[0] + (v[1] / 60 if len(v) > 1 else 0) + (v[2] / 3600 if len(v) > 2 else 0)
        lat, lon = dms(la) * (1 if h1 == "N" else -1), dms(lo) * (1 if h2 == "E" else -1)
        return (lat, lon)
    except (IndexError, ValueError):
        return None


YEAR = re.compile(r"(?<!\d)(1[2-9]\d\d|20[0-2]\d)(?!\d)")


def years(s):
    return [int(y) for y in YEAR.findall(s or "") if 1200 <= int(y) <= 2026]


def first_int(s):
    m = re.search(r"(?<![\d.])(\d{1,2},\d{3}|\d{2,5})(?![\d.,]*\s*(acres|hectares|ha\b|m\b|km|miles))", (s or "").replace(" ", " "))
    return int(m.group(1).replace(",", "")) if m else None


def plain(w):
    """Wikitext to plain text."""
    t = re.sub(r"<!--.*?-->", "", w, flags=re.S)
    t = re.sub(r"<ref[^>/]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<ref[^>]*>.*$", "", t, flags=re.S)             # an unclosed reference at the cut
    for _ in range(6):                                            # nested templates, innermost first
        t2 = re.sub(r"\{\{(?:convert|cvt)\|([\d.,]+)\|([a-z]+)[^{}]*\}\}", r"\1 \2", t, flags=re.I)
        t2 = re.sub(r"\{\{(?:lang|nowrap|small|sic)\|(?:[a-z-]+\|)?([^{}|]*)\}\}", r"\1", t2, flags=re.I)
        t2 = re.sub(r"\{\{[^{}]*\}\}", "", t2)
        if t2 == t: break
        t = t2
    t = re.sub(r"\[\[(?:File|Image):(?:[^\[\]]|\[\[[^\]]*\]\])*\]\]", "", t, flags=re.I)
    t = re.sub(r"\[\[Category:[^\]]*\]\]", "", t, flags=re.I)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", t)
    t = re.sub(r"'''?", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = _html.unescape(t).replace(" ", " ")
    return re.sub(r"[ \t]+", " ", t).strip()


def lead_and_body(head):
    """Split the wikitext head into the lead (before the first == heading ==, infobox removed) and the rest."""
    ib = find_template(head, r"infobox[^|\n]*")
    h = head.replace("{{" + ib + "}}", "") if ib else head
    m = re.search(r"^==[^=].*?==\s*$", h, re.M)
    lead, body = (h[:m.start()], h[m.start():]) if m else (h, "")
    return plain(lead), plain(re.sub(r"^=+.*?=+\s*$", "\n", body, flags=re.M))
