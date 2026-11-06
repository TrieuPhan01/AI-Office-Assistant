#!/usr/bin/env python3
"""Trích xuất nội dung PDF theo trang/dòng; cảnh báo PDF scan (cần OCR) và lỗi mã hóa font tiếng Việt.

Nhiều engine được thử theo thứ tự ưu tiên (cái nào có sẵn thì dùng), rồi CHỌN bản ít lỗi nhất:
  pymupdf (PyMuPDF) -> pdftotext (poppler, lệnh hệ thống) -> pdfplumber -> pypdf
Lý do: cùng một file PDF, mỗi thư viện có thể đọc dấu tiếng Việt khác nhau (có engine làm hỏng dấu,
ví dụ "Nguyễ0n", "(cid:18)"). Script chấm điểm lỗi và chọn engine tốt nhất; dùng --engine để ép một engine.

Script KHÔNG tự OCR. PDF scan cần OCR trước (ocrmypdf/Tesseract).

Ví dụ:
  python scripts/extract_pdf.py bao-gia.pdf -o workspace/output/bao-gia.json
  python scripts/extract_pdf.py bao-gia.pdf --format text --engine pdftotext
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_CHARS_PER_PAGE = 25  # dưới ngưỡng này coi trang là ảnh/scan
GARBLE = re.compile(r"\(cid:\d+\)|[^\W\d_][0-9][^\W\d_]")  # lỗi mã hóa: "(cid:18)", "Nguyễ0n"
ENGINES = ["pymupdf", "pdftotext", "pdfplumber", "pypdf"]


class Unavailable(Exception):
    pass


def _pymupdf(path):
    try:
        import fitz
    except ImportError:
        raise Unavailable("chưa cài PyMuPDF")
    with fitz.open(str(path)) as pdf:
        if pdf.needs_pass:
            raise RuntimeError("PDF có mật khẩu")
        return [pg.get_text("text") for pg in pdf]


def _pdftotext(path):
    exe = shutil.which("pdftotext")
    if not exe:
        raise Unavailable("không có lệnh pdftotext (poppler-utils)")
    r = subprocess.run([exe, "-layout", "-enc", "UTF-8", str(path), "-"], capture_output=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip()[:200] or "pdftotext lỗi")
    pages = r.stdout.decode("utf-8", "replace").split("\f")
    return pages[:-1] if pages and not pages[-1].strip() else pages


def _pdfplumber(path):
    try:
        import pdfplumber
    except ImportError:
        raise Unavailable("chưa cài pdfplumber")
    with pdfplumber.open(str(path)) as pdf:
        return [(pg.extract_text() or "") for pg in pdf.pages]


def _pypdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise Unavailable("chưa cài pypdf")
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise RuntimeError("PDF có mật khẩu")
    return [(pg.extract_text() or "") for pg in reader.pages]


_FUNCS = {"pymupdf": _pymupdf, "pdftotext": _pdftotext, "pdfplumber": _pdfplumber, "pypdf": _pypdf}


def garble_score(pages):
    return len(GARBLE.findall("\n".join(pages)))


def read_pages(path, engine="auto"):
    """Trả về (engine, pages, điểm_lỗi). Ném RuntimeError nếu không engine nào đọc được."""
    order = ENGINES if engine == "auto" else [engine]
    best, errors = None, []
    for name in order:
        try:
            pages = [p.replace("\x00", "") for p in _FUNCS[name](path)]
        except Unavailable as e:
            errors.append(f"{name}: {e}")
            continue
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__}: {e}")
            continue
        score = garble_score(pages)
        if best is None or score < best[2]:
            best = (name, pages, score)
        if score == 0 and any(p.strip() for p in pages):
            break  # đủ tốt, khỏi thử tiếp
    if best is None:
        raise RuntimeError("Không đọc được PDF. " + "; ".join(errors) +
                           " — hãy cài PyMuPDF (pip install PyMuPDF) hoặc poppler-utils.")
    return best


def extract(path, engine="auto"):
    path = Path(path)
    lib, page_texts, garble = read_pages(path, engine)
    pages, blocks, low_pages = [], [], []
    for n, text in enumerate(page_texts, start=1):
        chars = len(text.strip())
        if chars < MIN_CHARS_PER_PAGE:
            low_pages.append(n)
        pages.append({"page": n, "char_count": chars, "text": text})
        line_no = 0
        for line in text.splitlines():
            line = re.sub(r"\s{2,}", " ", line.strip())  # -layout chèn nhiều khoảng trắng
            if not line:
                continue
            line_no += 1
            blocks.append({"id": f"p{n}l{line_no}", "kind": "line", "page": n,
                           "loc": f"Trang {n}, dòng {line_no}", "text": line})
    needs_ocr = bool(pages) and len(low_pages) >= max(1, len(pages) // 2)
    data = {"file": path.name, "path": str(path), "type": "pdf", "library": lib, "page_count": len(pages),
            "needs_ocr": needs_ocr, "low_text_pages": low_pages, "garble_score": garble,
            "pages": pages, "blocks": blocks, "tables": []}
    warnings = []
    if needs_ocr:
        warnings.append("PDF có vẻ là bản scan (ít hoặc không có văn bản). Cần OCR trước khi kiểm tra; "
                        "nội dung trích xuất không đáng tin cậy.")
    elif low_pages:
        warnings.append(f"Các trang {low_pages} gần như không có văn bản (có thể là ảnh/scan).")
    if garble:
        warnings.append(f"Phát hiện {garble} vị trí nghi lỗi mã hóa font/dấu tiếng Việt (engine {lib}). "
                        "Cần đối chiếu mắt thường các chỗ khác biệt phát hiện từ file này.")
    if warnings:
        data["warning"] = " ".join(warnings)
    return data


def to_text(data):
    out = [f"# {data['file']}  ({data['page_count']} trang, engine: {data['library']})"]
    if data.get("warning"):
        out.append(f"[CẢNH BÁO] {data['warning']}")
    for pg in data["pages"]:
        out.append(f"\n--- Trang {pg['page']} ---\n{pg['text'].strip()}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    ap.add_argument("--engine", choices=["auto"] + ENGINES, default="auto")
    a = ap.parse_args()
    try:
        data = extract(a.input, a.engine)
    except Exception as e:
        print(f"[LỖI] Không đọc được {a.input}: {e}", file=sys.stderr)
        sys.exit(2)
    if data.get("warning"):
        print(f"[CẢNH BÁO] {data['warning']}", file=sys.stderr)
    text = to_text(data) if a.format == "text" else json.dumps(data, ensure_ascii=False, indent=2)
    if a.output:
        Path(a.output).parent.mkdir(parents=True, exist_ok=True)
        Path(a.output).write_text(text, encoding="utf-8")
        print(f"Đã ghi {a.output} ({data['page_count']} trang, engine {data['library']})")
    else:
        print(text)


if __name__ == "__main__":
    main()
