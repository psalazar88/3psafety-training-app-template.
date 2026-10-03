#!/usr/bin/env python3
"""
3P Safety - Google Takeout contact sorter
=========================================

Reads a Google Takeout export (Gmail .mbox + Google Contacts .csv/.vcf) on YOUR
computer and builds one spreadsheet with every person you have emailed or saved,
tagged by service line (Inspections / Training / Staffing).

Nothing is uploaded anywhere. Only the summary spreadsheet is written; email
bodies are never saved to the output.

Usage:
    Windows:  python  sort_takeout.py "C:\\Users\\you\\Downloads\\Takeout"
    Mac:      python3 sort_takeout.py ~/Downloads/Takeout

Output (written next to this script):
    3P_master_contacts.csv   one row per person, sorted by most recent contact
    3P_companies.csv         one row per company email domain
"""

import csv
import email
import email.utils
import html
import mailbox
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header

# ---------------------------------------------------------------- settings
MY_DOMAINS = {"3psafety.net"}          # treated as "me" / internal
MY_EXTRA_ADDRESSES = set()             # add other personal addresses you send from
MAX_BODY_CHARS = 20000                 # how much of each email to scan for keywords
RECENT_YEARS = 2                       # "within last N years" flag

KEYWORDS = {
    "inspections": [
        r"\binspection", r"\binspect\b", r"load test", r"post[- ]assembly", r"annual crane",
        r"quarterly (crane|inspection)", r"frequent inspection", r"periodic inspection",
        r"\bLOLER\b", r"1910\.179", r"1910\.180", r"1926\.1412", r"wire rope", r"hoist inspection",
        r"certificate of inspection", r"\bCOI\b", r"tower crane", r"buck hoist",
    ],
    "training": [
        r"\bNCCCO\b", r"\bCCO\b", r"\btraining\b", r"\bclass(es)?\b", r"\bcourse\b", r"\brigger\b",
        r"signal ?person", r"\bforklift\b", r"\bOSHA ?(10|30)\b", r"train[- ]the[- ]trainer", r"\bTTT\b",
        r"\boperator (training|certification|evaluation)", r"\bcertification\b", r"\brecert",
        r"practical exam", r"written exam", r"\bMEWP\b", r"aerial lift", r"qualif(y|ied|ication)",
        r"\bstudents?\b", r"\broster\b",
    ],
    "staffing": [
        r"\bstaffing\b", r"\bplacement\b", r"\btemp(orary)? (operator|labor|worker)", r"\bcrew\b",
        r"operators? (needed|available|for hire)", r"\bhourly rate\b", r"\bper hour\b", r"\btimesheet",
        r"\bmanpower\b", r"\bjob site\b.*\boperator", r"\bcontract labor\b", r"\bresume\b",
    ],
}
KW = {k: re.compile("|".join(v), re.I) for k, v in KEYWORDS.items()}

PERSONAL = re.compile(
    r"@(gmail|yahoo|hotmail|aol|outlook|icloud|comcast|att|bellsouth|live|msn|me|ymail|"
    r"sbcglobal|verizon|charter|cox|earthlink|protonmail|mail)\.", re.I)
