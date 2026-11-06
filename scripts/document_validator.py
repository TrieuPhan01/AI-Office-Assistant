#!/usr/bin/env python3
"""Kiểm tra file kết quả trước khi bàn giao (DOCX, MD, XLSX).

Mức kết quả: PASS (ổn), WARN (nên xem lại), FAIL (hỏng/thiếu nghiêm trọng).
Loại kiểm tra thêm (--type):
  admin  : văn bản hành chính – Quốc hiệu/Tiêu ngữ, "Số:", chỗ còn "[CẦN BỔ SUNG]"
  report : báo cáo – có ≥2 tiêu đề, có phần kết luận
  audit  : báo cáo kiểm tra – mỗi phát hiện đủ 9 trường, mã lỗi không trùng, mức độ hợp lệ

Ví dụ:
  python scripts/document_validator.py workspace/output/cong-van.docx --type admin
  python scripts/document_validator.py workspace/output/bao-cao.docx --json
Mã thoát: 0 = PASS/WARN, 1 = FAIL.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

AUDIT_FIELDS = ["Mã lỗi", "Tài liệu", "Vị trí", "Nội dung gốc", "Nội dung đối chiếu", "Loại lỗi", "Mức độ",
                "Phân tích", "Đề xuất"]
SEVERITIES = {"Critical", "High", "Medium", "Low"}
PLACEHOLDER = re.compile(r"\[CẦN BỔ SUNG[^\]]*\]")


class Report:
    def __init__(self, path):
        self.path, self.items = str(path), []

    def add(self, level, code, msg):
        self.items.append({"level": level, "code": code, "message": msg})

    @property
    def status(self):
        lv = {i["level"] for i in self.items}
        return "FAIL" if "FAIL" in lv else "WARN" if "WARN" in lv else "PASS"


def docx_text_and_tables(doc):
    paras = [p for p in doc.paragraphs]
    text = "\n".join(p.text for p in paras)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                text += "\n" + c.text
    return paras, text


def check_docx(path, kind, rep):
    from docx import Document
    try:
        doc = Document(str(path))
    except Exception as e:
        rep.add("FAIL", "OPEN", f"Không mở được DOCX: {e}")
        return
    paras, text = docx_text_and_tables(doc)
    if not text.strip():
        rep.add("FAIL", "EMPTY", "Tài liệu không có nội dung.")
        return
    rep.add("INFO", "STATS", f"{len(paras)} đoạn, {len(doc.tables)} bảng, {len(doc.inline_shapes)} ảnh.")
    ph = PLACEHOLDER.findall(text)
    if ph:
        rep.add("WARN", "PLACEHOLDER", f"Còn {len(ph)} chỗ cần bổ sung, ví dụ: {ph[0][:80]}")
    if re.search(r"\*\*[^*]+\*\*|^#{1,6}\s|\|\s*-{3,}", text, re.M):
        rep.add("WARN", "MARKDOWN_LEFTOVER", "Còn ký hiệu Markdown (**, #, |---|) trong nội dung.")
    fonts = Counter()
    for p in paras:
        for r in p.runs:
            if r.text.strip():
                fonts[r.font.name or (p.style.font.name if p.style is not None else None) or "(mặc định)"] += 1
    named = {f for f in fonts if f != "(mặc định)" and f != "Consolas"}
    if len(named) > 2:
        rep.add("WARN", "FONTS", f"Dùng nhiều font ({', '.join(sorted(named))}); nên thống nhất.")
    empty_run = 0
    for p in paras:
        empty_run = empty_run + 1 if not p.text.strip() else 0
        if empty_run > 3:
            rep.add("WARN", "BLANK_LINES", "Có hơn 3 đoạn trống liên tiếp.")
            break
    footer_xml = "".join(s.footer._element.xml for s in doc.sections)
    if "PAGE" not in footer_xml:
        rep.add("INFO", "NO_PAGE_NUMBER", "Chưa có số trang ở chân trang.")

    if kind == "admin":
        head = "\n".join(p.text for p in paras[:3])
        for t in doc.tables[:1]:
            head += "\n".join(c.text for r in t.rows for c in r.cells)
        if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" not in head.upper():
            rep.add("WARN", "QUOC_HIEU", "Không thấy Quốc hiệu ở đầu văn bản (bỏ qua nếu là văn bản nội bộ không cần).")
        if not re.search(r"\bSố\s*:", text):
            rep.add("WARN", "SO_VB", "Không thấy dòng 'Số:' của văn bản.")
        if not re.search(r"Nơi nhận", text, re.I):
            rep.add("WARN", "NOI_NHAN", "Không thấy phần 'Nơi nhận'.")
    elif kind == "report":
        heads = [p for p in paras if p.style is not None and p.style.name.startswith("Heading")]
        if len(heads) < 2:
            rep.add("WARN", "HEADINGS", "Báo cáo có ít hơn 2 tiêu đề (Heading) – cấu trúc có thể chưa rõ.")
        if not re.search(r"kết luận|đề xuất|kiến nghị", text, re.I):
            rep.add("WARN", "CONCLUSION", "Không thấy phần kết luận/đề xuất.")
    elif kind == "audit":
        check_audit_tables(doc, rep)


def check_audit_tables(doc, rep):
    blocks = []
    for t in doc.tables:
        labels = [r.cells[0].text.strip() for r in t.rows if r.cells]
        if "Mã lỗi" in labels:
            blocks.append({r.cells[0].text.strip(): r.cells[1].text.strip() for r in t.rows if len(r.cells) > 1})
    if not blocks:
        rep.add("FAIL", "AUDIT_NO_FINDINGS", "Không tìm thấy bảng chi tiết phát hiện (trường 'Mã lỗi').")
        return
    validate_audit_blocks(blocks, rep)


def validate_audit_blocks(blocks, rep):
    ids = [b.get("Mã lỗi", "") for b in blocks]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        rep.add("FAIL", "AUDIT_DUP_ID", f"Mã lỗi bị trùng: {', '.join(dup)}")
    for b in blocks:
        miss = [f for f in AUDIT_FIELDS if f not in b]
        empty = [f for f in AUDIT_FIELDS if f in b and not b[f] and f != "Nội dung đối chiếu"]
        if miss or empty:
            rep.add("FAIL", "AUDIT_FIELDS", f"{b.get('Mã lỗi', '?')}: thiếu/trống trường {', '.join(miss + empty)}")
        if b.get("Mức độ") and b["Mức độ"] not in SEVERITIES:
            rep.add("FAIL", "AUDIT_SEVERITY", f"{b.get('Mã lỗi', '?')}: mức độ không hợp lệ '{b['Mức độ']}'")
    rep.add("INFO", "AUDIT_COUNT", f"{len(blocks)} phát hiện được kiểm tra đủ 9 trường.")


def check_md(path, kind, rep):
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip():
        rep.add("FAIL", "EMPTY", "File Markdown rỗng.")
        return
    ph = PLACEHOLDER.findall(text)
    if ph:
        rep.add("WARN", "PLACEHOLDER", f"Còn {len(ph)} chỗ cần bổ sung.")
    if kind == "audit":
        blocks, cur = [], None
        for ln in text.splitlines():
            m = re.match(r"\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|$", ln)
            if re.match(r"^#{4}\s", ln):
                cur = {}
                blocks.append(cur)
            elif m and cur is not None and m.group(1) not in ("Trường", "---"):
                cur[m.group(1)] = m.group(2)
        if not blocks:
            rep.add("FAIL", "AUDIT_NO_FINDINGS", "Không thấy phát hiện nào (#### mã lỗi).")
        else:
            validate_audit_blocks(blocks, rep)
    rep.add("INFO", "STATS", f"{len(text.splitlines())} dòng.")


def check_xlsx(path, kind, rep):
    from openpyxl import load_workbook
    try:
        wb = load_workbook(str(path))
    except Exception as e:
        rep.add("FAIL", "OPEN", f"Không mở được XLSX: {e}")
        return
    ws = wb.worksheets[0]
    if ws.max_row < 1 or ws.max_column < 1:
        rep.add("FAIL", "EMPTY", "Bảng tính rỗng.")
        return
    rep.add("INFO", "STATS", f"Sheet '{ws.title}': {ws.max_row} hàng, {ws.max_column} cột.")
    if kind == "audit" and ws.max_row < 2:
        rep.add("WARN", "AUDIT_EMPTY", "Bảng Excel không có dòng lỗi nào.")


def validate(path, kind="auto"):
    p = Path(path)
    rep = Report(p)
    if not p.exists():
        rep.add("FAIL", "MISSING", "File không tồn tại.")
        return rep
    if p.stat().st_size == 0:
        rep.add("FAIL", "ZERO_BYTES", "File 0 byte.")
        return rep
    ext = p.suffix.lower()
    {".docx": check_docx, ".md": check_md, ".xlsx": check_xlsx}.get(
        ext, lambda *_: rep.add("WARN", "UNSUPPORTED", f"Chưa hỗ trợ kiểm tra định dạng {ext}"))(p, kind, rep)
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--type", choices=["auto", "admin", "report", "audit"], default="auto")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    reps = [validate(f, a.type) for f in a.files]
    if a.json:
        print(json.dumps([{"file": r.path, "status": r.status, "items": r.items} for r in reps],
                         ensure_ascii=False, indent=2))
    else:
        for r in reps:
            print(f"[{r.status}] {r.path}")
            for i in r.items:
                print(f"   - {i['level']:<4} {i['code']}: {i['message']}")
    sys.exit(1 if any(r.status == "FAIL" for r in reps) else 0)


if __name__ == "__main__":
    main()
