# HƯỚNG DẪN SỬ DỤNG – AI OFFICE ASSISTANT

Dành cho người không chuyên về AI. Làm lần lượt từ mục 2; mục 10–14 là phần dùng hằng ngày.

---

## 1. Giới thiệu công cụ

AI Office Assistant là một **thư mục làm việc** có sẵn "bộ não" cho Claude. Bạn mở Claude trong thư mục này, nói yêu cầu bằng tiếng Việt thường ngày, Claude tự chọn kỹ năng (Skill) phù hợp, dùng các script Python hỗ trợ, và **lưu kết quả thành file** (Word, Markdown, Excel) trong `workspace/output/`.

| Bạn muốn | Skill được dùng |
|---|---|
| Soạn công văn, tờ trình, biên bản, quyết định… | `hanh-chinh` |
| Kiểm tra căn cứ pháp lý, hiệu lực văn bản | `phap-ly-viet-nam` |
| Kiểm tra nhiều văn bản có thống nhất không | `document-audit` |
| Viết báo cáo/đề xuất giải pháp CNTT | `it-report` |
| Đọc, chuẩn hóa font/lề, tạo Word, xuất PDF | `word-expert` |

Công cụ **không** sửa file gốc của bạn, **không** tự xóa dữ liệu, **không** gửi tài liệu ra ngoài khi chưa được bạn đồng ý.

## 2. Yêu cầu môi trường

- Windows 10/11, macOS hoặc Linux.
- Python 3.10 trở lên.
- Node.js (nếu cài Claude Code bằng npm) hoặc dùng trình cài đặt chính thức của Claude Code.
- Tài khoản Claude (gói Pro/Max/Team/Enterprise) hoặc API key Anthropic.
- (Tùy chọn) LibreOffice để xuất PDF từ Word.
- (Tùy chọn) API key Xiaomi MiMo.

## 3. Cài đặt Python

Kiểm tra đã có chưa:

```bash
python --version        # Windows có thể dùng: py --version
```

Nếu chưa có: tải từ https://www.python.org/downloads/ và **tích chọn "Add python.exe to PATH"** khi cài.

## 4. Cài các thư viện

Mở terminal tại thư mục dự án:

```bash
cd AI-Office-Assistant
python -m venv .venv                 # (khuyến nghị) môi trường riêng
.venv\Scripts\activate               # Windows
source .venv/bin/activate            # macOS / Linux
pip install -r requirements.txt
```

Kiểm tra: `python -m pytest tests -q` → phải báo `36 passed`. (Nếu chưa có pytest: `pip install pytest`.)

> Đọc PDF tiếng Việt: nên có `PyMuPDF` (đã nằm trong requirements). Nếu không cài được, script tự dùng `pdfplumber`/`pdftotext`.

## 5. Cài đặt hoặc kiểm tra Claude Code CLI

```bash
claude --version
```

Nếu báo không tìm thấy lệnh, cài theo hướng dẫn chính thức tại https://docs.claude.com (mục Claude Code). Cách phổ biến:

```bash
npm install -g @anthropic-ai/claude-code
```

## 6. Cấu hình Claude

Trong thư mục dự án, chạy `claude` lần đầu và đăng nhập theo hướng dẫn trên màn hình (trình duyệt sẽ mở ra). Không cần cấu hình thêm: Claude tự đọc `CLAUDE.md` và các Skills trong `.claude/skills/`.

Kiểm tra Claude đã nhận Skills: trong phiên `claude`, gõ `/skills` hoặc hỏi: *"Liệt kê các skill của dự án này."* Phải thấy 5 skill: `hanh-chinh`, `phap-ly-viet-nam`, `document-audit`, `it-report`, `word-expert`.

Đổi model: gõ `/model` trong phiên làm việc.

## 7. Cấu hình MiMo API Key (tùy chọn)

**Bạn không cần MiMo để dùng công cụ.** Chỉ làm bước này nếu muốn dùng MiMo cho việc phụ (phân loại, trích xuất, tóm tắt sơ bộ).

