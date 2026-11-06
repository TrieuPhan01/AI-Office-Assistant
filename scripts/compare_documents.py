#!/usr/bin/env python3
"""So sánh nhiều tài liệu (DOCX/PDF/TXT/MD/JSON đã trích xuất) bằng quy tắc xác định (không dùng AI).

Phần máy làm được:
  - Trích thực thể: tên công ty, người/chức danh, địa chỉ, mã số thuế, số hợp đồng/văn bản,
    ngày tháng, số tiền, phần trăm.
  - Đối chiếu chéo giữa các tài liệu và phát hiện khác biệt / nghi gõ nhầm.
  - Kiểm tra số học: số tiền bằng số vs bằng chữ, SL x Đơn giá = Thành tiền, tổng bảng, thuế VAT.
  - Kiểm tra logic ngày: ngày kết thúc < hiệu lực, hiệu lực < ngày ký, ngày không tồn tại.
Phần cần Claude: ngữ nghĩa, mâu thuẫn điều khoản, loại bỏ cảnh báo sai (ví dụ hai bên khác nhau).

Kết quả: JSON {files, inventory, findings, stats}. Mỗi finding có category:
  certain (lỗi chắc chắn) | verify (khác biệt cần xác minh) | logic (cảnh báo logic) | suggestion (đề xuất).

Ví dụ:
  python scripts/compare_documents.py workspace/input/*.docx -o workspace/output/audit_raw.json
"""
import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_docx  # noqa: E402
import extract_pdf  # noqa: E402

SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
CAT_ORDER = {"certain": 0, "verify": 1, "logic": 2, "suggestion": 3}


# ===================== tiện ích chuỗi / số =====================
def nfc(s):
    return unicodedata.normalize("NFC", s)


def fold(s):
    """Bỏ dấu tiếng Việt + chữ thường, để so sánh 'thiếu dấu'."""
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()


def norm_key(s):
    s = nfc(s).casefold()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def levenshtein(a, b):
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def digit_typo(a, b):
    """Hai chuỗi số có vẻ là gõ nhầm của nhau (sai/thiếu/thừa 1 chữ số hoặc đổi chỗ 2 chữ số kề nhau)."""
    a, b = str(a), str(b)
    if a == b or min(len(a), len(b)) < 4:
        return False
    if levenshtein(a, b) <= 1:
        return True
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]
    return False


def transposed(a, b):
    """Hai chuỗi số khác nhau đúng do đảo chỗ 2 chữ số kề nhau (vd 150000000 và 105000000)."""
    a, b = str(a), str(b)
    if len(a) != len(b) or len(a) < 5:
        return False
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]


def parse_number(s):
    """Đọc số kiểu Việt Nam/quốc tế: '1.234.567', '1,234,567', '1.234,5'. Trả về float hoặc None."""
    s = re.sub(r"[^\d.,]", "", s or "")
    if not s or not re.search(r"\d", s):
        return None
    if "." in s and "," in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        thou = "." if dec == "," else ","
        s = s.replace(thou, "").replace(dec, ".")
    elif re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


