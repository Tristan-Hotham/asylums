"""Read the Wikipedia articles, keep the asylums and psychiatric hospitals, and pull out what each article states:
coordinates, opening and closing years, beds, names, listed status and what became of the place.

Which articles count (documented in the paper and README). An article is kept when it describes a single place and
  A  the first two sentences of its lead call it a psychiatric or mental hospital, an asylum, a lunatic asylum, or an
     institution for people with learning disabilities (words: psychiatric, asylum, lunatic, mental, insane, madhouse,
     idiot, imbecile, feeble-minded, mentally handicapped or defective, learning or intellectual disability, epileptic);
     the phrases Metropolitan Asylums Board, sick asylum, orphan asylum, Lock Asylum and asylum seeker do not count; or
  B  its infobox type or speciality uses one of those words and does not say General; or
  C  Wikipedia files it in a psychiatric hospital category (incats or page categories) and one of the words appears
     somewhere in the first 6,000 characters.
It is dropped when it is not a single place: a person (infobox person), an NHS trust, tribunal, charity or private
provider, a unit "based at" another hospital, the Epsom Cluster overview, or a drug and alcohol rehabilitation centre.
Articles describing the same site (within 300 m, checked by hand) are merged; the merges are listed in MERGE.

Years. Opened: the infobox field founded, opened or constructed; else the lead ("opened in 1851", "established in");
else the page category "NNNN establishments in". Closed: the infobox field closed; else the lead or text ("closed in
1995"); else the category "Hospitals disestablished in NNNN". Each value keeps its source. A place counts as still
open when the article's lead says it "is" a hospital or facility in the present tense and gives no closing year.

Beds: the infobox beds field; else the largest number of "beds" or "patients" the first 6,000 characters state, with
its phrase kept. These are stated capacities at some date, not a consistent peak.

Fate (what the place is now): keyword rules on the lead, and if the lead says nothing, on the rest of the text:
  derelict   derelict, disused, abandoned, lies empty, vacant, ruin, boarded up
  homes      flats, apartments, housing, homes, residential use or estate, dwellings, with a conversion, redevelopment or
             present-tense verb in the same clause (converted, redeveloped, developed, now, replaced by, make way for...);
             new housing on a cleared site counts. Not: care, nursing, family, staff or 'own' homes; plans or proposals
             for housing (flagged 'plans', not counted).
  other      college, university, campus, offices, hotel, business park, prison, museum, wedding venue, film studio,
             leisure, commercial, with the same kind of verb; schools of nursing and administration offices do not count
  demolished demolished, pulled down, razed, knocked down
  health     still open (present tense lead, no closing year) or "continues to provide", "remains a hospital"
  unknown    nothing stated
When several apply the order is health (if still open), homes, other, derelict, demolished: a site that stood derelict and
was then rebuilt as housing counts as homes, and 'demolished' means demolished with no new use stated.
Listed: 'Grade I/II*/II listed', 'Category A/B/C listed' or 'listed building' in the text or the page categories."""
import csv, collections
import numpy as np, pandas as pd
from common import *
from wikitext import *

W = jload(f"{RAW}/wp_pages.json")
PG = W["pages"]
CHK = {"pages": len(PG), "cats_walked": W["cats"]}

PSY = re.compile(r"\b(psychiatr\w*|asylums?|lunatics?|mental|mentally|insane|insanity|madhouses?|idiots?|imbeciles?|feeble[- ]minded|"
                 r"learning disabilit\w*|intellectual disabilit\w*|epileptics?|psychogeriatric)\b", re.I)
FALSE = re.compile(r"Metropolitan Asylums Board|sick asylum|orphans?'? asylum|Lock Asylum|asylum seekers?|Female Orphan Asylum|Seamen's Orphan Asylum", re.I)
NOTPLACE_KIND = {"person", "military person", "uk legislation", "military unit"}
NOTPLACE = re.compile(r"\b(is|was) an? (NHS trust|tribunal|large independent charity|independent charity|specialist private provider|cluster or group)\b|"
                      r"\bis based at the\b|drug and alcohol rehabilitation", re.I)
