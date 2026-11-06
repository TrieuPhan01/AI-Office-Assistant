---
name: word-expert
description: Xử lý tài liệu Microsoft Word và PDF - đọc DOCX/PDF, tạo DOCX từ nội dung, chỉnh sửa nội dung Word mà giữ nguyên bố cục, chuẩn hóa font/cỡ chữ/lề/căn đoạn, tiêu đề, mục lục, bảng biểu, đánh số trang, header/footer, xuất PDF. Dùng khi người dùng đưa file .docx/.pdf hoặc yêu cầu tạo/sửa/chuẩn hóa/xuất file Word hoặc PDF.
---

# Skill: Word & PDF

Công cụ: `python-docx` (DOCX), `PyMuPDF`/`pdftotext`/`pdfplumber` (đọc PDF), LibreOffice (`soffice`) để xuất PDF. Chưa có thư viện nào thì báo người dùng cách cài, **không tự cài khi chưa được phép**.

## Nguyên tắc
- **File gốc không bao giờ bị sửa.** Luôn làm trên bản sao ghi vào `workspace/output/` (không ghi đè file đã có: thêm `_v2`, `_v3`).
- **Không phá bố cục, không tự xóa nội dung, không đổi ý nghĩa.** Giữ nguyên bảng, hình, header/footer, trường (field) nếu không được yêu cầu.
- Sau khi tạo/sửa luôn **mở lại và kiểm tra**: `python scripts/document_validator.py <file>` (và so sánh trước/sau khi chuẩn hóa).
- Muốn đổi nội dung (không chỉ định dạng) → liệt kê thay đổi trước → sau cho người dùng.

## Việc thường gặp

### 1. Đọc nội dung
```bash
python scripts/extract_docx.py <file.docx> --format text      # xem nhanh
python scripts/extract_docx.py <file.docx> -o out.json         # có vị trí đoạn/bảng
python scripts/extract_pdf.py  <file.pdf>  --format text       # PDF: tự chọn engine đọc tốt nhất
```
PDF báo `needs_ocr` = bản scan → **dừng và báo**; cần OCR (ví dụ `ocrmypdf`, Tesseract) trước. PDF báo `garble_score` > 0 = có nghi lỗi dấu tiếng Việt → nói rõ độ tin cậy thấp, thử `--engine pdftotext` / `--engine pymupdf`.

### 2. Tạo DOCX mới từ nội dung
Viết Markdown rồi chuyển:
```bash
python scripts/md_to_docx.py <file.md> -o workspace/output/<tên>.docx --profile hanhchinh   # hoặc baocao
# tùy chọn: --font "Times New Roman" --size 13 --landscape --header "Tên văn bản" --no-page-numbers
```
Hỗ trợ: tiêu đề `#`–`####`, đoạn văn, **đậm**/*nghiêng*, danh sách, bảng (căn lề `:---:`), ảnh `![mô tả](đường-dẫn)`, `[TOC]` (mục lục: Word sẽ hỏi cập nhật trường khi mở; nhấn F9 để cập nhật), `<!-- pagebreak -->`, `<p align="center|right">…</p>`, bảng có hàng tiêu đề trống = bảng không viền (đầu công văn). Ghi chú: `[CẦN BỔ SUNG: …]` tự tô vàng.

### 3. Chuẩn hóa định dạng file Word có sẵn (không đổi nội dung)
```bash
python scripts/docx_standardize.py workspace/input/a.docx -o workspace/output/a_chuan.docx \
   --font "Times New Roman" --size 13 --margins 20,20,30,20 --align justify --line-spacing 1.15 \
   --first-indent-mm 12.7 --page-numbers
```
Script tự kiểm tra văn bản trước/sau giống hệt nhau, không ghi đè file gốc; tiêu đề, đoạn căn giữa/phải và cỡ chữ trong bảng được giữ nguyên (trừ khi dùng `--table-size`).

### 4. Sửa nội dung một file Word giữ nguyên bố cục
Sao chép file gốc sang `workspace/output/`, mở bằng python-docx và **sửa ở mức run** để giữ định dạng:
```python
from docx import Document
doc = Document("workspace/output/a_v2.docx")
for p in doc.paragraphs:
    for r in p.runs:
        if "Công ty ABD" in r.text:
            r.text = r.text.replace("Công ty ABD", "Công ty ABC")   # giữ nguyên font/đậm/nghiêng của run
doc.save("workspace/output/a_v2.docx")
```
Lưu ý: cụm cần sửa có thể bị tách ra nhiều run → gộp text các run của đoạn để tìm, rồi đặt lại vào run đầu và xóa phần thừa ở các run sau (giữ định dạng run đầu). Bảng: duyệt `doc.tables → rows → cells → paragraphs`. Không dùng `paragraph.text = …` cho đoạn có định dạng hỗn hợp (làm mất định dạng). Sửa xong chạy lại `extract_docx.py` hai bản và so sánh để liệt kê **đúng các thay đổi** đã làm.

### 5. Xuất PDF
```bash
soffice --headless --convert-to pdf --outdir workspace/output workspace/output/<tên>.docx
```
Kiểm tra PDF đã tạo (`extract_pdf.py --format text`, số trang hợp lý). Font chưa cài trên máy có thể bị thay thế, nói rõ nếu bố cục thay đổi.

### 6. Tiện ích khác (viết ngắn bằng python-docx khi cần)
- Header/footer, số trang: `section.header`, `section.footer`; số trang dùng trường `PAGE` (xem `add_field` trong `scripts/md_to_docx.py`).
- Mục lục: tiêu đề phải dùng style `Heading 1–3`; chèn bằng `[TOC]` trong Markdown.
- Bảng: dùng style `Table Grid`, lặp hàng tiêu đề (`w:tblHeader`), không cho hàng ngắt trang (`w:cantSplit`).
- Gộp/tách file Word phức tạp, theo dõi thay đổi (tracked changes), chữ ký số: ngoài phạm vi script; báo rõ giới hạn.

## Khuyến nghị thể thức mặc định
Times New Roman, cỡ 13, giãn dòng 1,15–1,3, lề trên/dưới 20 mm, trái 30 mm, phải 15–20 mm (có thể điều chỉnh theo quy định đơn vị). Quy định thể thức văn bản nhà nước phải được xác minh hiệu lực qua skill `phap-ly-viet-nam`.