_UNITS = {"không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "lăm": 5,
          "nhăm": 5, "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9}
_BIG = {"nghìn": 10 ** 3, "ngàn": 10 ** 3, "triệu": 10 ** 6, "tỷ": 10 ** 9, "tỉ": 10 ** 9}


def words_to_number(text):
    """'một trăm năm mươi triệu đồng' -> 150000000. Trả về None nếu có từ lạ."""
    t = nfc(text).lower()
    t = re.sub(r"[,.;:()]", " ", t)
    t = re.sub(r"\b(đồng|chẵn|việt nam|vnđ|vnd|bằng chữ|viết bằng chữ|đ)\b", " ", t)
    total = group = 0
    digit = None
    seen = False
    for tok in t.split():
        if tok in _UNITS:
            digit, seen = _UNITS[tok], True
        elif tok == "mười":
            group += 10
            seen = True
        elif tok == "mươi":
            group += (digit if digit is not None else 1) * 10
            digit, seen = None, True
        elif tok == "trăm":
            group += (digit if digit is not None else 1) * 100
            digit, seen = None, True
        elif tok in ("linh", "lẻ"):
            continue
        elif tok in _BIG:
            group += digit or 0
            digit = None
            total += (group or 1) * _BIG[tok]
            group, seen = 0, True
        else:
            return None
    group += digit or 0
    return total + group if seen else None


# ===================== nạp tài liệu =====================
def load(path):
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".docx":
        data = extract_docx.extract(p)
    elif ext == ".pdf":
        data = extract_pdf.extract(p)
    elif ext == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("file", p.name)
    elif ext in (".txt", ".md"):
        blocks = [{"id": f"L{i}", "kind": "line", "loc": f"Dòng {i}", "text": ln.strip()}
                  for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if ln.strip()]
        data = {"file": p.name, "type": "text", "blocks": blocks, "tables": []}
    else:
        raise ValueError(f"Định dạng chưa hỗ trợ: {ext}")
    for b in data.get("blocks", []):
        b["text"] = nfc(b["text"])
    return data


# ===================== trích thực thể =====================
LABELS_MONEY = [
    ("tax", r"thuế|vat|gtgt"),
    ("deposit", r"đặt cọc|tạm ứng|bảo đảm|bảo lãnh|bảo lãnh"),
    ("unit_price", r"đơn giá"),
    ("line_amount", r"thành tiền"),
    ("total", r"tổng|giá trị hợp đồng|giá trị thanh toán|cộng tiền"),
]
LABELS_DATE = [
    ("end", r"kết thúc|hết hạn|đến ngày|chấm dứt|đáo hạn|hết hiệu lực"),
    ("effective", r"hiệu lực|bắt đầu|từ ngày|có hiệu lực"),
    ("sign", r"\bký\b|lập tại|ban hành|làm tại|ngày ký"),
]
LABELS_PCT = [("vat", r"thuế|vat|gtgt"), ("penalty", r"phạt|lãi"), ("deposit", r"cọc|tạm ứng"),
              ("discount", r"chiết khấu|giảm giá")]
LABEL_VN = {"tax": "thuế", "deposit": "đặt cọc/tạm ứng", "unit_price": "đơn giá", "line_amount": "thành tiền",
            "total": "tổng giá trị", "sign": "ngày ký/ban hành", "effective": "ngày hiệu lực",
            "end": "ngày kết thúc", "vat": "thuế suất VAT", "penalty": "phạt/lãi", "discount": "chiết khấu"}

MONEY_RE = re.compile(r"(?<![\d.,/\-])(\d{1,3}(?:[.,]\d{3})+|\d{5,})(?!\d)(?:\s*(đồng|VNĐ|VND|đ(?![a-zà-ỹ])|USD|\$))?",
                      re.I)
DATE_NUM = re.compile(r"(?<![\d/.\-])(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})(?![\d])")
DATE_VN = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.I)
PCT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
TAX_RE = re.compile(r"(?:mã\s*số\s*thuế|\bMST\b|M\.S\.T)\s*(?:\(MST\))?\s*[:\-]?\s*(\d[\d\s\-.]{8,16}\d)", re.I)
DOCNO_RE = [
    re.compile(r"(hợp đồng|HĐ|phụ lục|biên bản|quyết định|công văn|văn bản|tờ trình)\s*(?:số|No\.?)\s*[:\-]?\s*"
               r"([0-9A-Za-zĐđ][0-9A-Za-zĐđ/\-._]*[0-9A-Za-zĐđ])", re.I),
    re.compile(r"(?<!\w)(Số)\s*[:\-]?\s*(\d+[/\-][0-9A-Za-zĐđ/\-._]*[0-9A-Za-zĐđ])"),
]
COMPANY_RE = re.compile(r"((?:CÔNG TY|Công ty|TẬP ĐOÀN|Tập đoàn)\s+[^\n,;:()\[\]|]{3,90})")
COMPANY_STOP = re.compile(r"\s+(?:có trụ sở|trụ sở|có địa chỉ|địa chỉ|mã số|MST|sau đây|gọi là|do ông|do bà|đại diện|được|và)"
                          r"(?=[\s:]|$)|\s[-–—]\s", re.I)
LEGAL_FORM = re.compile(r"tnhh|cổ phần|\bcp\b|mtv|hợp danh|tư nhân|tập đoàn", re.I)
PERSON_RE = re.compile(r"\b(?:Ông|Bà|ÔNG|BÀ)\s*:?\s+(.{3,70})")
TITLE_RE = re.compile(r"(?:Chức vụ|Chức danh)\s*:\s*([^\n,;|]{2,50})", re.I)
ADDR_RE = re.compile(r"Địa chỉ(?:\s*trụ sở)?(?:\s*chính)?\s*:\s*([^\n;|]{8,170})", re.I)
ADDR_STOP = re.compile(r"\s*,?\s*(?:Điện thoại|ĐT|SĐT|MST|Mã số thuế|Email|Fax|Tel)\b.*$", re.I)
WORDS_RE = re.compile(r"(?:bằng chữ|viết bằng chữ)\s*[:\-]?\s*(.+?)(?:[.;]\s|[.;]?$|\))", re.I)


def _label(prefix, table):
    best, best_end = None, -1
    for name, rx in table:
        for m in re.finditer(rx, prefix, re.I):
            if m.end() > best_end:
                best, best_end = name, m.end()
    return best


