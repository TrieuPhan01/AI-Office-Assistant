# TEST REPORT – AI Office Assistant

Ngày kiểm thử: 06/11/2026 · Môi trường: Linux, Python 3.13, Claude Code CLI 2.1.318, LibreOffice, pdfplumber + pdftotext (PyMuPDF **chưa cài** trong môi trường này).

Có hai lớp kiểm thử:
- **Tự động** (`python -m pytest tests -q`): 36 test, kết quả **36 passed**, chạy ~10 giây. Không cần mạng hay API key.
- **Thực tế bằng Claude Code CLI** (`claude -p ...`, có đăng nhập thật): các Test 1, 2, 4 và kiểm tra nhận diện Skills.

## 1. Tổng hợp theo yêu cầu (Phần 10)

| Test | Nội dung | Cách kiểm | Kết quả |
|---|---|---|---|
| 1 | Hành chính: soạn công văn → DOCX | Chạy thật bằng Claude Code | **Đạt**. Tạo `.docx` + `.md` đúng thể thức (quốc hiệu, kính gửi, nơi nhận). Thông tin chưa có (số văn bản, ngày, lý do, người ký) được đánh dấu `[CẦN BỔ SUNG]` (11 chỗ), không bịa. Validator báo WARN đúng thiết kế vì còn chỗ cần bổ sung. Log không thấy lệnh gọi Skill `hanh-chinh` tường minh; hành vi tuân theo `CLAUDE.md`. |
| 2 | Pháp lý: kiểm tra căn cứ | Chạy thật bằng Claude Code (có WebSearch) | **Đạt, có giới hạn**. Dùng đúng Skill `phap-ly-viet-nam`. File thử có 3 căn cứ: Luật 20/2023/QH15 (còn hiệu lực), NĐ 130/2018/NĐ-CP (phát hiện đã bị thay thế bởi NĐ 23/2025/NĐ-CP), NĐ "99/2099/NĐ-CP" cài giả (báo không tồn tại, không đoán thay thế). Báo cáo có nguồn URL, phân tách dữ liệu/nhận định/đề xuất. **Giới hạn:** nguồn chủ yếu thứ cấp (caselaw.vn, thuvienphapluat.vn…); mở trang đọc nguyên văn bị lỗi kết nối proxy nên chưa đối chiếu vbpl.vn. Tôi chưa tự xác minh độc lập từng số hiệu và ngày tháng mà Claude nêu; cần người dùng đối chiếu bản chính thức. |
| 3 | Document Audit: 3 DOCX có lỗi cài sẵn | Tự động + chạy thật pipeline | **Đạt**. `compare_documents.py` phát hiện 15 điểm (8 chắc chắn, 5 cần xác minh, 1 logic, 1 đề xuất; 4 Critical, 8 High, 2 Medium, 1 Low), có vị trí đoạn/bảng và trích dẫn. Xuất được DOCX + MD + XLSX; validator `--type audit` PASS (đủ 9 trường mỗi phát hiện). File gốc không bị thay đổi (có test riêng). Test không báo sai trên bộ tài liệu đúng. |
| 4 | IT Report → DOCX | Chạy thật bằng Claude Code | **Đạt**. Dùng Skill `it-report` + `word-expert`. Báo cáo 12 mục (tóm tắt, mục tiêu/phạm vi, hiện trạng, phân tích, phương án, so sánh, chi phí/rủi ro, đề xuất, kết luận, phụ lục), 7 bảng. Do không có số liệu chi phí, báo cáo **không bịa số**, gắn nhãn `[Giả định]` và `[CẦN BỔ SUNG]`. Xuất PDF qua LibreOffice thành công. |
| 5 | MiMo | Mock (không có API key thật) | **Đạt với mock; chưa kiểm với API thật** (xem mục 4). |

Kiểm tra Skills: `claude -p "Liệt kê tên các skill dự án"` trả về đủ 5 Skills (`document-audit, hanh-chinh, it-report, phap-ly-viet-nam, word-expert`), tức Claude Code nhận diện cấu hình trong `.claude/skills/` và đọc được `CLAUDE.md`.

## 2. Chi tiết 36 test tự động

