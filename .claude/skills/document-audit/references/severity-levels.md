# Mức độ nghiêm trọng và nhóm phát hiện

## Mức độ (severity)
| Mức | Khi nào | Ví dụ |
|---|---|---|
| **Critical** | Có thể làm sai giá trị/đối tượng pháp lý, gây tranh chấp hoặc làm văn bản vô hiệu/không thực hiện được | Số tiền bằng số ≠ bằng chữ; tổng giá trị hợp đồng khác nhau giữa hợp đồng và phụ lục; MST/số hợp đồng dẫn chiếu sai |
| **High** | Sai/khác ở nội dung quan trọng nhưng còn khả năng xác định đúng từ ngữ cảnh | Sai tên pháp nhân (1–2 ký tự); chức danh người ký khác nhau; ngày hiệu lực/kết thúc khác nhau; sai thành tiền, tổng bảng, thuế |
| **Medium** | Sai sót hình thức/chi tiết, ít ảnh hưởng pháp lý trực tiếp nhưng cần sửa | Thiếu dấu tiếng Việt; địa chỉ viết khác nhau; MST sai độ dài; hiệu lực trước ngày ký |
| **Low** | Thống nhất hình thức, thẩm mỹ | Hoa/thường tên công ty; cách viết ngày; dấu câu |

Nguyên tắc nâng/hạ mức:
- Nâng một mức khi giá trị liên quan đến **tiền, thuế, thời hạn, bên ký kết** hoặc lỗi lặp ở nhiều tài liệu.
- Hạ một mức khi tài liệu chỉ là bản nháp/nội bộ hoặc ngữ cảnh cho thấy hiển nhiên đúng.
- Critical chỉ dùng khi tự tin sai sót có hậu quả thực; không "đẩy" mức để gây chú ý.

## Nhóm phát hiện (category)
| Mã | Tên | Tiêu chí |
|---|---|---|
| `certain` | Lỗi chắc chắn | Có bằng chứng ngay trong tài liệu chứng minh sai/không nhất quán (tính toán, đối chiếu nội bộ, giá trị không tồn tại) |
| `verify` | Khác biệt cần xác minh | Hai giá trị khác nhau; chưa đủ cơ sở kết luận bên nào sai; cần giấy tờ gốc/ý kiến người có thẩm quyền |
| `logic` | Cảnh báo logic | Dấu hiệu bất hợp lý có thể có lý do chính đáng |
| `suggestion` | Đề xuất cải thiện | Không phải lỗi |

Quy tắc: nếu phải đoán thì xếp `verify`, không xếp `certain`.

## Cặp (nhóm, mức) thường gặp
- `certain` + Critical/High: sai số học, số/chữ không khớp, ngày không tồn tại.
- `verify` + High: số liệu/ngày/chức danh khác giữa hợp đồng và phụ lục.
- `logic` + Medium/High: thứ tự ngày bất hợp lý.
- `suggestion` + Low: thống nhất cách viết.
