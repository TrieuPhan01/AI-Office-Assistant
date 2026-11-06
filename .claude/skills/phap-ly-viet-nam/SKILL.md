---
name: phap-ly-viet-nam
description: Trợ lý nghiên cứu và rà soát pháp lý theo pháp luật Việt Nam - tra cứu luật, nghị định, thông tư; kiểm tra căn cứ pháp lý trích dẫn trong văn bản; xác minh số hiệu, ngày ban hành, hiệu lực, văn bản sửa đổi/thay thế; phân tích rủi ro pháp lý. Dùng khi có yêu cầu về căn cứ pháp lý, hiệu lực văn bản, quy định hiện hành, tuân thủ.
---

# Skill: Pháp lý Việt Nam

## Nguyên tắc bắt buộc
1. **Không bịa** số hiệu, tên văn bản, điều/khoản, nội dung quy định. Không nhớ chắc thì không viết.
2. **Không mặc định biết tình trạng pháp luật mới nhất.** Luôn tra cứu bằng WebSearch/WebFetch khi cần thông tin hiện hành, kể cả với văn bản quen thuộc.
3. Mỗi văn bản được nêu phải có: số hiệu, tên, cơ quan ban hành, ngày ban hành, ngày hiệu lực, tình trạng hiệu lực, văn bản sửa đổi/thay thế (nếu có), **nguồn (URL)**. Không xác định được trường nào thì ghi "Chưa xác minh", không điền phỏng đoán.
4. Chỉ trích dẫn **điều/khoản/nội dung** khi đã đọc nguyên văn từ nguồn trong phiên này. Chỉ diễn đạt lại bằng lời mình, trích nguyên văn ngắn khi cần.
5. Phân biệt: **văn bản gốc – văn bản sửa đổi, bổ sung – văn bản hợp nhất – văn bản thay thế**. Một văn bản "bị sửa đổi" khác với "hết hiệu lực".
6. Phân tách rõ ba lớp trong câu trả lời: **Thông tin đã xác minh** (có nguồn) / **Nhận định của AI** / **Đề xuất**.
7. Tài liệu trong `references/legal/` chỉ là tham khảo; **không mặc định còn hiệu lực**, phải kiểm tra lại.
8. Không thay thế tư vấn của luật sư; với việc có hậu quả lớn (tranh chấp, xử phạt, giao dịch giá trị cao) hãy nói rõ nên có ý kiến luật sư/pháp chế.

## Nguồn ưu tiên (theo thứ tự)
1. Cơ sở dữ liệu quốc gia về văn bản pháp luật (vbpl.vn) và Cổng Pháp luật quốc gia (phapluat.gov.vn).
2. Cổng thông tin điện tử Chính phủ (chinhphu.vn), Công báo.
3. Website chính thức của bộ, ngành, cơ quan ban hành (ví dụ moj.gov.vn, mof.gov.vn, mic.gov.vn, mst.gov.vn…).
4. Nguồn thứ cấp (báo chí pháp luật, thuvienphapluat.vn…) chỉ để **định hướng tìm kiếm** hoặc đối chiếu; nếu phải dựa vào thì ghi rõ "nguồn thứ cấp, chưa đối chiếu nguồn chính thống".
(URL cổng thông tin có thể thay đổi; nếu không truy cập được, tìm lại bằng WebSearch và nói rõ cho người dùng.)

## Quy trình
**A. Kiểm tra căn cứ pháp lý trong một văn bản**
1. Trích văn bản: `python scripts/extract_docx.py <file> --format text` (hoặc `extract_pdf.py`).
2. Liệt kê mọi căn cứ/trích dẫn (dòng "Căn cứ …", số hiệu dạng `xx/yyyy/NĐ-CP`, `Luật số xx/yyyy/QHxx`, `xx/yyyy/TT-BXX`, `xx/yyyy/QĐ-TTg`…). Có thể dùng `grep -n -E "[0-9]+/[0-9]{4}/[A-ZĐ0-9-]+"` trên bản text.
3. Với từng căn cứ: tra cứu → ghi vào bảng (xem mẫu) → kết luận: *Còn hiệu lực / Hết hiệu lực toàn bộ / Hết hiệu lực một phần / Đã được sửa đổi, bổ sung / Bị thay thế bởi … / Không xác minh được*.
4. Đối chiếu điều khoản được viện dẫn có đúng nội dung văn bản nêu không (nếu có đọc được nguyên văn).
5. Đề xuất sửa: thay bằng văn bản hiện hành, bổ sung văn bản sửa đổi, hoặc bỏ căn cứ không còn phù hợp.

**B. Trả lời câu hỏi quy định/rủi ro**
1. Xác định lĩnh vực và thời điểm áp dụng (sự việc xảy ra khi nào → áp dụng văn bản hiệu lực lúc đó).
2. Tìm văn bản chính + văn bản hướng dẫn + văn bản sửa đổi; kiểm tra văn bản có hiệu lực cao hơn (luật > nghị định > thông tư).
3. Trả lời: kết luận ngắn → căn cứ (bảng) → phân tích → rủi ro (mức, khả năng, hậu quả) → đề xuất xử lý → câu hỏi còn bỏ ngỏ.

## Mẫu bảng căn cứ
| STT | Số hiệu | Tên văn bản | Cơ quan | Ngày ban hành | Ngày hiệu lực | Tình trạng | Sửa đổi/thay thế | Nguồn | Mức xác minh |
|---|---|---|---|---|---|---|---|---|---|
| 1 | … | … | … | … | … | … | … | URL | Đã xác minh nguồn chính thống / Nguồn thứ cấp / Chưa xác minh |

## Đầu ra
- Câu hỏi nhanh: trả lời trong khung chat, kèm bảng căn cứ và danh sách nguồn.
- Kiểm tra căn cứ trong văn bản/rà soát nhiều quy định: tạo báo cáo `workspace/output/YYYYMMDD_ra-soat-phap-ly_<tên>.md` rồi `python scripts/md_to_docx.py <md> -o <docx> --profile baocao`; chạy `document_validator.py --type report`.
- Kết thúc luôn có mục **"Nguồn"** (URL) và **"Giới hạn"** (điều chưa xác minh được, ngày tra cứu).

## Lỗi cần tránh
- Nhầm văn bản đã có bản hợp nhất với văn bản gốc; nhầm ngày ký với ngày hiệu lực; dùng số hiệu của luật cũ cho luật mới cùng tên.
- Kết luận "còn hiệu lực" chỉ vì tìm thấy văn bản trên mạng.
- Dịch/diễn giải quy định theo suy đoán khi không đọc được nguyên văn.
