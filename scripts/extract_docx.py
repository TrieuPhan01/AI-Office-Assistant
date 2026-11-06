#!/usr/bin/env python3
"""Trích xuất nội dung DOCX theo đúng thứ tự trong tài liệu, kèm vị trí.

Kết quả JSON gồm:
  blocks   : danh sách đoạn văn và hàng bảng theo thứ tự xuất hiện (có "loc" để trích dẫn vị trí)
  tables   : toàn bộ bảng dạng ma trận (dùng để kiểm tra số học)
  headers / footers / properties

Ví dụ:
  python scripts/extract_docx.py hop-dong.docx -o workspace/output/hop-dong.json
  python scripts/extract_docx.py hop-dong.docx --format text
"""
import argparse
import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SECTION_RE = re.compile(r"^(Điều|ĐIỀU|Chương|CHƯƠNG|Mục|MỤC|Phần|PHẦN|Phụ lục|PHỤ LỤC)\s+[\dIVXLC]+", re.U)


def _iter_body(doc):
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield Table(child, doc)


def _row_cells(row):
    seen, out = set(), []
    for cell in row.cells:  # ô gộp lặp lại cùng một đối tượng -> chỉ lấy một lần
        if id(cell._tc) in seen:
            continue
        seen.add(id(cell._tc))
        out.append(cell.text.strip())
    return out


def extract(path):
    path = Path(path)
    doc = Document(str(path))
    blocks, tables = [], []
    section, p_idx, t_idx = "", 0, 0
    for item in _iter_body(doc):
        if isinstance(item, Paragraph):
            p_idx += 1
            text = item.text.strip()
            style = item.style.name if item.style is not None else ""
            if not text:
                continue
            if style.lower().startswith(("heading", "title")) or SECTION_RE.match(text):
                section = text[:80]
            loc = f"Đoạn {p_idx}" + (f" ({section})" if section else "")
            blocks.append({"id": f"P{p_idx}", "kind": "paragraph", "loc": loc,
                           "section": section, "style": style, "text": text})
        else:
            t_idx += 1
            rows = [_row_cells(r) for r in item.rows]
            tables.append({"id": f"T{t_idx}", "section": section, "rows": rows})
            for r_i, cells in enumerate(rows, start=1):
                if not any(cells):
                    continue
                blocks.append({"id": f"T{t_idx}R{r_i}", "kind": "table_row",
                               "loc": f"Bảng {t_idx}, hàng {r_i}" + (f" ({section})" if section else ""),
                               "section": section, "cells": cells, "text": " | ".join(cells)})
    headers, footers = [], []
    for s in doc.sections:
        headers += [p.text.strip() for p in s.header.paragraphs if p.text.strip()]
        footers += [p.text.strip() for p in s.footer.paragraphs if p.text.strip()]
    cp = doc.core_properties
    props = {k: (str(v) if v else "") for k, v in
             dict(author=cp.author, title=cp.title, created=cp.created, modified=cp.modified,
                  last_modified_by=cp.last_modified_by).items()}
    return {"file": path.name, "path": str(path), "type": "docx",
            "paragraph_count": p_idx, "table_count": t_idx, "has_images": bool(doc.inline_shapes),
            "blocks": blocks, "tables": tables, "headers": headers, "footers": footers,
            "properties": props}


def to_text(data):
    out = [f"# {data['file']}  ({data['paragraph_count']} đoạn, {data['table_count']} bảng)"]
    for b in data["blocks"]:
        out.append(f"[{b['id']}] {b['text']}")
    if data["headers"]:
        out.append("[HEADER] " + " / ".join(data["headers"]))
    if data["footers"]:
        out.append("[FOOTER] " + " / ".join(data["footers"]))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", help="ghi ra file thay vì màn hình")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    a = ap.parse_args()
    try:
        data = extract(a.input)
    except Exception as e:  # file hỏng, sai định dạng, bị khóa...
        print(f"[LỖI] Không đọc được {a.input}: {e}", file=sys.stderr)
        sys.exit(2)
    text = to_text(data) if a.format == "text" else json.dumps(data, ensure_ascii=False, indent=2)
    if a.output:
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(text, encoding="utf-8")
        print(f"Đã ghi {a.output} ({data['paragraph_count']} đoạn, {data['table_count']} bảng)")
    else:
        print(text)


if __name__ == "__main__":
    main()
