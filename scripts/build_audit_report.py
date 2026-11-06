#!/usr/bin/env python3
"""Tạo báo cáo kiểm tra tài liệu (Markdown + DOCX + Excel) từ file findings JSON.

Đầu vào: JSON do compare_documents.py tạo, sau khi Claude đã rà soát (xóa cảnh báo sai, bổ sung phát hiện
ngữ nghĩa). Có thể thêm khối "meta":
  {"title": "...", "summary": "đoạn tóm tắt", "limitations": ["..."],
   "dismissed": [{"id": "F-004", "reason": "Hai bên khác nhau nên MST khác nhau là bình thường"}]}
Mỗi phát hiện cần: category (certain|verify|logic|suggestion), severity (Critical|High|Medium|Low),
error_type, documents[], locations[], original, compare, analysis, suggestion. Thiếu "id" sẽ được tự cấp (C-001...).

Ví dụ:
  python scripts/build_audit_report.py workspace/output/audit_final.json --outdir workspace/output --name 20261106_kiem-tra-hop-dong
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md_to_docx  # noqa: E402

CAT_NAME = {"certain": "Lỗi chắc chắn", "verify": "Khác biệt cần xác minh",
            "logic": "Cảnh báo logic", "suggestion": "Đề xuất cải thiện"}
CAT_ORDER = list(CAT_NAME)
SEVERITIES = ["Critical", "High", "Medium", "Low"]
REQUIRED = ["category", "severity", "error_type", "documents", "locations", "original", "analysis", "suggestion"]
DEFAULT_LIMITS = [
    "Kết quả dựa trên nội dung văn bản trích xuất được; chữ trong ảnh, chữ ký, con dấu, ghi chú tay không được kiểm tra.",
    "Bộ so sánh tự động dùng quy tắc nhận diện mẫu nên có thể bỏ sót hoặc cảnh báo thừa; mục 'Khác biệt cần xác minh' cần người có thẩm quyền xác nhận.",
    "Báo cáo không thay thế việc rà soát của bộ phận pháp chế/kế toán đối với các nội dung quan trọng.",
]


def unique_path(p):
    p = Path(p)
    if not p.exists():
        return p
    i = 2
    while p.with_name(f"{p.stem}_v{i}{p.suffix}").exists():
        i += 1
    return p.with_name(f"{p.stem}_v{i}{p.suffix}")


def esc(s):
    return str(s if s is not None else "").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def load_findings(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = {"findings": data}
    meta = data.get("meta", {})
    dismissed = {d["id"]: d.get("reason", "") for d in meta.get("dismissed", [])}
    items, n = [], 0
    for f in data.get("findings", []):
        if f.get("id") in dismissed:
            continue
        miss = [k for k in REQUIRED if k not in f]
        if miss:
            raise ValueError(f"Phát hiện {f.get('id', '?')} thiếu trường: {', '.join(miss)}")
        if f["category"] not in CAT_NAME or f["severity"] not in SEVERITIES:
            raise ValueError(f"Phát hiện {f.get('id', '?')}: category/severity không hợp lệ "
                             f"({f['category']}/{f['severity']})")
        f = dict(f)
        f.setdefault("compare", "")
        if not f.get("id"):
            n += 1
            f["id"] = f"C-{n:03d}"
        items.append(f)
    ids = [f["id"] for f in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Mã lỗi (id) bị trùng nhau")
    items.sort(key=lambda f: (CAT_ORDER.index(f["category"]), SEVERITIES.index(f["severity"]), f["id"]))
    return data, meta, items, dismissed


def build_markdown(data, meta, items, dismissed):
    files = data.get("files") or sorted({d for f in items for d in f["documents"]})
    L = [f"# {meta.get('title', 'BÁO CÁO KIỂM TRA TÍNH ĐỒNG NHẤT TÀI LIỆU')}", "",
         f"**Ngày lập:** {datetime.now():%d/%m/%Y %H:%M}  |  **Số tài liệu:** {len(files)}  |  "
         f"**Số phát hiện:** {len(items)}", "", "## 1. Phạm vi kiểm tra", "",
         "| STT | Tài liệu |", "|---|---|"]
    L += [f"| {i} | {esc(f)} |" for i, f in enumerate(files, 1)]
    L += ["", "## 2. Tóm tắt kết quả", ""]
    if meta.get("summary"):
        L += [meta["summary"], ""]
    L += ["| Nhóm | " + " | ".join(SEVERITIES) + " | Tổng |", "|---|" + "---|" * (len(SEVERITIES) + 1)]
    for c in CAT_ORDER:
        row = [sum(1 for f in items if f["category"] == c and f["severity"] == s) for s in SEVERITIES]
        L.append(f"| {CAT_NAME[c]} | " + " | ".join(map(str, row)) + f" | {sum(row)} |")
    L += ["", "## 3. Chi tiết phát hiện", ""]
    for ci, c in enumerate(CAT_ORDER, 1):
        group = [f for f in items if f["category"] == c]
        L += [f"### 3.{ci} {CAT_NAME[c]} ({len(group)})", ""]
        if not group:
            L += ["Không có.", ""]
            continue
        for f in group:
            L += [f"#### {f['id']} – {esc(f['error_type'])}", "", "| Trường | Nội dung |", "|---|---|",
                  f"| Mã lỗi | {esc(f['id'])} |", f"| Tài liệu | {esc(', '.join(f['documents']))} |",
                  f"| Vị trí | {esc('; '.join(f['locations']))} |", f"| Nội dung gốc | {esc(f['original'])} |",
                  f"| Nội dung đối chiếu | {esc(f['compare'])} |", f"| Loại lỗi | {esc(f['error_type'])} |",
                  f"| Mức độ | {f['severity']} |", f"| Phân tích | {esc(f['analysis'])} |",
                  f"| Đề xuất | {esc(f['suggestion'])} |", ""]
    L += ["## 4. Giới hạn của lần kiểm tra", ""]
    L += [f"- {x}" for x in (meta.get("limitations") or DEFAULT_LIMITS)]
    for w in data.get("warnings", []):
        L.append(f"- {w}")
    if dismissed:
        L += ["", "## 5. Cảnh báo tự động đã loại trừ", "", "| Mã | Lý do loại trừ |", "|---|---|"]
        L += [f"| {esc(k)} | {esc(v)} |" for k, v in dismissed.items()]
    return "\n".join(L) + "\n"


def build_xlsx(path, items, files):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "Tổng hợp lỗi"
    head = ["Mã lỗi", "Nhóm", "Mức độ", "Loại lỗi", "Tài liệu", "Vị trí", "Nội dung gốc", "Nội dung đối chiếu",
            "Phân tích", "Đề xuất", "Nguồn phát hiện", "Trạng thái xử lý"]
    ws.append(head)
    fills = {"Critical": "F4B6B6", "High": "F8D5A8", "Medium": "FBF0B0", "Low": "D5E8D4"}
    for f in items:
        ws.append([f["id"], CAT_NAME[f["category"]], f["severity"], f["error_type"], ", ".join(f["documents"]),
                   "\n".join(f["locations"]), f["original"], f["compare"], f["analysis"], f["suggestion"],
                   f.get("source", "claude"), "Chưa xử lý"])
        ws.cell(ws.max_row, 3).fill = PatternFill("solid", fgColor=fills[f["severity"]])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="D9D9D9")
    for col, w in zip("ABCDEFGHIJKL", (9, 22, 10, 30, 28, 32, 50, 50, 50, 40, 12, 14)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    st = wb.create_sheet("Thống kê")
    st.append(["Nhóm"] + SEVERITIES + ["Tổng"])
    for c in CAT_ORDER:
        row = [sum(1 for f in items if f["category"] == c and f["severity"] == s) for s in SEVERITIES]
        st.append([CAT_NAME[c]] + row + [sum(row)])
    st.append(["Tổng"] + [sum(1 for f in items if f["severity"] == s) for s in SEVERITIES] + [len(items)])
    for c in st[1]:
        c.font = Font(bold=True)
    st.column_dimensions["A"].width = 26
    wb.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("findings", help="file JSON phát hiện")
    ap.add_argument("--outdir", default="workspace/output")
    ap.add_argument("--name", default=f"{datetime.now():%Y%m%d}_bao-cao-kiem-tra")
    ap.add_argument("--no-xlsx", action="store_true")
    a = ap.parse_args()
    try:
        data, meta, items, dismissed = load_findings(a.findings)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"[LỖI] {e}", file=sys.stderr)
        sys.exit(2)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = unique_path(out / f"{a.name}.md")
    md_path.write_text(build_markdown(data, meta, items, dismissed), encoding="utf-8")
    docx_path = unique_path(out / f"{a.name}.docx")
    md_to_docx.convert_file(md_path, docx_path, "baocao", header="Báo cáo kiểm tra tài liệu")
    made = [md_path, docx_path]
    if not a.no_xlsx:
        xlsx_path = unique_path(out / f"{a.name}.xlsx")
        build_xlsx(xlsx_path, items, data.get("files", []))
        made.append(xlsx_path)
    print("Đã tạo:\n  " + "\n  ".join(map(str, made)))


if __name__ == "__main__":
    main()