def _ctx(text, a, b, pad=45):
    s = text[max(0, a - pad):min(len(text), b + pad)].replace("\n", " ")
    return ("…" if a - pad > 0 else "") + s + ("…" if b + pad < len(text) else "")


def extract_entities(doc):
    """Trả về danh sách thực thể của một tài liệu."""
    name = doc["file"]
    ents, last_money = [], None
    blocks = doc.get("blocks", [])
    for bi, b in enumerate(blocks):
        text, loc = b["text"], b["loc"]
        masked = text

        def add(typ, raw, norm, a, z, label=None, **extra):
            ents.append(dict(doc=name, type=typ, raw=raw.strip(), norm=norm, label=label, loc=loc,
                             ctx=_ctx(text, a, z), **extra))

        # --- mã số thuế (che đi để không bị nhận nhầm là số tiền)
        for m in TAX_RE.finditer(text):
            raw = re.sub(r"[\s.]", "", m.group(1))
            add("tax_code", raw, raw, m.start(), m.end())
            masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
        # --- số hợp đồng / số văn bản
        for rx in DOCNO_RE:
            for m in rx.finditer(text):
                val = m.group(2).strip("-_./")
                if not re.search(r"\d", val) or not re.search(r"[/\-]", val):
                    continue
                kind = nfc(m.group(1)).casefold()
                label = "hop_dong" if kind in ("hợp đồng", "hđ") else "so" if kind == "số" else kind.replace(" ", "_")
                add("doc_no", m.group(0), val.upper(), m.start(), m.end(), label=label)
                masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
        # --- ngày
        for rx in (DATE_VN, DATE_NUM):
            for m in rx.finditer(text):
                d, mo, y = (int(g) for g in m.groups())
                label = _label(text[max(0, m.start() - 60):m.start()].lower(), LABELS_DATE)
                try:
                    iso = date(y, mo, d).isoformat()
                    valid = True
                except ValueError:
                    iso, valid = f"{y:04d}-{mo:02d}-{d:02d}", False
                add("date", m.group(0), iso, m.start(), m.end(), label=label, valid=valid)
                masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
        # --- số tiền
        block_money = []
        for m in MONEY_RE.finditer(masked):
            has_sep = bool(re.search(r"[.,]", m.group(1)))
            unit = m.group(2)
            if not has_sep and not unit:
                continue  # số trần không kèm đơn vị: bỏ qua (số điện thoại, tài khoản...)
            val = int(re.sub(r"[.,]", "", m.group(1)))
            if val < 1000:
                continue
            cur = "USD" if (unit or "").upper() in ("USD", "$") else "VND"
            label = _label(masked[max(0, m.start() - 70):m.start()].lower(), LABELS_MONEY)
            add("money", m.group(0), str(val), m.start(), m.end(), label=label, currency=cur, pos=m.start())
            block_money.append(ents[-1])
        # --- số tiền bằng chữ (so với số liền trước)
        wm = WORDS_RE.search(text)
        if wm:
            ref = None
            for e in reversed(block_money):
                if e["pos"] < wm.start():
                    ref = e
                    break
            ref = ref or last_money
            val = words_to_number(wm.group(1))
            if ref is not None:
                add("money_words", wm.group(1).strip(), "" if val is None else str(val), wm.start(), wm.end(),
                    ref_value=ref["norm"], ref_raw=ref["raw"], ref_loc=ref["loc"], parsed=val is not None)
        if block_money:
            last_money = block_money[-1]
        # --- phần trăm
        for m in PCT_RE.finditer(text):
            label = _label(text[max(0, m.start() - 50):m.start()].lower(), LABELS_PCT)
            v = parse_number(m.group(1))
            add("percent", m.group(0), f"{v:g}", m.start(), m.end(), label=label)
        # --- công ty
        for m in COMPANY_RE.finditer(text):
            nm = COMPANY_STOP.split(m.group(1), 1)[0].strip(" .-–—")
            letters = [c for c in nm if c.isalpha()]
            upper_ratio = sum(c.isupper() for c in letters) / max(1, len(letters))
            if len(nm.split()) < 3 or not (LEGAL_FORM.search(nm) or upper_ratio >= 0.6):
                continue
            add("company", nm, norm_key(nm).replace(" ", ""), m.start(), m.start() + len(nm))
        # --- người + chức danh
        for m in PERSON_RE.finditer(text):
            words = []
            for w in re.findall(r"[^\W\d_]+", m.group(1)):
                if not w[0].isupper() or len(words) >= 5:
                    break
                words.append(w)
            if len(words) < 2 and not (words and len(words[0]) > 2):
                continue
            person = " ".join(words)
            title = None
            for tb in blocks[bi: bi + 2]:
                seg = tb["text"][m.end():] if tb is b else tb["text"]
                tm = TITLE_RE.search(seg)
                if tm:
                    title = tm.group(1).strip(" .")
                    break
            add("person", person, norm_key(person).replace(" ", ""), m.start(), m.end(), title=title,
                title_key=norm_key(title).replace(" ", "") if title else None)
        # --- địa chỉ
        for m in ADDR_RE.finditer(text):
            addr = ADDR_STOP.sub("", m.group(1)).strip(" .,")
            if len(addr) >= 8:
                add("address", addr, norm_key(addr).replace(" ", ""), m.start(), m.end())
    return ents


