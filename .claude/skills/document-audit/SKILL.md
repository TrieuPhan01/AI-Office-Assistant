---
name: document-audit
description: Kiểm tra tính đồng nhất và nhất quán giữa nhiều tài liệu Word/PDF (hợp đồng, phụ lục, biên bản, quyết định, báo giá) - đối chiếu tên công ty, mã số thuế, số hợp đồng, ngày tháng, số tiền, điều khoản, phát hiện mâu thuẫn, sai số học, thiếu sót. Dùng khi người dùng đưa từ 2 tài liệu trở lên và hỏi có thống nhất, khớp, mâu thuẫn, sai sót không.
---

# Skill: Document Audit (kiểm tra đồng nhất nhiều tài liệu)

Kết hợp **máy** (script xác định, lặp lại được) và **Claude** (ngữ nghĩa, đánh giá, loại cảnh báo sai). Không dùng riêng Claude để "đọc lướt rồi so sánh".

## Nguyên tắc
- **Không sửa tài liệu gốc.** Chỉ đọc; kết quả là báo cáo mới trong `workspace/output/`.
- Mỗi phát hiện phải có **bằng chứng** (trích đoạn + vị trí trang/đoạn/bảng). Không có bằng chứng thì không đưa vào.
- Phân loại đúng 4 nhóm, không trộn:
  - `certain` – **Lỗi chắc chắn**: bằng chứng rõ (sai số học, số bằng số ≠ bằng chữ, ngày không tồn tại, hai giá trị hầu như giống nhau nhưng lệch 1–2 ký tự…).
  - `verify` – **Khác biệt cần xác minh**: khác nhau nhưng chưa đủ cơ sở kết luận bên nào sai (có thể là hai đối tượng khác nhau, hoặc phụ lục sửa đổi có chủ đích).
  - `logic` – **Cảnh báo logic**: dấu hiệu bất hợp lý (kết thúc trước hiệu lực, ký sau khi hiệu lực…).
  - `suggestion` – **Đề xuất cải thiện**: không sai nhưng nên thống nhất (hoa/thường, cách viết ngày…).
- Mức độ (Critical/High/Medium/Low): theo `references/severity-levels.md`. Quy tắc so sánh của script: `references/comparison-rules.md`.

## Quy trình
1. **Liệt kê & kiểm tra đầu vào**: file trong `workspace/input/` (hoặc đường dẫn người dùng nêu). Xác định loại/vai trò từng file (hợp đồng chính, phụ lục, biên bản…). Báo ngay nếu có PDF scan (script sẽ cảnh báo `needs_ocr`) hoặc file hỏng/có mật khẩu: không đoán nội dung, hỏi người dùng cung cấp bản đọc được/OCR.
2. **Chạy so sánh tự động**:
   `python scripts/compare_documents.py workspace/input/*.docx workspace/input/*.pdf -o workspace/output/<tên>_raw.json`
3. **Đọc kết quả raw** (`findings`, `inventory`, `warnings`). Với mỗi phát hiện, mở lại đoạn gốc (`python scripts/extract_docx.py <file> --format text` hoặc `extract_pdf.py`) để **xác thực**; script là heuristic nên có cảnh báo thừa. Ví dụ MST khác nhau là bình thường khi đó là hai bên khác nhau; PDF có thể bị lỗi mã hóa dấu (xem `warnings`, `garble_score`).
4. **Phân tích ngữ nghĩa bằng Claude** trên toàn văn các tài liệu (script không làm được): mâu thuẫn điều khoản, phụ lục ↔ hợp đồng, biên bản ↔ quyết định, tham chiếu chéo đúng/sai, thông tin bị thiếu, cùng một nội dung mô tả khác nhau, phủ định/đổi nghĩa, thời hạn–tiến độ–thanh toán có hợp lý không, tổng tiền và thuế có khớp chi tiết không (tự tính lại).
5. **Lập file kết luận** `workspace/output/<tên>_final.json`: lấy `findings` của raw, **xóa** cảnh báo sai (đưa vào `meta.dismissed` kèm lý do), chỉnh `category/severity/analysis/suggestion`, **thêm** phát hiện ngữ nghĩa của mình (không có `id`, đặt `"source": "claude"`). Cấu trúc:
```json
{"files": ["a.docx", "b.docx"],
 "meta": {"title": "…", "summary": "2–4 câu tóm tắt", "limitations": ["…"],
          "dismissed": [{"id": "F-004", "reason": "hai bên khác nhau nên MST khác nhau"}]},
 "warnings": [],
 "findings": [{"category": "verify", "severity": "High", "error_type": "…",
   "documents": ["…"], "locations": ["file – Điều 3, đoạn 12"], "original": "trích gốc",
   "compare": "trích đối chiếu", "analysis": "…", "suggestion": "…", "source": "claude"}]}
```
6. **Xuất báo cáo** (DOCX + Markdown + Excel):
   `python scripts/build_audit_report.py workspace/output/<tên>_final.json --outdir workspace/output --name <YYYYMMDD>_kiem-tra-<tên>`
7. **Kiểm tra báo cáo**: `python scripts/document_validator.py workspace/output/<tên>.docx workspace/output/<tên>.md --type audit`
8. **Trả lời**: đường dẫn 3 file, số phát hiện theo nhóm/mức độ, **3–5 phát hiện nghiêm trọng nhất** (1 dòng mỗi cái), giới hạn của lần kiểm tra (chữ trong ảnh, PDF scan, đoạn không đọc được).

## Phạm vi kiểm tra (đủ cả 4 nhóm)
- **Định danh**: tên công ty, cá nhân, chức danh, địa chỉ, MST, số hợp đồng/văn bản, mã khách hàng/dự án.
- **Dữ liệu**: ngày, thời hạn, số tiền, đơn giá, số lượng, %, tổng, thuế.
- **Nội dung**: thống nhất giữa các văn bản, điều khoản xung đột, phụ lục–hợp đồng, biên bản–quyết định, tham chiếu chéo, thiếu sót.
- **Logic**: thời hạn hợp lý, ngày ký–hiệu lực, tổng khớp chi tiết, phủ định/đổi nghĩa.
Script tự phủ phần lớn nhóm định danh/dữ liệu/logic số học; phần **nội dung** là việc của Claude (bước 4). Mã khách hàng/mã dự án chưa có bộ nhận diện riêng: tìm thủ công bằng grep trên bản text rồi đối chiếu.

## Quy tắc trình bày phát hiện
- `original` = trích nguyên văn ngắn của tài liệu "gốc" (thường là hợp đồng chính); `compare` = trích ở tài liệu khác. Luôn kèm vị trí.
- `analysis` nói rõ **vì sao** là vấn đề và **chưa biết bên nào đúng** nếu đúng như vậy; không khẳng định quá mức.
- `suggestion` cụ thể: đối chiếu với giấy tờ gốc nào, sửa ở tài liệu nào.
- Cùng một nguyên nhân gốc thì gộp một phát hiện (ví dụ MST sai lặp ở 3 file), liệt kê đủ vị trí.
- Nhiều tài liệu (> 10) hoặc dài: chạy theo cặp/nhóm theo loại, rồi tổng hợp; nói rõ nếu chưa đọc hết.
