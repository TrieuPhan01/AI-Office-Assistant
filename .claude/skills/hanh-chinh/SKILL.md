---
name: hanh-chinh
description: Soạn thảo, chuẩn hóa và rà soát văn bản hành chính và văn bản doanh nghiệp tiếng Việt (công văn, thông báo, quyết định, tờ trình, biên bản, báo cáo, kế hoạch, đề xuất). Dùng khi người dùng yêu cầu soạn, viết, sửa, chuẩn hóa văn phong, kiểm tra chính tả/ngữ pháp, hoặc làm văn bản gửi cơ quan, đối tác, nội bộ.
---

# Skill: Soạn thảo văn bản hành chính

## Nguyên tắc cứng
- Văn phong hành chính: trang trọng, súc tích, khách quan; không cảm tính, không khoa trương, không câu dài lê thê.
- **Không tự tạo**: số/ký hiệu văn bản, ngày ban hành, tên người ký, chức vụ người ký, số liệu, căn cứ pháp lý. Thiếu thì ghi đúng cú pháp `[CẦN BỔ SUNG: mô tả ngắn]` (script sẽ tô vàng trong Word).
- **Không thêm thông tin** ngoài dữ liệu người dùng cung cấp. Suy luận hợp lý thì nêu ở phần ghi chú, không đưa vào văn bản.
- Căn cứ pháp lý đưa vào văn bản phải qua skill `phap-ly-viet-nam` (xác minh số hiệu, hiệu lực). Chưa xác minh được thì để `[CẦN BỔ SUNG: căn cứ ...]`.

## Quy trình
1. **Xác định**: loại văn bản, người nhận, mục đích, cấp ký, mức độ trang trọng. Thiếu điều cốt lõi (ai gửi/gửi ai/về việc gì) thì hỏi ngắn; còn lại cứ làm và đánh dấu chỗ thiếu.
2. **Chọn cấu trúc** theo bảng dưới (mẫu có sẵn trong `references/administrative/`; nếu người dùng đưa biểu mẫu riêng của đơn vị thì ưu tiên biểu mẫu đó).
3. **Viết** vào file Markdown `workspace/output/YYYYMMDD_<tên>.md`.
4. **Rà soát**: chính tả/dấu, ngữ pháp, thuật ngữ nhất quán, tiêu đề khớp nội dung, số liệu và ngày tháng khớp nhau, danh sách đánh số liên tục, không còn câu thừa/lặp.
5. **Xuất DOCX**: `python scripts/md_to_docx.py workspace/output/<tên>.md -o workspace/output/<tên>.docx --profile hanhchinh`
6. **Kiểm tra**: `python scripts/document_validator.py workspace/output/<tên>.docx --type admin`
7. **Trả lời ngắn**: đường dẫn file, tóm tắt 1–2 câu, **danh sách các chỗ `[CẦN BỔ SUNG]`** người dùng phải điền.

## Cấu trúc theo loại văn bản
| Loại | Các phần chính |
|---|---|
| Công văn | Quốc hiệu - Tiêu ngữ; tên cơ quan, Số; địa danh, ngày; V/v (trích yếu); Kính gửi; nội dung (lý do → đề nghị/nội dung chính → mong muốn phản hồi); nơi nhận; chữ ký |
| Thông báo | Tên cơ quan, Số; THÔNG BÁO + V/v; nội dung (căn cứ, nội dung thông báo, thời gian, đối tượng, tổ chức thực hiện); nơi nhận; chữ ký |
| Quyết định | Quốc hiệu; tên cơ quan; QUYẾT ĐỊNH + trích yếu; căn cứ; Điều 1, 2, … (nội dung, hiệu lực, trách nhiệm thi hành); nơi nhận; chữ ký |
| Tờ trình | Kính gửi; sự cần thiết; nội dung đề xuất; phương án/so sánh nếu có; kiến nghị; phụ lục kèm theo; chữ ký |
| Biên bản | Tên biên bản; thời gian, địa điểm; thành phần tham dự; nội dung diễn biến; kết luận/thống nhất; giờ kết thúc; chữ ký các bên |
| Báo cáo | Căn cứ/mục đích; tình hình, kết quả (số liệu có nguồn); tồn tại, nguyên nhân; kiến nghị; phụ lục |
| Kế hoạch | Mục đích, yêu cầu; nội dung và tiến độ (bảng: việc – người phụ trách – thời hạn); nguồn lực; tổ chức thực hiện |
| Đề xuất | Vấn đề; mục tiêu; giải pháp; lợi ích/rủi ro; nguồn lực; kiến nghị |

Thể thức (Quốc hiệu, tiêu ngữ, lề, cỡ chữ, vị trí chữ ký) tham chiếu quy định về công tác văn thư, hiện là Nghị định 30/2020/NĐ-CP. **Quy định này có thể đã được sửa đổi/thay thế; nếu văn bản gửi cơ quan nhà nước, hãy chạy `phap-ly-viet-nam` để xác minh hiệu lực trước khi khẳng định thể thức.** Văn bản nội bộ doanh nghiệp theo quy chế của đơn vị.

## Mẫu đầu công văn (Markdown, bảng có hàng tiêu đề trống = bảng không viền)
```markdown
| | |
|:---:|:---:|
| **TÊN CƠ QUAN/DOANH NGHIỆP**<br>Số: [CẦN BỔ SUNG: số, ký hiệu] | **CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**<br>**Độc lập - Tự do - Hạnh phúc** |

<p align="right">[CẦN BỔ SUNG: địa danh], ngày [CẦN BỔ SUNG] tháng [CẦN BỔ SUNG] năm [CẦN BỔ SUNG]</p>

<p align="center">**V/v [trích yếu]**</p>

**Kính gửi:** [CẦN BỔ SUNG: đơn vị nhận]
```

## Văn phong – lỗi thường gặp cần sửa
- Câu dài nhiều ý → tách câu; mỗi đoạn một ý chính.
- Từ khẩu ngữ ("nhờ", "cho em hỏi") → "đề nghị", "kính đề nghị".
- Chủ ngữ mơ hồ ("chúng tôi", "bên này") → ghi rõ tên đơn vị lần đầu, sau đó dùng tên gọi tắt thống nhất.
- Số/ngày: viết thống nhất (ví dụ `15/03/2026`; số tiền `150.000.000 đồng`, kèm bằng chữ nếu là giá trị hợp đồng).
- Viết hoa tên cơ quan, chức danh đúng thông lệ; không viết hoa tùy tiện.

## Khi người dùng đưa văn bản có sẵn để chỉnh sửa
Đọc bằng `python scripts/extract_docx.py <file> --format text`; sửa trên **bản sao**; nêu danh sách thay đổi (trước → sau, lý do). Muốn giữ nguyên bố cục gốc của file Word: dùng skill `word-expert` (sửa trực tiếp bản sao bằng python-docx), không dựng lại từ Markdown.
