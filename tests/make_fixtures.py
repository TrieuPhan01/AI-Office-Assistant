#!/usr/bin/env python3
"""Tạo 3 file DOCX mẫu có CÀI SẴN lỗi để kiểm thử Document Audit.

  python tests/make_fixtures.py workspace/input     # tạo ra thư mục để thử thủ công

Lỗi đã cài (xem EXPECTED trong test_all.py):
  - Phụ lục: MST 0312345687 (đảo 2 chữ số so với 0312345678 của hợp đồng)
  - Phụ lục: số hợp đồng dẫn chiếu ...ABD thay vì ...ABC
  - Phụ lục: tên công ty thiếu dấu (MAI thay vì MẠI)
  - Phụ lục: tổng giá trị 105.000.000 (hợp đồng: 150.000.000), bằng chữ "một trăm năm mươi triệu" không khớp
  - Phụ lục: chức danh ông Nguyễn Văn An là "Tổng Giám đốc" (hợp đồng: "Giám đốc")
  - Phụ lục: ngày kết thúc 30/03/2027 (hợp đồng: 31/03/2027)
  - Phụ lục: bảng 4 × 2.500.000 ghi 12.000.000; tổng bảng sai
  - Biên bản: ngày 31/02/2026 không tồn tại; hiệu lực 10/05/2026 đến 10/04/2026 (kết thúc trước hiệu lực)
  - Biên bản: thuế GTGT 8% (hợp đồng: 10%); viết hoa/thường tên công ty khác; địa chỉ viết khác
"""
import sys
from pathlib import Path

from docx import Document


def _table(doc, rows):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            t.cell(i, j).text = v
    return t


def hop_dong(path):
    d = Document()
    for line in [
        "HỢP ĐỒNG MUA BÁN HÀNG HÓA",
        "Số: 123/2026/HĐMB-ABC",
        "Hà Nội, ngày 15 tháng 03 năm 2026",
        "BÊN A: CÔNG TY TNHH THƯƠNG MẠI ABC",
        "Địa chỉ: 12 Nguyễn Trãi, Quận 1, TP. Hồ Chí Minh",
        "Mã số thuế: 0312345678",
        "Đại diện: Ông Nguyễn Văn An",
        "Chức vụ: Giám đốc",
        "BÊN B: CÔNG TY CỔ PHẦN XÂY DỰNG XYZ",
        "Mã số thuế: 0109876543",
        "Đại diện: Bà Trần Thị Bình",
        "Chức vụ: Phó Giám đốc",
        "Điều 1. Giá trị hợp đồng",
        "Tổng giá trị hợp đồng là 150.000.000 đồng (Bằng chữ: Một trăm năm mươi triệu đồng chẵn), "
        "đã bao gồm thuế GTGT 10%.",
        "Điều 2. Thời hạn",
        "Hợp đồng có hiệu lực từ ngày 01/04/2026 đến ngày 31/03/2027.",
        "Điều 3. Thanh toán",
        "Bên A tạm ứng cho Bên B 30% giá trị hợp đồng sau khi ký.",
    ]:
        d.add_paragraph(line)
    _table(d, [["STT", "Tên hàng", "Số lượng", "Đơn giá", "Thành tiền"],
               ["1", "Máy A", "10", "5.000.000", "50.000.000"],
               ["2", "Máy B", "20", "5.000.000", "100.000.000"],
               ["", "Tổng cộng", "", "", "150.000.000"]])
    d.save(path)


def phu_luc(path):
    d = Document()
    for line in [
        "PHỤ LỤC 01 – HỢP ĐỒNG MUA BÁN HÀNG HÓA",
        "Số: 01/PL-123/2026",
        "Căn cứ Hợp đồng số 123/2026/HĐMB-ABD ngày 15 tháng 03 năm 2026.",
        "BÊN A: CÔNG TY TNHH THƯƠNG MAI ABC",
        "Địa chỉ: 12 Nguyễn Trãi, Quận 1, TP. Hồ Chí Minh",
        "Mã số thuế: 0312345687",
        "Đại diện: Ông Nguyễn Văn An",
        "Chức vụ: Tổng Giám đốc",
        "BÊN B: CÔNG TY CỔ PHẦN XÂY DỰNG XYZ",
        "Mã số thuế: 0109876543",
        "Điều 1. Điều chỉnh giá trị",
        "Tổng giá trị hợp đồng sau điều chỉnh là 105.000.000 đồng (Bằng chữ: Một trăm năm mươi triệu đồng chẵn).",
        "Điều 2. Thời hạn",
        "Hợp đồng có hiệu lực từ ngày 01/04/2026 đến ngày 30/03/2027.",
    ]:
        d.add_paragraph(line)
    _table(d, [["STT", "Tên hàng", "Số lượng", "Đơn giá", "Thành tiền"],
               ["1", "Máy C", "4", "2.500.000", "12.000.000"],
               ["2", "Máy D", "4", "5.000.000", "20.000.000"],
               ["", "Tổng cộng", "", "", "31.000.000"]])
    d.save(path)


def bien_ban(path):
    d = Document()
    for line in [
        "BIÊN BẢN NGHIỆM THU",
        "Số: 05/BBNT-2026",
        "Căn cứ Hợp đồng số 123/2026/HĐMB-ABC.",
        "Lập tại TP. Hồ Chí Minh, ngày 31/02/2026.",
        "Đại diện Bên A: Công ty TNHH Thương mại ABC",
        "Địa chỉ: 12 Nguyễn Trãi, Quận 1, TP.HCM",
        "Mã số thuế: 0312345678",
        "Đại diện Bên B: CÔNG TY CỔ PHẦN XÂY DỰNG XYZ",
        "Biên bản này có hiệu lực từ ngày 10/05/2026 đến ngày 10/04/2026.",
        "Giá trị nghiệm thu đã bao gồm thuế GTGT 8%.",
    ]:
        d.add_paragraph(line)
    d.save(path)


def make_all(outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = [out / "01_hop-dong.docx", out / "02_phu-luc.docx", out / "03_bien-ban.docx"]
    for fn, p in zip((hop_dong, phu_luc, bien_ban), paths):
        fn(p)
    return paths


if __name__ == "__main__":
    for p in make_all(sys.argv[1] if len(sys.argv) > 1 else "workspace/input"):
        print("Đã tạo", p)