JUNK_ADDR = re.compile(
    r"(no-?reply|do-?not-?reply|mailer-daemon|postmaster|notification|newsletter|bounce|"
    r"unsubscribe|marketing|alerts?@|news@|info@.*(mail|email)\.|support@|billing@|receipts?@|"
    r"@.*\.(hubspot|mailchimp|sendgrid|mcsv|constantcontact|salesforce)\.)", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+'\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?\(?\b([2-9]\d{2})\)?[\s.\-]*([2-9]\d{2})[\s.\-]*(\d{4})\b")


# ---------------------------------------------------------------- helpers
def dec(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)


def norm_phone(s):
    m = PHONE_RE.search(s or "")
    return f"({m.group(1)}) {m.group(2)}-{m.group(3)}" if m else ""


def is_me(addr):
    addr = addr.lower()
    return addr in MY_EXTRA_ADDRESSES or addr.split("@")[-1] in MY_DOMAINS


def msg_date(msg):
    try:
        d = email.utils.parsedate_to_datetime(msg.get("Date"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


def body_text(msg):
    """Plain text of the message (first MAX_BODY_CHARS)."""
    parts, htmls = [], []
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() == "multipart":
            continue
        if (part.get("Content-Disposition") or "").lower().startswith("attachment"):
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        try:
            payload = part.get_payload(decode=True) or b""
            text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        (parts if ctype == "text/plain" else htmls).append(text)
        if sum(map(len, parts)) > MAX_BODY_CHARS:
            break
    if parts:
        text = "\n".join(parts)
    else:
        text = re.sub(r"<(script|style).*?</\1>", " ", "\n".join(htmls), flags=re.S | re.I)
        text = html.unescape(re.sub(r"<br\s*/?>|</p>|</div>", "\n", text, flags=re.I))
        text = re.sub(r"<[^>]+>", " ", text)
    return text[:MAX_BODY_CHARS]


def own_text(body):
    """Drop quoted replies so keywords/phones come from this message only."""
    out = []
    for line in body.splitlines():
        if line.startswith(">") or re.match(r"\s*On .{5,80} wrote:\s*$", line) \
                or re.match(r"\s*-+ ?Original Message ?-+", line, re.I) or re.match(r"\s*From: .+@", line):
            break
        out.append(line)
    return "\n".join(out)


def signature_phone(body):
    lines = [l for l in own_text(body).splitlines() if l.strip()][-15:]
    for l in reversed(lines):
        if re.search(r"fax", l, re.I):
            continue
        p = norm_phone(l)
        if p:
            return p
    return ""


# ---------------------------------------------------------------- data
def new_person():
    return {
        "name": "", "company": "", "phone": "", "sources": set(),
        "first": None, "last": None, "sent_to": 0, "received_from": 0, "bulk": 0,
        "inspections": 0, "training": 0, "staffing": 0,
        "last_inspections": None, "last_training": None, "last_staffing": None,
    }


people = defaultdict(new_person)
phone_only = {}


def touch(addr, name, when, direction, cats, bulk=False, phone=""):
    addr = addr.lower().strip(".")
    if is_me(addr) or JUNK_ADDR.search(addr):
        return
    p = people[addr]
    p["sources"].add("gmail")
    if name and not p["name"] and "@" not in name:
        p["name"] = name.strip().strip('"')
    if phone and not p["phone"]:
        p["phone"] = phone
    if when:
        p["first"] = when if not p["first"] or when < p["first"] else p["first"]
        p["last"] = when if not p["last"] or when > p["last"] else p["last"]
    p["sent_to" if direction == "out" else "received_from"] += 1
    if bulk:
        p["bulk"] += 1
    for c in cats:
        p[c] += 1
        key = "last_" + c
        if when and (not p[key] or when > p[key]):
            p[key] = when


# ---------------------------------------------------------------- mbox
def process_mbox(path):
    print(f"\nReading mail: {path}")
    n = 0
    box = mailbox.mbox(path, create=False)
    for msg in box:
        n += 1
        if n % 2000 == 0:
            print(f"  {n:,} emails processed...", flush=True)
        try:
            labels = (msg.get("X-Gmail-Labels") or "").lower()
            if "spam" in labels:
                continue
            frm_name, frm = email.utils.parseaddr(dec(msg.get("From")))
            if not frm:
                continue
            when = msg_date(msg)
            subject = dec(msg.get("Subject"))
            body = body_text(msg)
            text = subject + "\n" + own_text(body)
            cats = [k for k, rx in KW.items() if rx.search(text)]
            bulk = bool(msg.get("List-Unsubscribe") or (msg.get("Precedence") or "").lower() in ("bulk", "list"))
            if is_me(frm):
                rcpts = email.utils.getaddresses(
                    [dec(msg.get(h)) for h in ("To", "Cc", "Bcc") if msg.get(h)])
                for name, addr in rcpts:
                    if "@" in addr:
                        touch(addr, name, when, "out", cats)
            else:
                touch(frm, frm_name, when, "in", cats, bulk=bulk, phone=signature_phone(body))
        except Exception as e:  # keep going on odd messages
            if n < 20:
                print("  skipped one message:", e)
    print(f"  done: {n:,} emails")
    return n


# ---------------------------------------------------------------- contacts
def col(row, *needles):
    for k, v in row.items():
        if k and v and all(x.lower() in k.lower() for x in needles):
            yield v


def process_contacts_csv(path):
    print(f"\nReading contacts: {path}")
    n = 0
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            n += 1
            name = " ".join(x for x in [row.get("First Name") or row.get("Given Name") or "",
                                        row.get("Last Name") or row.get("Family Name") or ""] if x).strip() \
                or row.get("Name") or ""
            org = next(col(row, "organization", "name"), "") or next(col(row, "company"), "")
            emails = [e.lower() for v in col(row, "e-mail", "value") for e in EMAIL_RE.findall(v)]
            phones = [norm_phone(x) for v in col(row, "phone", "value") for x in v.split(":::")]
            phones = [p for p in phones if p]
            add_contact(name, org, emails, phones)
    print(f"  done: {n:,} contacts")


def process_vcf(path):
    print(f"\nReading contacts: {path}")
    text = open(path, encoding="utf-8", errors="replace").read()
    for card in text.split("BEGIN:VCARD")[1:]:
        name = (re.search(r"^FN[^:]*:(.*)$", card, re.M) or [None, ""])[1].strip()
        org = (re.search(r"^ORG[^:]*:(.*)$", card, re.M) or [None, ""])[1].strip().strip(";")
        emails = [e.lower() for e in EMAIL_RE.findall(
            "\n".join(re.findall(r"^EMAIL[^:]*:(.*)$", card, re.M)))]
        phones = [norm_phone(p) for p in re.findall(r"^TEL[^:]*:(.*)$", card, re.M)]
        add_contact(name, org, emails, [p for p in phones if p])


def add_contact(name, org, emails, phones):
    emails = [e for e in emails if not is_me(e)]
    if emails:
        for e in emails:
            p = people[e]
            p["sources"].add("google_contacts")
            p["name"] = p["name"] or name
            p["company"] = p["company"] or org
            if phones and not p["phone"]:
                p["phone"] = phones[0]
    elif phones:
        key = phones[0]
        phone_only.setdefault(key, {"name": name, "company": org, "phone": key})


# ---------------------------------------------------------------- output
def company_from(addr, p):
    if p["company"]:
        return p["company"]
    if PERSONAL.search(addr):
        return ""
    dom = addr.split("@")[-1].split(".")
    return dom[-2].capitalize() if len(dom) >= 2 else ""


def fmt(d):
    return d.strftime("%Y-%m-%d") if d else ""


def write_outputs(outdir):
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * RECENT_YEARS)
    rows = []
    for addr, p in people.items():
        two_way = p["sent_to"] > 0 and p["received_from"] > 0
        newsletter = p["bulk"] > 0 and p["sent_to"] == 0
        if newsletter:
            continue
        svc = {k: p[k] for k in ("inspections", "training", "staffing")}
        primary = max(svc, key=svc.get) if any(svc.values()) else ""
        rows.append({
            "email": addr,
            "name": p["name"],
            "company": company_from(addr, p),
            "phone": p["phone"],
            "type": "personal email" if PERSONAL.search(addr) else "company email",
            "source": "+".join(sorted(p["sources"])),
            "first_contact": fmt(p["first"]),
            "last_contact": fmt(p["last"]),
            "within_last_2_years": "yes" if p["last"] and p["last"] >= cutoff else ("no" if p["last"] else "unknown"),
            "emails_you_sent": p["sent_to"],
            "emails_they_sent": p["received_from"],
            "two_way_conversation": "yes" if two_way else "no",
            "primary_service": primary,
            "tag_inspections": "yes" if p["inspections"] else "",
            "tag_training": "yes" if p["training"] else "",
            "tag_staffing": "yes" if p["staffing"] else "",
            "inspection_emails": p["inspections"],
            "last_inspection_email": fmt(p["last_inspections"]),
            "training_emails": p["training"],
            "last_training_email": fmt(p["last_training"]),
            "staffing_emails": p["staffing"],
            "last_staffing_email": fmt(p["last_staffing"]),
        })
    for ph, c in phone_only.items():
        rows.append({"email": "", "name": c["name"], "company": c["company"], "phone": ph,
                     "type": "phone only", "source": "google_contacts", "within_last_2_years": "unknown"})
    rows.sort(key=lambda r: r.get("last_contact") or "", reverse=True)
    fields = list(rows[0].keys()) if rows else ["email"]
    for r in rows:
        for k in fields:
            r.setdefault(k, "")

    out = os.path.join(outdir, "3P_master_contacts.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    comps = defaultdict(lambda: {"people": 0, "inspections": 0, "training": 0, "staffing": 0, "last": ""})
    for r in rows:
        if r["type"] != "company email":
            continue
        c = comps[r["email"].split("@")[-1]]
        c["name"] = r["company"]
        c["people"] += 1
        for k, colname in (("inspections", "inspection_emails"), ("training", "training_emails"),
                           ("staffing", "staffing_emails")):
            c[k] += int(r[colname] or 0)
        c["last"] = max(c["last"], r["last_contact"] or "")
    out2 = os.path.join(outdir, "3P_companies.csv")
    with open(out2, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["domain", "company", "people", "inspection_emails", "training_emails",
                    "staffing_emails", "last_contact"])
        for d, c in sorted(comps.items(), key=lambda x: x[1]["last"], reverse=True):
            w.writerow([d, c.get("name", ""), c["people"], c["inspections"], c["training"],
                        c["staffing"], c["last"]])

    recent = sum(1 for r in rows if r["within_last_2_years"] == "yes")
    print("\n================ SUMMARY ================")
    print(f"People total:            {len(rows):,}")
    print(f"  with email:            {sum(1 for r in rows if r['email']):,}")
    print(f"  with phone:            {sum(1 for r in rows if r['phone']):,}")
    print(f"  contacted last 2 yrs:  {recent:,}")
    print(f"  two-way conversations: {sum(1 for r in rows if r.get('two_way_conversation') == 'yes'):,}")
    for k in ("inspections", "training", "staffing"):
        print(f"  tagged {k:12s}  {sum(1 for r in rows if r.get('tag_' + k)):,}")
    print(f"Companies (domains):     {len(comps):,}")
    print(f"\nSaved: {out}\nSaved: {out2}")
    print("Upload 3P_master_contacts.csv to Claude to merge with your other lists.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    root = os.path.expanduser(sys.argv[1])
    if not os.path.exists(root):
        sys.exit(f"Folder not found: {root}")
    mboxes, csvs, vcfs = [], [], []
    for d, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(d, fn)
            low = fn.lower()
            if low.endswith(".mbox"):
                mboxes.append(p)
            elif low.endswith(".csv") and "contact" in p.lower():
                csvs.append(p)
            elif low.endswith(".vcf"):
                vcfs.append(p)
    if not (mboxes or csvs or vcfs):
        sys.exit("No .mbox or contacts files found. Point this at the unzipped Takeout folder.")
    for p in csvs:
        process_contacts_csv(p)
    for p in vcfs:
        process_vcf(p)
    for p in mboxes:
        process_mbox(p)
    write_outputs(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    main()
