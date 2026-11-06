# Quy tắc so sánh của `scripts/compare_documents.py`

Tài liệu này mô tả script **làm gì** để Claude biết khi nào tin, khi nào phải kiểm lại.

## 1. Chuẩn hóa trước khi so sánh
- Văn bản chuẩn hóa Unicode NFC (tránh dấu tiếng Việt dạng tổ hợp làm "khác" giả).
- Tên công ty / người / địa chỉ: bỏ dấu câu, hạ chữ thường, **bỏ khoảng trắng** (PDF hay chèn khoảng trắng thừa trong từ như "PHẦ N").
- Số tiền: bỏ dấu chấm/phẩy ngăn cách → số nguyên; chỉ nhận số có ngăn cách nghìn hoặc số ≥ 5 chữ số **kèm đơn vị** (đồng/VNĐ/VND/USD). Số trần (số điện thoại, tài khoản) bị bỏ qua. Dưới 1.000 bị bỏ qua.
- Ngày: `dd/mm/yyyy`, `dd-mm-yyyy`, `dd.mm.yyyy`, "ngày dd tháng mm năm yyyy" → ISO `yyyy-mm-dd`; ngày không tồn tại (31/02) bị đánh dấu.
- Số hợp đồng/văn bản: viết hoa, phải có chữ số và có `/` hoặc `-`.

## 2. Nhãn ngữ cảnh (để biết "cùng một loại giá trị")
Nhãn lấy theo từ khóa gần nhất **đứng trước** giá trị (50–70 ký tự):
| Loại | Nhãn | Từ khóa |
|---|---|---|
| Tiền | `total` | tổng, giá trị hợp đồng, giá trị thanh toán, cộng tiền |
| | `tax` | thuế, VAT, GTGT |
| | `deposit` | đặt cọc, tạm ứng, bảo đảm, bảo lãnh |
| | `unit_price`, `line_amount` | đơn giá, thành tiền |
| Ngày | `sign` | ký, lập tại, ban hành, làm tại |
| | `effective` | hiệu lực, bắt đầu, từ ngày |
| | `end` | kết thúc, hết hạn, đến ngày, chấm dứt, đáo hạn |
| % | `vat`, `penalty`, `deposit`, `discount` | thuế/VAT, phạt/lãi, cọc/tạm ứng, chiết khấu |
**Hạn chế**: nhãn sai khi từ khóa nằm xa hoặc câu phức; ngày/tiền không có nhãn chỉ được kiểm tra các quy tắc không cần nhãn. Luôn xác thực bằng bản gốc.

## 3. Các phép kiểm tra
| Phép kiểm tra | Nhóm kết quả | Mức mặc định |
|---|---|---|
| MST sai độ dài (≠ 10/13 số) | certain | Medium |
| Hai MST khác nhau ≤ 2 ký tự và không cùng xuất hiện trong một tài liệu | certain | Critical |
| MST chỉ xuất hiện ở một tài liệu (khi các tài liệu khác có MST khác, không gần giống) | verify | Medium |
| Hai số hợp đồng/văn bản khác ≤ 2 ký tự, không cùng một tài liệu | certain | Critical |
| Các tài liệu dẫn chiếu "Hợp đồng số …" khác nhau (không gần giống) | verify | High |
| Tên công ty/người gần giống (≥ 90%) nhưng khác | certain | High |
| Tên công ty chỉ khác dấu tiếng Việt | certain | Medium |
| Tên/địa chỉ giống ≥ 80% nhưng < 90% | verify | High / Medium |
| Tên chỉ khác hoa/thường hoặc dấu câu | suggestion | Low |
| Cùng một người, chức danh khác nhau | verify | High |
| Tổng/thuế/đặt cọc khác nhau giữa tài liệu (lệch kiểu đảo/sai 1 chữ số ⇒ certain) | verify / certain | High / Critical |
| Hai số tiền chỉ khác do đảo 2 chữ số kề nhau ở các tài liệu khác nhau | verify | Medium |
| Ngày ký/hiệu lực/kết thúc khác nhau giữa tài liệu | verify | High |
| Ngày không tồn tại | certain | High |
| Kết thúc trước hiệu lực | logic | High |
| Hiệu lực trước ngày ký | logic | Medium |
| % thuế/phạt/cọc/chiết khấu khác nhau | verify | High (VAT) / Medium |
| Số tiền bằng số ≠ bằng chữ | certain | Critical |
| SL × Đơn giá ≠ Thành tiền (dung sai 1 đồng) | certain | High |
| Tổng bảng ≠ tổng các dòng | certain | High |
| Thuế VAT ≠ % × cơ sở tính | certain | High |
| Tổng thanh toán ≠ cộng tiền hàng + thuế | certain | High |

## 4. Những thứ script KHÔNG làm (Claude phải làm)
- Hiểu nghĩa điều khoản, mâu thuẫn không thể hiện bằng con số/tên.
- Biết hai thực thể có phải cùng một bên hay không (MST khác nhau ở hai bên là bình thường).
- Chữ trong ảnh/chữ ký/con dấu; PDF scan (cần OCR); bảng trong PDF (không dựng lại cấu trúc bảng nên các phép kiểm tra số học theo bảng chỉ áp dụng cho DOCX).
- Mã khách hàng, mã dự án, số lượng/đơn vị tính, tên hàng hóa, điều khoản phạt/bảo hành.
- Đánh giá "hợp lý" của thời hạn, tiến độ, tỷ lệ thanh toán.

## 5. Dấu hiệu cần nghi ngờ chính script
- `warnings` có `needs_ocr` hoặc `garble_score` > 0 (PDF lỗi mã hóa) → các khác biệt từ file đó cần xem lại bằng mắt.
- Nhiều phát hiện cùng kiểu trên cùng một cặp file → thường do một lỗi nhận diện, gộp lại.
- Tài liệu không cùng một hợp đồng (người dùng gom nhầm) → báo người dùng thay vì liệt kê hàng loạt "lỗi".