GENERAL = {"Southern General Hospital"}   # general hospital, in a psychiatric category because Govan poorhouse had a lunatic asylum
# same site, two articles (first kept, later merged into it): checked by hand from coordinates within 300 m
MERGE = {"Beaufort War Hospital": "Glenside, Bristol"}


def psy(s):
    return bool(PSY.search(FALSE.sub(" ", s or "")))


def sentences(t, n=2):
    return " ".join(re.split(r"(?<=[a-z0-9\)\]'\"])\.\s+(?=[A-Z])", t.strip())[:n])


rows, dropped = [], []
for title, p in PG.items():
    h = p["head"]; ib = find_template(h, r"infobox[^|\n]*")
    kind = re.match(r"infobox\s*([^\n|]*)", ib, re.I).group(1).strip().lower() if ib else ""
    f = split_params(ib) if ib else {}
    lead, body = lead_and_body(h)
    s2 = sentences(lead)
    cats = p["cats"]; incats = p["incats"]
    in_psy_cat = any(("sychiatric hosp" in c) and "People detained" not in c for c in incats + cats) or any("Intellectual disability hosp" in c for c in cats)
    ty = plain(f.get("type", "") + " ; " + f.get("speciality", ""))
    A, B = psy(s2), psy(ty) and not re.search(r"general|teaching|district", ty, re.I)
    C = in_psy_cat and psy(lead + " " + body)
    r = {"title": title, "revid": p["revid"], "wikidata": p["wikidata"], "kind": kind, "lead": lead, "body": body, "s2": s2, "f": f, "cats": cats,
         "incats": incats, "A": A, "B": B, "C": C, "in_psy_cat": in_psy_cat, "type": ty}
    why = None
    if kind in NOTPLACE_KIND: why = "a person or other non-place article"
    elif NOTPLACE.search(sentences(lead, 1)[:160]): why = "an organisation, unit or group article, not a single place"
    elif title == "Epsom Cluster": why = "an organisation, unit or group article, not a single place"
    elif title in GENERAL: why = "a general hospital whose site once had a lunatic ward (checked by hand)"
    elif not (A or B or C):
        why = "a general or other hospital (no psychiatric signal in category, infobox or lead)" if kind == "hospital" or "hospital" in title.lower() else "not a hospital article"
    if why:
        dropped.append({"title": title, "reason": why, "in_psy_cat": in_psy_cat, "first_sentences": s2[:300]}); continue
    rows.append(r)
CHK["kept_before_merge"] = len(rows)

# ---------- fields ----------
MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"


def raw(v):
    """Infobox value with references and comments removed but templates kept (dates live in {{start date|1863}})."""
    v = re.sub(r"<!--.*?-->", "", v or "", flags=re.S)
    return re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", v, flags=re.S)


def yr_field(v):
    ys = years(raw(v))
    return ys[0] if ys else None


def lead_year(text, verbs, subject=False):
    """Year in the first clause that uses one of the verbs ('opened in 1851'). With subject=True the verb must have the
    place itself as subject (the hospital, the asylum, it), so 'the Stanley Royd Hospital closed' does not count.
    Clauses about a campus, a refurbishment, a new or replacement facility or a re-opening are skipped."""
    subj = r"(?:\b(?:[Tt]he (?:hospital|asylum|institution|facility)|It|it)\s+(?:was\s+)?(?:finally\s+|eventually\s+|officially\s+)?)" if subject else r"\b(?<!re-)"
    for m in re.finditer(subj + r"(?:" + verbs + r")\b[^.;]{0,90}?\b(?:in|on)\s+(?:the\s+)?(?:\d{1,2}\s+)?(?:" + MONTHS + r"\s+)?(1[6-9]\d\d|20[0-2]\d)\b", text):
        clause = text[max(0, m.start() - 80):m.end() + 40]
        if re.search(r"campus|refurbish|new (?:hospital|facilit|building|unit)|replacement|re-opened|reopened|nursing home", clause, re.I): continue
        return int(m.group(1))
    return None