# ===================== đối chiếu =====================
class Findings:
    def __init__(self):
        self.items = []
        self._seen = set()

    def add(self, category, severity, error_type, evidence, analysis, suggestion, key=None):
        key = key or (category, error_type, tuple(sorted((e["doc"], e["loc"], e["raw"]) for e in evidence)))
        if key in self._seen:
            return
        self._seen.add(key)
        docs = sorted({e["doc"] for e in evidence})
        fmt = [f"[{e['doc']}] {e['loc']}: {e.get('ctx') or e['raw']}" for e in evidence]
        self.items.append({
            "category": category, "severity": severity, "error_type": error_type, "source": "script",
            "documents": docs, "locations": [f"{e['doc']} – {e['loc']}" for e in evidence],
            "original": fmt[0] if fmt else "", "compare": "\n".join(fmt[1:]),
            "analysis": analysis, "suggestion": suggestion, "evidence": evidence_slim(evidence)})

    def finalize(self):
        self.items.sort(key=lambda f: (CAT_ORDER[f["category"]], SEV_ORDER[f["severity"]]))
        for i, f in enumerate(self.items, 1):
            f["id"] = f"F-{i:03d}"
        return self.items


def evidence_slim(evs):
    return [{k: e.get(k) for k in ("doc", "loc", "raw", "label") if k in e} for e in evs]


def cluster(ents, thr=0.8):
    clusters = []
    for e in ents:
        for c in clusters:
            if any(SequenceMatcher(None, e["norm"], x["norm"]).ratio() >= thr for x in c):
                c.append(e)
                break
        else:
            clusters.append([e])
    return clusters


def pick_per_value(ents):
    """Mỗi giá trị khác nhau lấy 1 bằng chứng (ưu tiên khác tài liệu)."""
    out, seen = [], set()
    for e in ents:
        k = (e["norm"], e["doc"])
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out


def pick_per_raw(ents):
    out, seen = [], set()
    for e in ents:
        k = (e["raw"].replace(" ", ""), e["doc"])
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out


def exclusive(ents, a, b):
    """Hai giá trị a, b không cùng xuất hiện trong một tài liệu nào (nếu cùng nằm trong một tài liệu
    thì đó là hai khoản khác nhau chứ không phải một khoản bị gõ sai)."""
    da = {e["doc"] for e in ents if e["norm"] == a}
    db = {e["doc"] for e in ents if e["norm"] == b}
    return not (da & db)


def check_names(F, ents, kind, vn_name, sev_diff):
    for c in cluster([e for e in ents if e["type"] == kind]):
        by_norm = {}
        for e in c:
            by_norm.setdefault(e["norm"], []).append(e)
        for group in by_norm.values():  # cùng tên nhưng khác hoa/thường
            raws = {e["raw"].replace(" ", "") for e in group}
            if len(raws) > 1 and len({e["doc"] for e in group}) > 1:
                F.add("suggestion", "Low", f"Viết hoa/thường không thống nhất ({vn_name})", pick_per_raw(group),
                      f"Cùng một {vn_name} nhưng cách viết hoa/thường hoặc dấu câu khác nhau giữa các tài liệu.",
                      "Thống nhất theo đúng tên trên giấy đăng ký/giấy tờ pháp lý.")
        norms = set(by_norm)
        if len(norms) < 2:
            continue
        if len({fold(n) for n in norms}) == 1:
            F.add("certain", "Medium", f"Sai/thiếu dấu tiếng Việt ({vn_name})", pick_per_value(c),
                  f"Các cách viết của {vn_name} chỉ khác nhau ở dấu tiếng Việt.",
                  "Chuẩn hóa về một cách viết có dấu đúng.")
            continue
        ratios = [SequenceMatcher(None, a, b).ratio() for a in norms for b in norms if a < b]
        near = min(ratios) >= 0.9
        F.add("certain" if near else "verify", sev_diff, f"{vn_name.capitalize()} khác nhau giữa các tài liệu",
              pick_per_value(c),
              f"Các tài liệu ghi {vn_name} gần giống nhưng không giống hệt (độ tương đồng tối thiểu {min(ratios):.0%}). "
              + ("Khả năng cao là lỗi gõ/viết sai; cần đối chiếu giấy tờ gốc để biết cách viết đúng." if near
                 else "Có thể là hai đối tượng khác nhau – cần xác minh."),
              f"Đối chiếu giấy tờ gốc và thống nhất {vn_name} ở mọi tài liệu.")


