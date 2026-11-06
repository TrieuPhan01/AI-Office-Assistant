#!/usr/bin/env python3
"""Chuyển Markdown (tập con đơn giản) sang DOCX chuẩn tiếng Việt.

Hỗ trợ: tiêu đề #..####, đoạn văn, **đậm**, *nghiêng*, `mã`, danh sách gạch đầu dòng và đánh số,
bảng (|...|, có căn lề :---: ), trích dẫn (>), khối mã (```), ảnh ![mô tả](đường-dẫn),
<p align="center|right|left">…</p>, <br> trong ô bảng, [TOC], <!-- pagebreak -->.
Bảng có hàng tiêu đề để trống => bảng bố cục không viền (dùng cho Quốc hiệu - Tiêu ngữ).
Chỗ "[CẦN BỔ SUNG: ...]" được tô vàng để người dùng dễ thấy.

Ví dụ:
  python scripts/md_to_docx.py van-ban.md -o workspace/output/van-ban.docx --profile hanhchinh
"""
import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

PROFILES = {
    # Lề theo thông lệ thể thức văn bản hành chính VN (trên/dưới 20, trái 30, phải 20 mm).
    # Cần đối chiếu quy định hiện hành khi dùng cho văn bản gửi cơ quan nhà nước.
    "hanhchinh": dict(font="Times New Roman", size=13, top=20, bottom=20, left=30, right=20,
                      align="justify", first_indent_mm=12.7, line=1.15, after=6),
    "baocao": dict(font="Times New Roman", size=13, top=20, bottom=20, left=25, right=20,
                   align="justify", first_indent_mm=0, line=1.3, after=6),
}
INLINE = re.compile(r"(\*\*[^*]+\*\*|(?<![\w*])\*[^*\s][^*]*\*(?![\w*])|`[^`]+`|\[CẦN BỔ SUNG[^\]]*\])")
SEVERITY_FILL = {"Critical": "F4B6B6", "High": "F8D5A8", "Medium": "FBF0B0", "Low": "D5E8D4"}
ALIGN = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
         "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}


# ---------- tiện ích định dạng ----------
def set_fonts(rpr_owner, name):
    """Gán font cho cả 4 nhóm ký tự (quan trọng với tiếng Việt)."""
    rpr = rpr_owner.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def style_font(style, name, size, bold=None, italic=None):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    set_fonts(style.element, name)