def cat_year(cats, pat):
    for c in cats:
        m = re.search(pat, c)
        if m: return int(m.group(1))
    return None


TERMS = [("lunatic asylum", r"lunatic asylum|asylum for (?:the )?(?:insane|lunatics)|pauper lunatic|lunatic hospital|criminal lunatic"),
         ("asylum", r"\basylum\b"),
         ("mental hospital", r"mental hospital"),
         ("institution or colony", r"\b(?:colony|institution|mental deficiency|epileptic colony|training school|school for (?:imbecile|idiot))"),
         ("psychiatric hospital", r"psychiatric hospital"),
         ("mental health unit or centre", r"mental health (?:unit|centre|center|hospital)|\bclinic\b|resource centre"),
         ("hospital", r"\bhospital\b")]


def term_of(name):
    n = name.lower()
    for k, pat in TERMS:
        if re.search(pat, n): return k
    return None


NAMEPAT = re.compile(r"(?:the\s+)?((?:[A-Z][\w'’.&-]*|of|the|and|for|de|on|upon|in|St\.?|Saint)(?:\s+(?:[A-Z][\w'’.&-]*|of|the|and|for|on|upon|in|St\.?|Pauper|Lunatic|Asylum|Mental|Hospital))*\s+"
                     r"(?:Lunatic Asylum|Asylum(?: for the Insane| for Idiots)?|Mental Hospital|Psychiatric Hospital|Hospital|Institution|Colony|House|Home|Retreat))")


def names_in(text):
    out = []
    for m in NAMEPAT.finditer(text):
        nm = re.sub(r"^(?:The|the|In|in|As|as|It|Its|When|By|From|and|of)\s+", "", m.group(1)).strip()
        if len(nm.split()) >= 2 and term_of(nm): out.append(nm)
    return out


def renames(text):
    """(name, term, year) for sentences that say a place was renamed, became or was known as a name, with one year."""
    out = []
    for s in re.split(r"(?<=[a-z0-9\)])\.\s+", text):
        if not re.search(r"renamed|became|known as|changed its name|name was changed|retitled|re-named|opened as|opened in \d{4} as|originally|formerly|was called", s, re.I): continue
        ys = sorted(set(years(s)))
        for nm in names_in(s):
            out.append((nm, term_of(nm), ys[0] if len(ys) == 1 else None))
    return out


CAPW = r"(?:accommodat\w*|capacity|cater(?:ed|ing)? for|designed (?:for|to (?:hold|house|take|accommodate))|to (?:hold|house|take)|housed|housing|home to|held|provid\w* (?:for )?|provision for|contained|peak\w*|height|heyday|there were|had(?: over| around| some| about| almost)?|population of|with(?: over| around)?|beds for|room for|over|for)"
NEGW = r"killed|died|deaths?|moved|transferred|records|admitted|incident|outbreak|evacuat|discharged|relocated|took in|census|analysis|of the|were found"


def beds_of(r):
    """Infobox beds, and the largest capacity the text states ('accommodation for 1,700 patients', 'had 2,000 beds')."""
    v = r["f"].get("beds", "")
    ib = first_int(plain(v))
    ib = ib if ib and 5 <= ib <= 6000 else None
    txt = r["lead"] + " " + r["body"]; best = None
    for m in re.finditer(r"(?<![\d.£$,])(\d{1,2},\d{3}|\d{2,4})\s+(?:\w+\s+){0,2}?(beds|patients|inmates|residents|lunatics)\b", txt):
        k = int(m.group(1).replace(",", "")); pre = txt[max(0, m.start() - 45):m.start()]
        if not (20 <= k <= 6000) or re.fullmatch(r"1[6-9]\d\d|20[0-2]\d", m.group(1)) and "," not in m.group(1): continue
        post = txt[m.end():m.end() + 25]
        if not re.search(CAPW + r"[^.]{0,25}$", pre, re.I) or re.search(NEGW, pre, re.I) or re.search(r"^\s*(?:had )?(?:died|were buried|were killed|were moved)", post): continue
        if best is None or k > best[0]:
            best = (k, re.sub(r"\s+", " ", txt[max(0, m.start() - 60):m.end() + 20]))
    if best and (ib is None or best[0] > ib): return best[0], "text", best[1], ib
    if ib: return ib, "infobox", plain(v)[:60], ib
    return None, None, None, None