def compare_across(all_ents, F):
    by = lambda t: [e for e in all_ents if e["type"] == t]  # noqa: E731
    ndocs = len({e["doc"] for e in all_ents})

    # -- mã số thuế
    taxes = by("tax_code")
    for e in taxes:
        digits = re.sub(r"\D", "", e["norm"])
        if len(digits) not in (10, 13):
            F.add("certain", "Medium", "Mã số thuế sai độ dài", [e],
                  f"MST '{e['raw']}' có {len(digits)} chữ số; MST hợp lệ có 10 hoặc 13 chữ số.",
                  "Kiểm tra lại MST trên giấy đăng ký kinh doanh.")
    vals = sorted({e["norm"] for e in taxes})
    for i, a in enumerate(vals):
        for b in vals[i + 1:]:
            if levenshtein(a, b) <= 2 and exclusive(taxes, a, b):
                F.add("certain", "Critical", "Mã số thuế nghi gõ nhầm giữa các tài liệu",
                      [e for e in taxes if e["norm"] in (a, b)],
                      f"Hai MST '{a}' và '{b}' chỉ khác nhau {levenshtein(a, b)} ký tự – rất có thể là một MST bị gõ sai.",
                      "Đối chiếu MST với giấy đăng ký kinh doanh và sửa lại cho đúng.")
    if ndocs >= 2:
        docs_with = {e["doc"] for e in taxes}
        for v in vals:
            holders = {e["doc"] for e in taxes if e["norm"] == v}
            if len(holders) == 1 and len(docs_with) >= 2 and not any(levenshtein(v, o) <= 2 for o in vals if o != v):
                F.add("verify", "Medium", "Mã số thuế chỉ xuất hiện ở một tài liệu",
                      [e for e in taxes if e["norm"] == v],
                      f"MST {v} chỉ có trong một tài liệu trong khi các tài liệu khác có MST khác. "
                      "Có thể là bên khác nhau, cũng có thể là sai sót.", "Xác minh MST thuộc đối tượng nào.")

    # -- số hợp đồng / văn bản
    nos = by("doc_no")
    vals = sorted({e["norm"] for e in nos})
    for i, a in enumerate(vals):
        for b in vals[i + 1:]:
            if levenshtein(a, b) <= 2 and len(a) >= 6 and exclusive(nos, a, b):
                F.add("certain", "Critical", "Số hợp đồng/số văn bản nghi gõ nhầm",
                      [e for e in nos if e["norm"] in (a, b)],
                      f"'{a}' và '{b}' gần như giống nhau (khác {levenshtein(a, b)} ký tự) – có thể là cùng một số bị ghi sai.",
                      "Đối chiếu với bản gốc/đăng ký số văn bản và thống nhất.")
    hd = [e for e in nos if e["label"] == "hop_dong"]
    hd_vals = sorted({e["norm"] for e in hd})
    if len(hd_vals) > 1 and not any(levenshtein(a, b) <= 2 for a in hd_vals for b in hd_vals if a < b):
        F.add("verify", "High", "Số hợp đồng được dẫn chiếu khác nhau", pick_per_value(hd),
              "Các tài liệu dẫn chiếu tới các số hợp đồng khác nhau: " + ", ".join(hd_vals) + ".",
              "Xác nhận các tài liệu có cùng thuộc một hợp đồng không; nếu có, sửa lại số dẫn chiếu.")

    # -- tên công ty / người / địa chỉ
    check_names(F, all_ents, "company", "tên công ty", "High")
    check_names(F, all_ents, "person", "tên người", "High")
    check_names(F, all_ents, "address", "địa chỉ", "Medium")
    # chức danh của cùng một người
    persons = [e for e in by("person") if e.get("title_key")]
    for c in cluster(persons, 0.9):
        titles = {e["title_key"] for e in c}
        if len(titles) > 1:
            F.add("verify", "High", "Chức danh của cùng một người khác nhau", pick_per_value(c),
                  "Cùng một người nhưng chức danh ghi khác nhau: " + "; ".join(sorted({e["title"] for e in c})) + ".",
                  "Xác nhận chức danh đúng (theo quyết định bổ nhiệm/giấy ủy quyền) và thống nhất.")

    # -- số tiền theo nhãn
    money = [e for e in by("money")]
    for label in ("total", "tax", "deposit"):
        group = [e for e in money if e["label"] == label]
        for cur in ("VND", "USD"):
            g = [e for e in group if e["currency"] == cur]
            docs = {e["doc"] for e in g}
            vals = sorted({int(e["norm"]) for e in g})
            if len(docs) >= 2 and len(vals) > 1:
                near = any(digit_typo(a, b) for a in vals for b in vals if a < b)
                per_doc = {d: sorted({int(e["norm"]) for e in g if e["doc"] == d}) for d in docs}
                if all(set(per_doc[docs_a]) <= set(per_doc[docs_b]) or set(per_doc[docs_b]) <= set(per_doc[docs_a])
                       for docs_a in docs for docs_b in docs):
                    continue  # tập giá trị lồng nhau: không coi là khác biệt
                sev = "Critical" if (near and label == "total") else "High"
                F.add("certain" if near else "verify", sev, f"Số tiền ({LABEL_VN[label]}) khác nhau giữa các tài liệu",
                      pick_per_value(g),
                      f"Các tài liệu ghi {LABEL_VN[label]} khác nhau: "
                      + "; ".join(f"{d}: {', '.join(f'{v:,}'.replace(',', '.') for v in vs)}" for d, vs in sorted(per_doc.items()))
                      + (". Hai giá trị chỉ khác một chữ số/đổi chỗ chữ số → nghi gõ nhầm." if near else "."),
                      "Đối chiếu hợp đồng/phụ lục/báo giá gốc để xác định số tiền đúng và thống nhất.")
    # hai số tiền khác nhau do đảo chỗ 2 chữ số kề nhau, nằm ở các tài liệu khác nhau (bỏ qua nếu đã được
    # nhóm tổng/thuế/cọc ở trên xử lý)
    allv = sorted({(int(e["norm"]), e["currency"]) for e in money})
    for i, (a, ca) in enumerate(allv):
        for b, cb in allv[i + 1:]:
            if ca != cb or not transposed(a, b):
                continue
            ea = [e for e in money if int(e["norm"]) == a and e["currency"] == ca]
            eb = [e for e in money if int(e["norm"]) == b and e["currency"] == ca]
            if {e["doc"] for e in ea} & {e["doc"] for e in eb}:
                continue
            la, lb = {e["label"] for e in ea}, {e["label"] for e in eb}
            if la == lb and len(la) == 1 and None not in la:
                continue
            F.add("verify", "Medium", "Hai số tiền chỉ khác nhau do đảo chữ số ở các tài liệu khác nhau",
                  pick_per_value(ea + eb),
                  f"{a:,} và {b:,} chỉ khác nhau do đảo chỗ hai chữ số kề nhau – có thể là cùng một khoản bị gõ sai."
                  .replace(",", "."), "Kiểm tra từng khoản và thống nhất.")

    # -- ngày theo nhãn
    dates = by("date")
    for e in dates:
        if not e["valid"]:
            F.add("certain", "High", "Ngày không tồn tại", [e],
                  f"'{e['raw']}' không phải ngày hợp lệ trong lịch.", "Sửa lại ngày cho đúng.")
    for label in ("sign", "effective", "end"):
        g = [e for e in dates if e["label"] == label and e["valid"]]
        docs = {e["doc"] for e in g}
        vals = sorted({e["norm"] for e in g})
        if len(docs) >= 2 and len(vals) > 1:
            F.add("verify", "High", f"{LABEL_VN[label].capitalize()} khác nhau giữa các tài liệu", pick_per_value(g),
                  f"Các tài liệu ghi {LABEL_VN[label]} khác nhau: {', '.join(vals)}.",
                  "Xác định ngày đúng theo hợp đồng chính và thống nhất.")

    # -- phần trăm theo nhãn
    pcts = by("percent")
    for label in ("vat", "penalty", "deposit", "discount"):
        g = [e for e in pcts if e["label"] == label]
        docs = {e["doc"] for e in g}
        vals = sorted({float(e["norm"]) for e in g})
        if len(docs) >= 2 and len(vals) > 1:
            F.add("verify", "High" if label == "vat" else "Medium", f"Tỷ lệ % ({LABEL_VN[label]}) khác nhau",
                  pick_per_value(g), f"Các tài liệu ghi {LABEL_VN[label]} khác nhau: "
                  + ", ".join(f"{v:g}%" for v in vals) + ".", "Xác minh tỷ lệ đúng và thống nhất.")