def shade(cell, hex_fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def add_field(paragraph, instr):
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        elif text == instr:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = instr
        else:
            el = OxmlElement("w:t")
            el.text = text
        run._r.append(el)
    return run


def add_inline(par, text, font, size, bold=False, italic=False):
    """Thêm văn bản có **đậm**, *nghiêng*, `mã`, <br> và tô vàng chỗ cần bổ sung."""
    parts = re.split(r"<br\s*/?>", text)
    for pi, part in enumerate(parts):
        if pi > 0:
            par.add_run().add_break(WD_BREAK.LINE)
        for tok in INLINE.split(part):
            if not tok:
                continue
            run_bold, run_italic, run_font, hl = bold, italic, font, False
            if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
                tok, run_bold = tok[2:-2], True
            elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
                tok, run_font = tok[1:-1], "Consolas"
            elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2 and not tok.startswith("**"):
                tok, run_italic = tok[1:-1], True
            elif tok.startswith("[CẦN BỔ SUNG"):
                hl = True
            run = par.add_run(tok)
            run.bold = run_bold or None
            run.italic = run_italic or None
            run.font.size = Pt(size)
            run.font.name = run_font
            set_fonts(run._r, run_font)
            if hl:
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW


# ---------- bộ chuyển đổi ----------
class Converter:
    def __init__(self, profile, font=None, size=None, landscape=False, header=None, page_numbers=True,
                 base_dir=None):
        p = dict(PROFILES[profile])
        if font:
            p["font"] = font
        if size:
            p["size"] = size
        self.p = p
        self.base_dir = Path(base_dir or ".")
        self.doc = Document()
        self._setup(landscape, header, page_numbers)

    def _setup(self, landscape, header, page_numbers):
        p, doc = self.p, self.doc
        sec = doc.sections[0]
        if landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = Mm(297), Mm(210)
        else:
            sec.page_width, sec.page_height = Mm(210), Mm(297)
        sec.top_margin, sec.bottom_margin = Mm(p["top"]), Mm(p["bottom"])
        sec.left_margin, sec.right_margin = Mm(p["left"]), Mm(p["right"])
        style_font(doc.styles["Normal"], p["font"], p["size"])
        for lvl, delta in ((1, 2), (2, 1), (3, 0), (4, 0)):
            st = doc.styles[f"Heading {lvl}"]
            style_font(st, p["font"], p["size"] + delta, bold=True, italic=(lvl == 4))
            st.paragraph_format.space_before = Pt(12 if lvl <= 2 else 8)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.keep_with_next = True
        for name in ("List Bullet", "List Bullet 2"):
            style_font(doc.styles[name], p["font"], p["size"])
        if page_numbers:
            fp = sec.footer.paragraphs[0]
            fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_field(fp, "PAGE")
            for r in fp.runs:
                r.font.size = Pt(p["size"] - 2)
        if header:
            hp = sec.header.paragraphs[0]
            hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = hp.add_run(header)
            run.font.size = Pt(p["size"] - 3)
            run.italic = True

    def _fmt(self, par, align=None, indent=False):
        p = self.p
        pf = par.paragraph_format
        pf.line_spacing = p["line"]
        pf.space_after = Pt(p["after"])
        pf.alignment = ALIGN[align or p["align"]]
        if indent and p["first_indent_mm"]:
            pf.first_line_indent = Mm(p["first_indent_mm"])

    def paragraph(self, text, align=None, indent=True, bold=False, italic=False):
        par = self.doc.add_paragraph()
        self._fmt(par, align, indent)
        add_inline(par, text, self.p["font"], self.p["size"], bold, italic)
        return par

    def heading(self, level, text):
        par = self.doc.add_heading(level=min(level, 4))
        par.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_inline(par, text, self.p["font"], self.p["size"] + {1: 2, 2: 1}.get(level, 0), bold=True)

    def bullet(self, text, level):
        par = self.doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
        par.paragraph_format.space_after = Pt(3)
        par.paragraph_format.line_spacing = self.p["line"]
        add_inline(par, text, self.p["font"], self.p["size"])

    def numbered(self, num, text, level):
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.left_indent = Mm(10 + 8 * level)
        pf.first_line_indent = Mm(-6)
        pf.space_after = Pt(3)
        pf.line_spacing = self.p["line"]
        add_inline(par, f"{num}.\t{text}", self.p["font"], self.p["size"])

    def quote(self, text):
        par = self.doc.add_paragraph()
        par.paragraph_format.left_indent = Mm(10)
        par.paragraph_format.space_after = Pt(6)
        add_inline(par, text, self.p["font"], self.p["size"], italic=True)

    def code(self, lines):
        for ln in lines or [""]:
            par = self.doc.add_paragraph()
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.left_indent = Mm(5)
            run = par.add_run(ln)
            run.font.name = "Consolas"
            run.font.size = Pt(self.p["size"] - 3)
            set_fonts(run._r, "Consolas")
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def image(self, alt, path):
        img = Path(path)
        if not img.is_absolute():
            img = self.base_dir / img
        if not img.exists():
            self.paragraph(f"[CẦN BỔ SUNG: không tìm thấy ảnh {path}]", indent=False)
            return
        sec = self.doc.sections[0]
        max_w = sec.page_width - sec.left_margin - sec.right_margin
        self.doc.add_picture(str(img), width=int(max_w * 0.9))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if alt:
            self.paragraph(alt, align="center", indent=False, italic=True)

    def toc(self):
        par = self.doc.add_paragraph()
        add_field(par, 'TOC \\o "1-3" \\h \\z \\u')
        # Yêu cầu Word tự cập nhật mục lục khi mở file (sẽ hiện hộp thoại hỏi cập nhật)
        settings = self.doc.settings.element
        if settings.find(qn("w:updateFields")) is None:
            el = OxmlElement("w:updateFields")
            el.set(qn("w:val"), "true")
            settings.append(el)

    def table(self, rows):
        def split(line):
            line = line.strip()
            if line.startswith("|"):
                line = line[1:]
            if line.endswith("|"):
                line = line[:-1]
            return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]

        cells = [split(r) for r in rows]
        aligns = None
        if len(cells) >= 2 and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells[1]):
            aligns = []
            for c in cells[1]:
                c = c.replace(" ", "")
                aligns.append("center" if c.startswith(":") and c.endswith(":")
                              else "right" if c.endswith(":") else "left")
            cells = [cells[0]] + cells[2:]
        ncol = max(len(r) for r in cells)
        cells = [r + [""] * (ncol - len(r)) for r in cells]
        layout = all(c == "" for c in cells[0])  # tiêu đề trống => bảng bố cục
        if layout:
            cells = cells[1:]
        if not cells:
            return
        tbl = self.doc.add_table(rows=len(cells), cols=ncol)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        if not layout:
            tbl.style = "Table Grid"
        fsize = self.p["size"] if layout else max(self.p["size"] - 2, 9)
        for ri, row in enumerate(cells):
            tr = tbl.rows[ri]
            no_split(tr)
            for ci, text in enumerate(row):
                cell = tr.cells[ci]
                par = cell.paragraphs[0]
                par.paragraph_format.space_after = Pt(2)
                par.paragraph_format.alignment = ALIGN[(aligns[ci] if aligns else "left")]
                header = (ri == 0 and not layout)
                add_inline(par, text, self.p["font"], fsize, bold=header)
                if header:
                    shade(cell, "D9D9D9")
                elif text in SEVERITY_FILL:
                    shade(cell, SEVERITY_FILL[text])
            if ri == 0 and not layout:
                repeat_header(tr)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # ---------- đọc Markdown ----------
    def convert(self, md_text):
        lines = md_text.replace("\r\n", "\n").split("\n")
        if lines and lines[0].strip() == "---":  # bỏ front-matter
            try:
                end = lines[1:].index("---") + 1
                lines = lines[end + 1:]
            except ValueError:
                pass
        buf = []  # đoạn văn đang gom

        def flush():
            if buf:
                self.paragraph(" ".join(s.strip() for s in buf))
                buf.clear()

        i = 0
        while i < len(lines):
            ln = lines[i]
            s = ln.strip()
            if s.startswith("```"):
                flush()
                j, block = i + 1, []
                while j < len(lines) and not lines[j].strip().startswith("```"):
                    block.append(lines[j])
                    j += 1
                self.code(block)
                i = j + 1
                continue
            if not s:
                flush()
                i += 1
                continue
            if s.startswith("|"):
                flush()
                j, rows = i, []
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append(lines[j])
                    j += 1
                self.table(rows)
                i = j
                continue
            m = re.match(r"^(#{1,6})\s+(.*)$", s)
            if m:
                flush()
                self.heading(len(m.group(1)), m.group(2))
            elif re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", s):
                flush()
            elif s.lower() in ("[toc]", "<!-- toc -->"):
                flush()
                self.toc()
            elif s.lower() in ("<!-- pagebreak -->", "\\pagebreak"):
                flush()
                self.doc.add_page_break()
            elif re.match(r"^<p\s+align=\"(left|center|right)\">(.*)</p>$", s, re.I):
                flush()
                mm = re.match(r"^<p\s+align=\"(left|center|right)\">(.*)</p>$", s, re.I)
                self.paragraph(mm.group(2), align=mm.group(1).lower(), indent=False)
            elif re.match(r"^!\[(.*?)\]\((.+?)\)$", s):
                flush()
                mm = re.match(r"^!\[(.*?)\]\((.+?)\)$", s)
                self.image(mm.group(1), mm.group(2))
            elif re.match(r"^\s*[-*+]\s+", ln):
                flush()
                lvl = 1 if len(ln) - len(ln.lstrip()) >= 2 else 0
                self.bullet(re.sub(r"^\s*[-*+]\s+", "", ln), lvl)
            elif re.match(r"^\s*\d+[.)]\s+", ln):
                flush()
                mm = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", ln)
                self.numbered(mm.group(2), mm.group(3), 1 if len(mm.group(1)) >= 2 else 0)
            elif s.startswith(">"):
                flush()
                self.quote(s.lstrip("> ").strip())
            else:
                buf.append(ln)
            i += 1
        flush()
        return self.doc


def convert_file(src, dst, profile="hanhchinh", **kw):
    src, dst = Path(src), Path(dst)
    conv = Converter(profile, base_dir=src.parent, **kw)
    doc = conv.convert(src.read_text(encoding="utf-8"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dst)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="file .md")
    ap.add_argument("-o", "--output", required=True, help="file .docx kết quả")
    ap.add_argument("--profile", choices=PROFILES, default="hanhchinh")
    ap.add_argument("--font")
    ap.add_argument("--size", type=float)
    ap.add_argument("--landscape", action="store_true")
    ap.add_argument("--header", help="chữ ở đầu mỗi trang")
    ap.add_argument("--no-page-numbers", action="store_true")
    a = ap.parse_args()
    if Path(a.output).exists():
        print(f"[CẢNH BÁO] {a.output} đã tồn tại và sẽ bị ghi đè.", file=sys.stderr)
    out = convert_file(a.input, a.output, a.profile, font=a.font, size=a.size, landscape=a.landscape,
                       header=a.header, page_numbers=not a.no_page_numbers)
    print(f"Đã tạo: {out}")


if __name__ == "__main__":
    main()