FATE_RX = {"derelict": r"\bderelict|\bdisused\b|\babandoned (?:site|buildings?|complex|hospital|asylum|since|after|in \d)|\bleft (?:empty|abandoned|derelict)|\blies empty|\bstands? empty|\bremain(?:s|ed)? (?:empty|derelict|disused|vacant)|\b(?:lies|stands?|remain\w*|left) vacant|\bvacant (?:since|for)|\bin ruins\b|\bnow a ruin|\bruins of the\b|boarded up|fell into disrepair",
           "homes": r"(?:flats|apartments|housing (?:estate|development)|\bhousing\b(?!\s+(?:people|patients|the|up|\d|\w+ patients|\w+ people))|"
                    r"\bhomes\b(?! and Communities| England)|residential (?:use|development|accommodation|area|estate|community|properties|housing|"
                    r"apartments|village|units|scheme|purposes|building)|\bhouses\b(?= and|\.|,)|\bdwellings\b|village development|housing scheme)",
           "other": r"\b(?:college|university|faculty|campus|offices|office space|hotel|business park|prison|museum|wedding|film studio|conference|"
                    r"retail|supermarket|nursing home|care home|hospice|leisure|commercial|industrial estate|arboretum|sixth form)\b",
           "demolished": r"\bdemolish\w*|\bpulled down\b|\brazed\b|\bknocked down\b|\bdemolition\b"}
VERB = r"(?:convert\w*|clear\w* the site for|restored and supplemented as|redevelop\w*|developed|turned|now|today|currently|replaced by|make way for|built|being|sold|acquired|occupied by|became|forms?|"
VERB += r"is used as|serves as|home of|re-?opened as|subsequently|since|taken over by|houses|housed)\b[^.]{0,80}?"
CONTEXT = {"homes": VERB, "other": VERB}
NOTHOME = r"\b(?:own|care|nursing|family|children's|staff|official's)\s+$"
PLANS = r"\b(?:plans?|proposals?|planning applications?|proposed|sought bids|bids for|planned)\b"
NOTOTHER = r"School of Nursing|College of Nursing|Nursing and Midwifery|training school|nurses|for the administration|administration offices|Training School"
KEPT = r"\b(?:convert\w*|retained|restored|refurbish\w*|survives?|surviving|remains of the|preserved)\b"


def fate_flags(t):
    """Which fate words the text uses, each with a conversion or present-tense verb in the same clause (homes, other)."""
    fl = {}
    for k, rx in FATE_RX.items():
        pat = (CONTEXT[k] + "(?:" + rx + ")") if k in CONTEXT else rx
        for m in re.finditer(pat, t, re.I):
            seg = m.group(0)
            if k == "homes":
                noun = list(re.finditer(rx, t[m.start():m.end() + 12], re.I))
                if noun and re.search(NOTHOME, seg[:noun[-1].start()], re.I): continue
                if re.search(PLANS, t[max(0, m.start() - 60):m.end()], re.I): fl.setdefault("plans", seg); continue
            if k == "other" and re.search(NOTOTHER, seg, re.I): continue
            fl[k] = t[max(0, m.start() - 40):m.end() + 40].replace("\n", " "); break
    return fl