def check_within_doc(doc, ents, F):
    """Kiểm tra bên trong từng tài liệu: bằng chữ, logic ngày."""
    for e in ents:
        if e["type"] == "money_words":
            if not e["parsed"]:
                F.add("verify", "Low", "Không đọc được số tiền bằng chữ", [e],
                      f"Không quy đổi được '{e['raw']}' sang số để đối chiếu với {e['ref_raw']}.",
                      "Kiểm tra bằng mắt thường số tiền bằng chữ.")
            elif e["norm"] != e["ref_value"]:
                a, b = int(e["ref_value"]), int(e["norm"])
                F.add("certain", "Critical", "Số tiền bằng số và bằng chữ không khớp", [e],
                      f"Bằng số: {a:,} nhưng bằng chữ tương ứng {b:,} ('{e['raw']}'). Chênh lệch {abs(a - b):,}."
                      .replace(",", "."), "Xác định số tiền đúng và sửa lại cho khớp.")
    dts = {}
    for e in ents:
        if e["type"] == "date" and e["valid"] and e["label"]:
            dts.setdefault(e["label"], []).append(e)
    if dts.get("end") and dts.get("effective"):
        s, t = min(dts["effective"], key=lambda x: x["norm"]), max(dts["end"], key=lambda x: x["norm"])
        if t["norm"] < s["norm"]:
            F.add("logic", "High", "Ngày kết thúc trước ngày hiệu lực", [s, t],
                  f"Ngày hiệu lực {s['norm']} muộn hơn ngày kết thúc {t['norm']}.", "Kiểm tra lại thời hạn.")
    if dts.get("effective") and dts.get("sign"):
        sg, ef = min(dts["sign"], key=lambda x: x["norm"]), min(dts["effective"], key=lambda x: x["norm"])
        if ef["norm"] < sg["norm"]:
            F.add("logic", "Medium", "Ngày hiệu lực sớm hơn ngày ký", [sg, ef],
                  f"Hiệu lực từ {ef['norm']} nhưng ký ngày {sg['norm']}: có thể là hồi tố có chủ đích hoặc sai sót.",
                  "Xác nhận có chủ đích; nếu không, sửa ngày.")