| Nhóm | Số test | Nội dung chính |
|---|---|---|
| Hành chính | 2 | Chuẩn font/lề; Markdown → DOCX → validator |
| Document Audit | 9 | Cấu trúc trích xuất; phát hiện đủ các lỗi cài sẵn; có bằng chứng + vị trí; không báo sai trên tài liệu đúng; loại bỏ phát hiện đã bác (`dismissed`); từ chối phát hiện thiếu trường; bóc tách số/số bằng chữ; xuất báo cáo; file gốc nguyên vẹn |
| Word Expert | 5 | Vòng PDF (tạo → đọc); PDF trống cảnh báo OCR; DOCX hỏng báo lỗi sạch; chuẩn hóa giữ nguyên nội dung; từ chối ghi đè file gốc |
| IT Report | 1 | Markdown báo cáo → DOCX |
| MiMo | 13 | Mặc định tắt; thiếu key; thành công (key được gửi nhưng không lộ ra output); retry khi 503 rồi thành công; lỗi 500 kéo dài; timeout; 401 không retry; phản hồi rác; cần đồng ý mới gửi tài liệu; cắt bớt đầu vào; tác vụ ngoài `routing` bị từ chối; hệ thống vẫn chạy khi MiMo tắt (CLI); không có secret hardcode trong mã nguồn |
| Cấu trúc dự án | 6 | `models.yaml` mặc định; script được tham chiếu tồn tại; file tham chiếu của Skill tồn tại; frontmatter Skill hợp lệ; đồng bộ `.agents/skills` |

Biên dịch toàn bộ `scripts/*.py` và `tests/*.py`: không lỗi.

## 3. Lỗi và vấn đề phát hiện trong lần kiểm thử này

- Không phát hiện lỗi mã nguồn cần sửa trong lượt chạy này; toàn bộ test đạt ngay lần đầu.
- Lưu ý khi chạy kiểm thử thực tế: lần đầu tôi truyền sai đường dẫn file cho `mimo_client.py` và nhận lỗi `PackageNotFoundError` rõ ràng, đã chạy lại đúng đường dẫn (không phải lỗi hệ thống).
- Lịch sử sửa lỗi của các phiên xây dựng trước không được ghi lại đầy đủ nên không liệt kê ở đây.

## 4. Chưa hoàn thiện / chưa kiểm thử thực tế

| Mục | Tình trạng |
|---|---|
| **MiMo với API thật** | **Chưa kiểm.** Không có API key. Chỉ kiểm bằng mock HTTP: logic retry, timeout, lỗi, fallback sang Claude, cơ chế xin phép. Endpoint `https://api.xiaomimimo.com/v1` và model `mimo-v2.6-pro` trong `config/models.yaml` ghi theo tài liệu tại thời điểm xây dựng, **chưa được xác nhận bằng một lần gọi thật**; cần đối chiếu https://mimo.mi.com và chạy `python scripts/mimo_client.py ping` khi có key. |
| **Antigravity** | **Chưa thử trên ứng dụng thật.** Chỉ chuẩn bị `.agents/skills/` theo tài liệu của Google (đã kiểm đồng bộ bằng script). |
| **PyMuPDF** | Môi trường test không cài PyMuPDF; nhánh PyMuPDF của `extract_pdf.py` chưa được chạy ở đây (các engine `pdftotext`/`pdfplumber` đã chạy). |
| **PDF scan / OCR** | Không có OCR; công cụ chỉ phát hiện và cảnh báo. |
| **Mâu thuẫn ngữ nghĩa trong Document Audit** | Do Claude phân tích, chưa có bộ test định lượng độ chính xác. Chưa kiểm tra thực tế trên hợp đồng PDF dài/nhiều file (> 10). |
| **Mã khách hàng / mã dự án** | Chưa có bộ nhận diện tự động; Claude phải tìm thủ công. |
| **Độ chính xác pháp lý** | Phụ thuộc nguồn tra cứu của Claude tại thời điểm hỏi; cần người có chuyên môn đối chiếu bản chính thức trước khi dùng làm căn cứ. |
| **Test 1 và 4** | Mới chạy một lần mỗi test, chưa đo độ ổn định giữa các lần chạy; nội dung văn bản do Claude sinh nên có thể khác nhau mỗi lần. |

## 5. Cách chạy lại

```bash
pip install -r requirements.txt pytest
python -m pytest tests -q                      # 36 test tự động
python tests/make_fixtures.py workspace/input  # tạo 3 DOCX mẫu có lỗi cài sẵn
claude -p "Kiểm tra các file trong workspace/input có thống nhất không" --allowedTools "Bash,Read,Write,Edit,Skill"
```