def heritage(r):
    t = r["lead"] + " " + r["body"] + " " + " ".join(v for k, v in r["f"].items() if k.startswith("designation"))
    m = re.search(r"\blisted at Grade I{1,2}\*?|\b(Grade (?:I{1,2}\*?|II\*)|Category [ABC]|[AB]\+?)[- ]listed|\blisted building|\bis listed\b|\blisted as\b|Grade II listed|scheduled monument", t)
    g = None
    if m:
        s = m.group(0)
        g = "Grade I" if re.search(r"Grade I\b(?!I)", s) else "Grade II*" if "II*" in s else "Grade II" if "Grade II" in s else \
            ("Category " + re.search(r"Category ([ABC])", s).group(1)) if "Category" in s else "listed"
        return g, "text"
    for c in r["cats"]:
        mm = re.search(r"(Grade I{1,2}\*?|Category [ABC]) listed", c)
        if mm: return mm.group(1), "category"
    return None, None


out = []
for r in rows:
    f, lead, body = r["f"], r["lead"], r["body"]
    # coordinates: infobox or text {{coord}}, else the API's
    c = coord(f.get("coordinates", "")) or coord(PG[r["title"]]["head"])
    src = "wikitext"
    if not c and PG[r["title"]].get("coords"):
        a = PG[r["title"]]["coords"][0]; c = (a["lat"], a["lon"]); src = "api"
    if not c: src = None
    o = {"title": r["title"], "revid": r["revid"], "wikidata": r["wikidata"], "lat": c[0] if c else None, "lon": c[1] if c else None, "coord_src": src}
    o["rule"] = "".join(k for k in "ABC" if r[k])
    # opened
    op = yr_field(f.get("founded")) or yr_field(f.get("opened")) or yr_field(f.get("constructed")); osrc = "infobox"
    if not op: op = lead_year(lead, r"opened|established|founded|built|completed|admitted its first"); osrc = "lead"
    if not op: op = lead_year(body, r"opened|admitted its first patients|received its first patients", subject=True); osrc = "text"
    if not op: op = cat_year(r["cats"], r"^Category:(1[6-9]\d\d|20[0-2]\d) establishments in"); osrc = "category"
    o["opened"], o["opened_src"] = (op, osrc) if op else (None, None)
    # closed
    cv = raw(f.get("closed", "")); cl = None; csrc = None
    if years(cv): cl, csrc = years(cv)[-1] if re.search(r"fully|finally|completely", cv, re.I) else years(cv)[0], "infobox"
    if not cl:
        cl = lead_year(lead, r"closed|closure|shut") ; csrc = "lead"
    if not cl:
        cl = lead_year(body, r"closed|closed its doors", subject=True); csrc = "text"
    if not cl:
        cl = cat_year(r["cats"], r"^Category:Hospitals disestablished in (1[6-9]\d\d|20[0-2]\d)") or cat_year(r["cats"], r"^Category:(1[6-9]\d\d|20[0-2]\d) disestablishments in"); csrc = "category"
    o["closed"], o["closed_src"] = (cl, csrc) if cl else (None, None)
    if o["closed"] and o["opened"] and o["closed"] < o["opened"]:
        o["closed"], o["closed_src"] = None, None
    present = bool(re.search(r"\b(?:is|remains)\s+(?:an?|the)\s+(?:[\w-]+\s+){0,6}?(?:hospital|facility|unit|centre|center|clinic|institution|service)\b", r["s2"]))
    if present and o["closed_src"] in ("text", "category"):      # a present-tense lead outranks a closing year found in the text
        o["closed"], o["closed_src"] = None, None
    o["open_now"] = int(present and not o["closed"])
    o["status"] = "open" if o["open_now"] else ("closed" if o["closed"] or re.search(r"\bwas an?\b|\bformer\b|\bformerly\b", r["s2"]) else "unknown")
    # beds
    o["beds"], o["beds_src"], o["beds_text"], o["beds_infobox"] = beds_of(r)
    # names
    fn = [x.strip() for x in re.split(r"<br\s*/?>|;|\n|,(?=\s*[A-Z])", plain(f.get("former_names", ""))) if x.strip()]
    rn = renames(lead + ". " + body)
    nm = [r["title"].split(",")[0]] + fn + [x[0] for x in rn] + names_in(sentences(lead, 4))
    seen, names = set(), []
    for x in nm:
        x = re.sub(r"\s+", " ", x).strip(" .'\"")
        if norm(x) not in seen and len(x) < 80: seen.add(norm(x)); names.append(x)
    o["names"] = names
    o["terms"] = sorted({t for t in (term_of(x) for x in names) if t})
    o["renames"] = [[a, b, y] for a, b, y in rn if y]
    o["saint"] = int(bool(re.match(r"(St\.?|Saint)\s", r["title"])))
    # fate
    fl_lead, fl_body = fate_flags(lead), fate_flags(body)
    fl, fsrc = (fl_lead, "lead") if fl_lead else (fl_body, "text") if fl_body else ({}, None)
    if o["open_now"] or re.search(r"continues to (?:provide|operate|serve)|remains (?:a|an|in use as a) (?:\w+ )?(?:hospital|psychiatric)", lead):
        fate = "health"; fsrc = fsrc or "lead"
    else:
        fate = next((k for k in ("homes", "other", "derelict", "demolished") if k in fl), "unknown")
    o["plans"] = int("plans" in fl and fate in ("unknown", "derelict", "demolished"))
    o["fate"], o["fate_src"] = fate, (fsrc if fate != "unknown" else None)
    o["fate_flags"] = sorted(fl)
    o["fate_text"] = fl.get(fate, "") if fate in fl else ""
    o["kept_buildings"] = int(bool(re.search(KEPT, lead + " " + body, re.I)))
    # listed
    o["listed"], o["listed_src"] = heritage(r)
    # kind of institution
    lt = (r["s2"] + " " + r["type"]).lower()
    o["ld"] = int(bool(re.search(r"idiot|imbecile|feeble|mentally handicapped|mental handicap|mentally defective|mental deficiency|learning disab|intellectual disab|epilep|colony", lt)))
    o["secure"] = int(bool(re.search(r"\bsecure\b|criminal lunatic|high[- ]security|special hospital", lt)))
    o["private"] = int(bool(re.search(r"\bprivate\b|independent", lt)))
    o["lead"] = lead[:700]
    out.append(o)