def check_tables(doc, F):
    name = doc["file"]
    TOL = 1.0
    for t in doc.get("tables", []):
        rows = t["rows"]
        if len(rows) < 2:
            continue
        hdr_i, cols = None, {}
        for i, r in enumerate(rows[:4]):
            low = [c.casefold() for c in r]
            for key, rx in (("qty", r"số lượng|khối lượng|\bsl\b"), ("price", r"đơn giá"), ("amount", r"thành tiền")):
                for j, c in enumerate(low):
                    if re.search(rx, c):
                        cols.setdefault(key, j)
            if cols:
                hdr_i = i
                break
        if hdr_i is None:
            continue

        def ev(ri, text=None):
            return {"doc": name, "loc": f"Bảng {t['id'][1:]}, hàng {ri + 1}", "raw": " | ".join(rows[ri]),
                    "ctx": " | ".join(rows[ri])}

        summary_rx = re.compile(r"^\s*(cộng|tổng|thuế|vat|gtgt|chiết khấu|giảm giá)", re.I)
        lines, summaries = [], []
        for ri in range(hdr_i + 1, len(rows)):
            first = next((c for c in rows[ri] if c), "")
            (summaries if summary_rx.match(first) else lines).append(ri) if first else None
        amt_col = cols.get("amount")
        # SL x ĐG = TT
        if {"qty", "price", "amount"} <= set(cols):
            for ri in lines:
                r = rows[ri]
                try:
                    q, p, a = (parse_number(r[cols[k]]) for k in ("qty", "price", "amount"))
                except IndexError:
                    continue
                if None not in (q, p, a) and abs(q * p - a) > TOL:
                    F.add("certain", "High", "Thành tiền ≠ Số lượng × Đơn giá", [ev(ri)],
                          f"{q:g} × {p:,.0f} = {q * p:,.0f} nhưng bảng ghi thành tiền {a:,.0f} (chênh {abs(q * p - a):,.0f})."
                          .replace(",", "."), "Tính lại và sửa số liệu.")
        # tổng / thuế
        if amt_col is None:
            continue
        vals = []
        for ri in lines:
            try:
                v = parse_number(rows[ri][amt_col])
            except IndexError:
                v = None
            if v is not None:
                vals.append(v)
        line_sum = sum(vals) if vals else None

        def cell_val(ri):
            try:
                v = parse_number(rows[ri][amt_col])
                if v is not None:
                    return v
            except IndexError:
                pass
            nums = [parse_number(c) for c in rows[ri][1:]]
            nums = [n for n in nums if n is not None]
            return nums[-1] if nums else None

        subtotal, vat = None, None
        for ri in summaries:
            label = next((c for c in rows[ri] if c), "").casefold()
            v = cell_val(ri)
            if v is None:
                continue
            if re.search(r"thuế|vat|gtgt", label):
                pm = re.search(r"(\d+(?:[.,]\d+)?)\s*%", " ".join(rows[ri]))
                base = subtotal if subtotal is not None else line_sum
                if pm and base is not None:
                    exp = base * parse_number(pm.group(1)) / 100
                    if abs(exp - v) > max(TOL, 1.0):
                        F.add("certain", "High", "Thuế VAT tính sai", [ev(ri)],
                              f"{pm.group(0)} × {base:,.0f} = {exp:,.0f} nhưng bảng ghi {v:,.0f}.".replace(",", "."),
                              "Tính lại thuế hoặc kiểm tra thuế suất/cơ sở tính thuế.")
                vat = v
            elif subtotal is None and vat is None and line_sum is not None:
                subtotal = v
                if abs(line_sum - v) > TOL:
                    F.add("certain", "High", "Tổng bảng không bằng tổng các dòng", [ev(ri)],
                          f"Tổng các dòng = {line_sum:,.0f} nhưng hàng tổng ghi {v:,.0f} (chênh {abs(line_sum - v):,.0f})."
                          .replace(",", "."), "Cộng lại các dòng và sửa hàng tổng.")
            elif vat is not None and subtotal is not None and re.search(r"tổng|cộng", label):
                if abs(subtotal + vat - v) > TOL:
                    F.add("certain", "High", "Tổng thanh toán ≠ Cộng tiền hàng + Thuế", [ev(ri)],
                          f"{subtotal:,.0f} + {vat:,.0f} = {subtotal + vat:,.0f} nhưng ghi {v:,.0f}.".replace(",", "."),
                          "Tính lại tổng thanh toán.")


