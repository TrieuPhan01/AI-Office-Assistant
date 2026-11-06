#!/usr/bin/env python3
"""Chuẩn hóa định dạng một file DOCX (font, cỡ chữ, lề, căn đoạn, số trang) mà KHÔNG đổi nội dung.

Tạo file mới, không sửa file gốc. Giữ nguyên bảng, hình ảnh, thứ tự nội dung; đoạn căn giữa/phải
(tiêu đề, chữ ký) được giữ nguyên căn lề.

Ví dụ:
  python scripts/docx_standardize.py workspace/input/bao-cao.docx -o workspace/output/bao-cao_chuan.docx \
      --font "Times New Roman" --size 13 --margins 20,20,30,20 --align justify --line-spacing 1.15 --page-numbers
"""
import argparse
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_to_docx import add_field, set_fonts  # noqa: E402

ALIGN = {"left": WD_ALIGN_PARAGRAPH.LEFT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}


def iter_paragraphs(doc, include_tables=True):
    for p in doc.paragraphs:
        yield p, False
    if include_tables:
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        yield p, True


def standardize(src, dst, font=None, size=None, margins=None, align=None, line_spacing=None,
                first_indent_mm=None, page_numbers=False, table_size=None):
    doc = Document(str(src))
    before = "\n".join(p.text for p, _ in iter_paragraphs(doc))
    stats = {"runs": 0, "paragraphs": 0}
    if font:
        for st in doc.styles:
            if st.type in (1, 2):  # paragraph / character
                try:
                    st.font.name = font
                    set_fonts(st.element, font)
                except Exception:
                    pass
    seen = set()
    for p, in_table in iter_paragraphs(doc):
        if id(p._p) in seen:  # ô gộp lặp lại
            continue
        seen.add(id(p._p))
        is_heading = p.style is not None and p.style.name.lower().startswith(("heading", "title"))
        for r in p.runs:
            if font:
                r.font.name = font
                set_fonts(r._r, font)
            if size and not is_heading and not in_table:
                r.font.size = Pt(size)
            if table_size and in_table:
                r.font.size = Pt(table_size)
            stats["runs"] += 1
        if not in_table and not is_heading and p.text.strip():
            pf = p.paragraph_format
            if align and p.alignment in (None, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY):
                p.alignment = ALIGN[align]
            if line_spacing:
                pf.line_spacing = line_spacing
            if first_indent_mm is not None and not p.style.name.lower().startswith("list"):
                pf.first_line_indent = Mm(first_indent_mm) if first_indent_mm else None
            stats["paragraphs"] += 1
    if margins:
        t, b, l, r = margins
        for s in doc.sections:
            s.top_margin, s.bottom_margin, s.left_margin, s.right_margin = Mm(t), Mm(b), Mm(l), Mm(r)
    if page_numbers:
        for s in doc.sections:
            if "PAGE" not in s.footer._element.xml:
                fp = s.footer.paragraphs[0] if s.footer.paragraphs else s.footer.add_paragraph()
                fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_field(fp, "PAGE")
    after = "\n".join(p.text for p, _ in iter_paragraphs(doc))
    if before != after:  # bảo hiểm: không bao giờ đổi nội dung
        raise RuntimeError("Nội dung bị thay đổi ngoài ý muốn – hủy, không ghi file.")
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dst))
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--font")
    ap.add_argument("--size", type=float, help="cỡ chữ nội dung (không áp cho tiêu đề và bảng)")
    ap.add_argument("--table-size", type=float, help="cỡ chữ trong bảng")
    ap.add_argument("--margins", help="trên,dưới,trái,phải (mm), ví dụ 20,20,30,20")
    ap.add_argument("--align", choices=["left", "justify"])
    ap.add_argument("--line-spacing", type=float)
    ap.add_argument("--first-indent-mm", type=float, help="thụt đầu dòng (0 = bỏ)")
    ap.add_argument("--page-numbers", action="store_true")
    a = ap.parse_args()
    src, dst = Path(a.input), Path(a.output)
    if src.resolve() == dst.resolve():
        print("[LỖI] Không được ghi đè file gốc. Hãy chọn tên file kết quả khác.", file=sys.stderr)
        sys.exit(2)
    if dst.exists():
        print(f"[CẢNH BÁO] {dst} đã tồn tại và sẽ bị ghi đè.", file=sys.stderr)
    margins = [float(x) for x in a.margins.split(",")] if a.margins else None
    if margins and len(margins) != 4:
        print("[LỖI] --margins cần đúng 4 số: trên,dưới,trái,phải", file=sys.stderr)
        sys.exit(2)
    try:
        st = standardize(src, dst, a.font, a.size, margins, a.align, a.line_spacing, a.first_indent_mm,
                         a.page_numbers, a.table_size)
    except Exception as e:
        print(f"[LỖI] {e}", file=sys.stderr)
        sys.exit(2)
    print(f"Đã tạo {dst}: chuẩn hóa {st['runs']} đoạn chữ (run), {st['paragraphs']} đoạn văn. Nội dung không đổi.")


if __name__ == "__main__":
    main()
