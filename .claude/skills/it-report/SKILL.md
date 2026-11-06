---
name: it-report
description: Phân tích và viết báo cáo công nghệ thông tin - hiện trạng hệ thống, phân tích nghiệp vụ, đề xuất giải pháp phần mềm/kiến trúc, thiết kế CSDL/API, so sánh công nghệ, server vật lý và cloud, bảo mật, AI/IoT, RFID/QRCode/barcode, nâng cấp ERP, kế hoạch triển khai, chi phí, phương án trình lãnh đạo. Dùng khi cần báo cáo hoặc đề xuất CNTT có cấu trúc.
---

# Skill: Báo cáo & đề xuất công nghệ thông tin

Đối tượng đọc chính: **lãnh đạo không chuyên CNTT** (kèm phụ lục kỹ thuật cho đội kỹ thuật). Chuyên nghiệp, có chiều sâu, ngắn gọn, không nhận định thiếu căn cứ.

## Nguyên tắc
1. **Phân biệt dữ liệu và giả định.** Mọi số liệu đưa vào phải có nguồn: do người dùng cung cấp / từ tài liệu (nêu tên) / từ tra cứu (URL, ngày tra). Điều Claude tự giả định phải gắn nhãn **[Giả định]**; điều chưa có dữ liệu ghi `[CẦN BỔ SUNG: …]`. Không tự bịa giá, số người dùng, hiệu năng, ROI.
2. **Thông tin hiện hành phải tra cứu**: giá cloud/phần mềm, phiên bản, tính năng, lộ trình hỗ trợ, quy định (không dựa trí nhớ). Ghi ngày tra cứu.
3. Mọi đề xuất phải nêu **ít nhất 2 phương án** (kể cả "giữ nguyên hiện trạng"), so sánh theo cùng tiêu chí, rồi mới khuyến nghị.
4. Chi phí/rủi ro chỉ định lượng khi có dữ liệu; nếu không, nêu **mức định tính (Thấp/TB/Cao)** và cách ước lượng cần thêm dữ liệu gì.
5. Không phóng đại lợi ích; nêu rõ điều kiện thành công và rủi ro triển khai.

## Quy trình
1. **Làm rõ** (hỏi ngắn khi thật sự thiếu): bối cảnh doanh nghiệp, hiện trạng, vấn đề, quy mô (người dùng/giao dịch/dữ liệu), ràng buộc (ngân sách, thời hạn, nhân sự, tuân thủ), người đọc là ai. Dùng tài liệu người dùng đưa (đọc bằng `extract_docx.py`/`extract_pdf.py`).
2. **Nghiên cứu** thông tin hiện hành khi cần (WebSearch/WebFetch), ghi nguồn.
3. **Phân tích → so sánh → khuyến nghị.**
4. **Viết** Markdown `workspace/output/YYYYMMDD_<tên>.md` theo cấu trúc dưới.
5. **Xuất DOCX**: `python scripts/md_to_docx.py <md> -o workspace/output/<tên>.docx --profile baocao` (có `[TOC]` đầu tài liệu nếu > 8 trang; ảnh sơ đồ chèn bằng `![mô tả](đường-dẫn.png)`).
6. **Kiểm tra**: `python scripts/document_validator.py <docx> --type report`; tự rà số liệu, tổng, tên gọi nhất quán.
7. **Trả lời ngắn**: file ở đâu, khuyến nghị chính (1–2 câu), danh sách `[CẦN BỔ SUNG]`/giả định cần người dùng xác nhận.

## Cấu trúc báo cáo
1. **Tóm tắt điều hành** (≤ 1/2 trang): vấn đề → khuyến nghị → chi phí/lợi ích chính → việc cần lãnh đạo quyết.
2. **Mục tiêu và phạm vi** (làm gì, không làm gì).
3. **Hiện trạng** (hệ thống, quy trình, số liệu; nguồn).
4. **Phân tích vấn đề** (nguyên nhân, tác động, rủi ro nếu không làm).
5. **Các phương án** (mô tả từng phương án + sơ đồ khi giúp hiểu).
6. **So sánh** (bảng tiêu chí: chức năng đáp ứng, chi phí đầu tư/vận hành, thời gian, rủi ro, khả năng mở rộng, bảo mật, phụ thuộc nhà cung cấp, yêu cầu nhân sự).
7. **Đánh giá chi phí và rủi ro** (khi có dữ liệu; nếu không, định tính + dữ liệu cần thu thập).
8. **Phương án đề xuất** (vì sao; điều kiện; lộ trình/giai đoạn; mốc nghiệm thu).
9. **Kết luận và kiến nghị**.
10. **Phụ lục**: chi tiết kỹ thuật, bảng giá, nguồn tham khảo, giả định.

## Bảng so sánh mẫu
| Tiêu chí | Phương án A | Phương án B | Giữ nguyên hiện trạng |
|---|---|---|---|
| Đáp ứng nghiệp vụ | … | … | … |
| Chi phí đầu tư | [Dữ liệu/Giả định/CẦN BỔ SUNG] | … | … |
| Chi phí vận hành/năm | … | … | … |
| Thời gian triển khai | … | … | … |
| Rủi ro chính | … | … | … |

## Gợi ý theo chủ đề
- **Server vật lý vs Cloud**: TCO nhiều năm (phần cứng, điện, mạng, nhân sự, khấu hao vs thuê bao, băng thông, dung lượng), khả năng mở rộng, SLA, sao lưu/khôi phục, vị trí dữ liệu và yêu cầu pháp lý về dữ liệu, phụ thuộc nhà cung cấp.
- **RFID / QRCode / Barcode / app di động**: môi trường (kim loại, chất lỏng, vải sợi), tốc độ quét hàng loạt, độ chính xác, chi phí tem/đầu đọc, yêu cầu hạ tầng mạng, tích hợp ERP/WMS, nhân sự thao tác; nên có bảng so sánh theo đúng bối cảnh kho.
- **ERP/phần mềm**: mức khớp quy trình, tùy biến vs chuẩn, tích hợp, dữ liệu chuyển đổi, đào tạo, rủi ro triển khai, giấy phép/thuê bao.
- **Bảo mật**: phân quyền, mã hóa, sao lưu, nhật ký, tuân thủ; liệt kê rủi ro theo xác suất × tác động.
- **Thiết kế CSDL/API**: thực thể, quan hệ, khóa, chỉ mục, quy mô dữ liệu; API (endpoint, xác thực, lỗi, phiên bản); trình bày bằng bảng/sơ đồ ER dạng bảng mô tả.
- **AI/IoT**: bài toán rõ ràng, chất lượng dữ liệu, chi phí vận hành, rủi ro đạo đức/quyền riêng tư; không hứa hiệu quả khi chưa có thử nghiệm.

## Sơ đồ
Chỉ vẽ khi **thực sự giúp hiểu** (kiến trúc, luồng quy trình). Cách làm trong môi trường CLI: bảng mô tả luồng "Bước – Hệ thống – Dữ liệu vào/ra", hoặc ảnh PNG tạo bằng thư viện có sẵn (ví dụ matplotlib nếu đã cài) rồi chèn `![](…)`. Không cài thêm thư viện chỉ để vẽ.

## Văn phong
Câu ngắn, chủ động; thuật ngữ kỹ thuật có giải thích trong lần đầu; tránh từ quảng cáo ("tối ưu vượt trội", "tốt nhất") khi không có số liệu; con số kèm đơn vị và nguồn.