# ===================== chạy =====================
def build_summary_md(result):
    f = result["findings"]
    lines = [f"# Kết quả so sánh tự động ({len(result['files'])} tài liệu)", "",
             "Tài liệu: " + ", ".join(result["files"]), "",
             f"Số phát hiện: {len(f)}  |  " + "  |  ".join(f"{k}: {v}" for k, v in result["stats"]["by_category"].items()), ""]
    for x in f:
        lines += [f"## {x['id']} [{x['severity']}] {x['error_type']}  ({x['category']})",
                  f"- Tài liệu: {', '.join(x['documents'])}", f"- Vị trí: {'; '.join(x['locations'])}",
                  f"- Phân tích: {x['analysis']}", ""]
    return "\n".join(lines)


def run(paths):
    docs = [load(p) for p in paths]
    names = [d["file"] for d in docs]
    if len(set(names)) != len(names):  # trùng tên file ở thư mục khác nhau
        for d, p in zip(docs, paths):
            d["file"] = str(p)
    all_ents, F, warnings = [], Findings(), []
    for d in docs:
        if d.get("needs_ocr"):
            warnings.append(f"{d['file']}: PDF scan, cần OCR – kết quả so sánh không đáng tin cậy cho file này.")
        ents = extract_entities(d)
        all_ents += ents
        check_within_doc(d, ents, F)
        check_tables(d, F)
    if len(docs) >= 2:
        compare_across(all_ents, F)
    findings = F.finalize()
    inv = {}
    for e in all_ents:
        inv.setdefault(e["type"], []).append({k: e.get(k) for k in ("doc", "loc", "raw", "norm", "label", "title") if e.get(k) is not None})
    stats = {"entities": len(all_ents), "by_category": {}, "by_severity": {}}
    for x in findings:
        stats["by_category"][x["category"]] = stats["by_category"].get(x["category"], 0) + 1
        stats["by_severity"][x["severity"]] = stats["by_severity"].get(x["severity"], 0) + 1
    return {"files": [d["file"] for d in docs], "warnings": warnings, "inventory": inv,
            "findings": findings, "stats": stats}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--output", help="ghi JSON kết quả")
    ap.add_argument("--md", help="ghi thêm bản tóm tắt Markdown")
    a = ap.parse_args()
    try:
        result = run(a.files)
    except Exception as e:
        print(f"[LỖI] {e}", file=sys.stderr)
        sys.exit(2)
    for w in result["warnings"]:
        print(f"[CẢNH BÁO] {w}", file=sys.stderr)
    if a.output:
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.md:
        Path(a.md).write_text(build_summary_md(result), encoding="utf-8")
    s = result["stats"]
    print(f"So sánh {len(result['files'])} tài liệu: {len(result['findings'])} phát hiện "
          f"(theo loại: {s['by_category']}; theo mức độ: {s['by_severity']}).")
    if not a.output:
        print(build_summary_md(result))


if __name__ == "__main__":
    main()