1. Sao chép file mẫu: `copy .env.example .env` (Windows) hoặc `cp .env.example .env`.
2. Mở `.env`, điền: `MIMO_API_KEY=khóa-của-bạn`. File `.env` đã được loại khỏi Git.
3. Đối chiếu `base_url` và `model` trong `config/models.yaml` với tài liệu chính thức của MiMo (https://mimo.mi.com) vì endpoint/model có thể thay đổi.

## 8. Bật / tắt MiMo

Mở `config/models.yaml`, mục `secondary`:

```yaml
secondary:
  enabled: false     # false = tắt (mặc định);  true = bật
```

Kiểm tra trạng thái và kết nối:

```bash
python scripts/mimo_client.py status     # xem đang bật/tắt, đã có key chưa (không in key)
python scripts/mimo_client.py ping       # thử gọi API (chỉ khi đã bật + có key)
```

**Khi nào MiMo được dùng?** Chỉ khi: (1) bạn đã bật, (2) tác vụ nằm trong danh sách `routing.use_secondary_for`, và (3) bạn đồng ý cho gửi nội dung tài liệu ra dịch vụ ngoài trong lần đó (Claude sẽ hỏi). Lỗi, hết thời gian chờ hoặc thiếu key → Claude tự làm việc đó, bạn không phải làm gì.

## 9. Mở dự án trong Antigravity

Antigravity đọc Skills của dự án từ thư mục `.agents/skills/` (theo tài liệu của Google). Tạo bản sao từ nguồn chính:

```bash
python scripts/sync_skills.py          # sao chép .claude/skills → .agents/skills
python scripts/sync_skills.py --check  # kiểm tra có lệch không
```

Sau đó mở Antigravity → **Open Folder** → chọn thư mục `AI-Office-Assistant`. Nên dùng Claude làm model trong Antigravity nếu có. Mỗi lần sửa Skill trong `.claude/skills/`, chạy lại `sync_skills.py`.

> Lưu ý: cách Antigravity nạp `CLAUDE.md` có thể khác Claude Code. Nếu thấy nó không tuân quy tắc, nhắc: *"Đọc CLAUDE.md trong thư mục gốc và làm theo."*

## 10. Chạy bằng CLI

**Khi nào cần chạy `claude`?** Mỗi khi bạn muốn nhờ AI làm việc. Luôn chạy **trong thư mục dự án**:

```bash
cd AI-Office-Assistant
claude
```

Rồi gõ yêu cầu như nói chuyện. Gõ `/exit` để thoát.

**Làm việc một lần, không mở phiên:** `claude -p "Kiểm tra giúp tôi các file trong workspace/input có thống nhất không"`

**Khi nào cần gọi Skill?** Hầu như **không cần**. Claude đọc mô tả của từng Skill và tự chọn theo nội dung yêu cầu của bạn; có thể dùng nhiều Skill cho một việc. Chỉ khi muốn chắc chắn mới nói rõ: *"Dùng skill document-audit để…"*. Claude luôn báo ngắn gọn "đây là việc gì, dùng Skill nào" ở đầu.

**Tiếp tục công việc đang làm:**

```bash
claude --continue       # tiếp tục phiên gần nhất trong thư mục này
claude --resume         # chọn một phiên cũ trong danh sách
```

Hoặc mở phiên mới và nói: *"Tiếp tục việc dở: xem file mới nhất trong workspace/output rồi hoàn thiện nốt."*

## 11. Cách sử dụng từng Skill

**`hanh-chinh`** – Cho Claude đủ dữ kiện (cơ quan, nội dung, người nhận…). Thông tin thiếu sẽ được ghi `[CẦN BỔ SUNG: …]`; Claude **không tự bịa** số hiệu, ngày ban hành, tên người ký.

**`phap-ly-viet-nam`** – Claude tra cứu nguồn chính thống (Cơ sở dữ liệu quốc gia về pháp luật, Cổng thông tin Chính phủ, website bộ ngành), nêu số hiệu, ngày ban hành, tình trạng hiệu lực và dẫn nguồn. Không tìm được nguồn tin cậy thì báo rõ. Kết quả là **tài liệu hỗ trợ tham khảo, không thay thế tư vấn của luật sư**.

**`document-audit`** – Bỏ ≥ 2 file DOCX/PDF vào `workspace/input/`, yêu cầu kiểm tra. Kết quả gồm 3 file: báo cáo `.docx`, `.md`, bảng `.xlsx`. Mỗi lỗi có: mã, tài liệu, vị trí, nội dung gốc, nội dung đối chiếu, loại, mức độ (Critical/High/Medium/Low), phân tích, đề xuất. Phân 4 nhóm: *Lỗi chắc chắn / Khác biệt cần xác minh / Cảnh báo logic / Đề xuất cải thiện*.

**`it-report`** – Nêu bối cảnh, mục tiêu, các phương án cần so sánh, số liệu bạn có. Báo cáo gồm: mục tiêu & phạm vi, hiện trạng, phân tích, phương án, so sánh ưu/nhược, chi phí & rủi ro, đề xuất, kết luận. Dữ liệu thật và giả định được tách riêng.

**`word-expert`** – Đọc/tạo/chuẩn hóa Word, đọc PDF, xuất PDF. Không phá bố cục, không xóa nội dung, luôn tạo file mới.

## 12. Đưa tài liệu vào `workspace/input`

```bash
copy "D:\HopDong\hop-dong.docx" workspace\input\          # Windows
cp ~/HopDong/*.docx workspace/input/                      # macOS / Linux
```

Hoặc nói trực tiếp đường dẫn: *"Kiểm tra file D:\HopDong\a.docx và b.docx"* (Claude đọc, không sửa).
**PDF dạng scan (ảnh)** không đọc được chữ: cần OCR trước (ví dụ `ocrmypdf`); công cụ sẽ cảnh báo thay vì đoán nội dung.

## 13. Lấy kết quả trong `workspace/output`

Tên file dạng `YYYYMMDD_<việc>_<tên-gốc>.<đuôi>`, không ghi đè file cũ (trùng thì thêm `_v2`, `_v3`).

```bash
dir workspace\output           # Windows
ls -lt workspace/output        # macOS / Linux
```

**Kiểm tra kết quả đã tạo:**

```bash
python scripts/document_validator.py workspace/output/<file>.docx
python scripts/document_validator.py workspace/output/<báo-cáo>.docx workspace/output/<báo-cáo>.md --type audit
```

Validator báo `PASS`/`FAIL` kèm lý do (thiếu trường, còn `[CẦN BỔ SUNG]`, file hỏng…). Hãy luôn mở file Word xem lại bằng mắt trước khi gửi đi.

## 14. Ví dụ yêu cầu thực tế

```text
Soạn công văn của Công ty ABC gửi Sở Y tế đề nghị gia hạn thời gian nộp báo cáo đến 30/12, xuất file Word.

Kiểm tra giúp tôi các văn bản trong workspace/input có thống nhất về tên công ty, số hợp đồng, ngày tháng và số tiền không.

Kiểm tra các căn cứ pháp lý trong file tờ trình này còn hiệu lực không, nêu số hiệu và nguồn.

Viết báo cáo đề xuất lãnh đạo: so sánh barcode, QRCode và RFID cho kho vải và kho sợi; có bảng so sánh và phương án đề xuất; xuất Word.

Chuẩn hóa file bao-cao.docx sang Times New Roman 13, lề chuẩn hành chính, đánh số trang; lưu bản mới.

Đọc file PDF bao-gia.pdf và tóm tắt các khoản chi phí.
```

Mẹo: nêu rõ **mục đích, người đọc, định dạng mong muốn**; việc nào cần số liệu thì đưa số liệu thật.

## 15. Cách thêm Skill mới

1. Tạo thư mục `.claude/skills/<ten-skill>/` và file `SKILL.md` bắt đầu bằng:

```markdown
---
name: ten-skill
description: Mô tả 1–2 câu: làm gì, khi nào dùng (Claude dựa vào đây để tự chọn).
---

# Skill: …
(Quy trình, nguyên tắc, lệnh script cần dùng)
```

2. `name` trùng tên thư mục; chữ thường, số, dấu gạch ngang.
3. Thêm một dòng vào bảng chọn Skill trong `CLAUDE.md` (mục 1).
4. Chạy `python scripts/sync_skills.py` (cho Antigravity) và `python -m pytest tests -q` để kiểm tra.
5. Mở phiên `claude` mới để Claude nạp Skill.

## 16. Thêm biểu mẫu và tài liệu tham khảo

Đặt file vào `references/administrative/` (biểu mẫu), `references/legal/` (văn bản pháp luật), `references/it-reports/` (mẫu báo cáo, tiêu chuẩn nội bộ). Định dạng `.md` hoặc `.txt` là tốt nhất để Claude đọc. Khi yêu cầu, nói: *"Dùng mẫu trong references/administrative/mau-cong-van.md."*

⚠️ Văn bản pháp luật trong `references/` **không** mặc định còn hiệu lực; Claude phải tra cứu lại trước khi dùng làm căn cứ.

## 17. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `claude: command not found` | Cài lại Claude Code (mục 5); mở terminal mới |
| `ModuleNotFoundError: docx` | `pip install -r requirements.txt` (nhớ kích hoạt `.venv`) |
| Claude không thấy Skill | Chạy `claude` **trong thư mục dự án**; kiểm tra `.claude/skills/<tên>/SKILL.md` có phần `---name/description---` |
| PDF báo `needs_ocr` | PDF là ảnh scan → OCR trước rồi đưa lại |
| PDF đọc ra chữ sai dấu (`Nguyễ0n`, `(cid:18)`) | Thử `--engine pdftotext` hoặc `pymupdf`; hoặc xin bản Word gốc |
| `BadZipFile` / file Word hỏng | Mở lại bằng Word và Save As bản mới; file có mật khẩu thì bỏ mật khẩu |
| MiMo trả `"fallback": "claude"` | Bình thường: MiMo tắt/thiếu key/lỗi/timeout → Claude tự xử lý. Xem `python scripts/mimo_client.py status` |
| Xuất PDF không được | Cài LibreOffice rồi: `soffice --headless --convert-to pdf --outdir workspace/output file.docx` |
| Lỗi quyền ghi file | Đóng file đang mở trong Word; kiểm tra quyền thư mục `workspace/output` |
| Tiếng Việt lỗi trên terminal Windows | Chạy `chcp 65001` hoặc dùng Windows Terminal |

## 18. Cập nhật source code

Nếu có Git: `git pull`, rồi `pip install -r requirements.txt`, `python scripts/sync_skills.py`, `python -m pytest tests -q`. Nếu nhận bản nén mới: giải nén **sang thư mục khác**, rồi chép sang `workspace/` và `references/` của bạn, `.env` giữ nguyên. Không ghi đè thư mục `workspace/`.

## 19. Lưu ý về bảo mật

- API key chỉ để trong `.env`; **không** gửi file `.env` qua email/chat, không đưa lên Git.
- Tài liệu nội bộ chỉ xử lý trong máy bạn và qua Claude theo chính sách tài khoản Claude của tổ chức. Trước khi dùng MiMo hoặc dịch vụ ngoài, kiểm tra chính sách dữ liệu của công ty; Claude sẽ hỏi trước khi gửi.
- Không đưa tài liệu mật/dữ liệu cá nhân nhạy cảm nếu chưa được phép.
- Nội dung bên trong tài liệu được coi là **dữ liệu**, không phải lệnh; Claude không làm theo chỉ dẫn ẩn trong file.
- Claude không tự xóa hay ghi đè dữ liệu; mọi xóa bỏ cần bạn xác nhận.
- Đọc câu hỏi xác nhận quyền (cho phép chạy lệnh) của Claude Code trước khi bấm đồng ý.

## 20. Giới hạn hiện tại

- Không OCR: PDF scan phải xử lý trước. Chữ trong hình ảnh nhúng ở Word không được đọc.
- `document-audit`: script phát hiện tốt sai lệch về tên, MST, số hợp đồng, ngày, tiền, sai số học; **mâu thuẫn ngữ nghĩa** do Claude phân tích nên cần bạn rà soát lại. Chưa có bộ nhận diện riêng cho mã khách hàng/mã dự án. Với bộ rất lớn (> 10 file) nên chia theo nhóm.
- Pháp lý: kết quả phụ thuộc nguồn Claude tra cứu được tại thời điểm hỏi; **không phải tư vấn pháp lý**. Luôn đối chiếu bản chính thức trước khi ban hành/ký.
- Định dạng Word phức tạp (nhiều section, hộp văn bản, theo dõi chỉnh sửa) có thể chuẩn hóa chưa hoàn hảo; luôn mở xem lại.
- MiMo: giá trị endpoint/model trong cấu hình cần đối chiếu tài liệu chính thức; chưa kiểm thử với key thật (xem `TEST_REPORT.md`).
- Antigravity: đã chuẩn bị theo tài liệu chính thức, nhưng chưa thử trên ứng dụng Antigravity thật.