D = pd.DataFrame(out)
# merges (same site)
for a, b in MERGE.items():
    if a in set(D.title) and b in set(D.title):
        ia, ib_ = D.index[D.title == a][0], D.index[D.title == b][0]
        D.at[ib_, "names"] = list(dict.fromkeys(D.at[ib_, "names"] + D.at[ia, "names"]))
        for k in ("opened", "closed", "beds", "lat", "listed"):
            if pd.isna(D.at[ib_, k]) or D.at[ib_, k] is None: D.at[ib_, k] = D.at[ia, k]
        D = D[D.title != a]
        dropped.append({"title": a, "reason": f"same site as {b} (merged)", "in_psy_cat": True, "first_sentences": ""})
D = D.reset_index(drop=True)
CHK["kept"] = len(D)
CHK["dropped"] = collections.Counter(x["reason"] for x in dropped)
D.to_pickle(f"{WORK}/places.pkl")
pd.DataFrame(dropped).to_csv(f"{DATA}/excluded.csv", index=False)
jsave(CHK, f"{WORK}/checks.json", indent=1)
print("kept", len(D), "dropped", len(dropped), dict(CHK["dropped"]))
print("located", D.lat.notna().sum(), "opened", D.opened.notna().sum(), "closed", D.closed.notna().sum(), "open now", D.open_now.sum(), "beds", D.beds.notna().sum())
print(D.fate.value_counts().to_dict(), D.fate_src.value_counts().to_dict())
print("listed", D.listed.notna().sum(), D.listed.value_counts().to_dict())
