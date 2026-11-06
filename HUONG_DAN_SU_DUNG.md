# HƯỚNG DẪN SỬ DỤNG – AI OFFICE ASSISTANT

Dành cho người không chuyên về AI. Toàn bộ công việc làm **trong VS Code, qua khung chat Claude Code** – không cần gõ lệnh trong terminal.
Cài đặt một lần theo mục 2–4; mục 5–9 là phần dùng hằng ngày.

---

## 1. Giới thiệu công cụ

AI Office Assistant là một **thư mục làm việc** có sẵn "bộ não" cho Claude. Bạn mở thư mục này trong VS Code, nói yêu cầu bằng tiếng Việt thường ngày trong khung chat, Claude tự chọn kỹ năng (Skill) phù hợp, tự chạy các script Python hỗ trợ, và **lưu kết quả thành file** (Word, Markdown, Excel) trong `workspace/output/`.

| Bạn muốn | Skill được dùng |
|---|---|
| Soạn công văn, tờ trình, biên bản, quyết định… | `hanh-chinh` |
| Kiểm tra căn cứ pháp lý, hiệu lực văn bản | `phap-ly-viet-nam` |
| Kiểm tra nhiều văn bản có thống nhất không, sửa cho đồng nhất | `document-audit` |
| Viết báo cáo/đề xuất giải pháp CNTT | `it-report` |
| Đọc, chuẩn hóa font/lề, tạo Word, xuất PDF | `word-expert` |

Công cụ **không** sửa file gốc của bạn, **không** tự xóa dữ liệu, **không** gửi tài liệu ra ngoài khi chưa được bạn đồng ý.

## 2. Chuẩn bị (một lần)

- Windows 10/11, macOS hoặc Linux.
- **VS Code**: tải tại https://code.visualstudio.com
- **Python 3.10 trở lên**: tải tại https://www.python.org/downloads/ – khi cài trên Windows nhớ **tích chọn "Add python.exe to PATH"**.
- Tài khoản Claude (gói Pro/Max/Team/Enterprise) hoặc API key Anthropic.
- (Tùy chọn) LibreOffice – để xuất PDF từ Word.
- (Tùy chọn) API key Xiaomi MiMo – xem mục 11.

## 3. Cài extension Claude Code và mở dự án

1. Mở VS Code → biểu tượng **Extensions** (thanh bên trái) → tìm **"Claude Code"** (nhà phát hành Anthropic) → **Install**.
2. Bấm biểu tượng Claude ở thanh bên/góc trên để mở **khung chat Claude Code**, đăng nhập theo hướng dẫn (trình duyệt sẽ mở ra).
3. **File → Open Folder** → chọn thư mục `AI-Office-Assistant`.
   ⚠️ Phải mở **đúng thư mục gốc dự án** (nơi có file `CLAUDE.md`), Claude mới nạp được quy tắc và 5 Skill.

Kiểm tra: hỏi trong khung chat *"Liệt kê các skill của dự án này."* → phải thấy `hanh-chinh`, `phap-ly-viet-nam`, `document-audit`, `it-report`, `word-expert`.

## 4. Cài môi trường Python cho dự án (một lần – nhờ Claude làm)

Dự án dùng **môi trường Python riêng** (thư mục `.venv`) để không đụng thư viện của phần mềm khác trên máy (tránh lỗi `pip's dependency resolver ... incompatible`).

Bạn chỉ cần gõ vào khung chat:

```text
Cài môi trường Python (.venv) cho dự án, cài thư viện trong requirements.txt, bật UTF-8 và chạy test kiểm tra giúp tôi.
```

Claude sẽ tạo `.venv`, cài thư viện, chạy kiểm tra và báo kết quả. Kết quả bình thường: `34 passed, 2 skipped` (2 test bỏ qua vì máy chưa có `pypdf` và LibreOffice – không ảnh hưởng sử dụng).

Claude sẽ hỏi xin phép trước khi chạy lệnh – đọc nội dung rồi bấm đồng ý. Từ đó về sau Claude **tự dùng `.venv`** mỗi khi chạy script (quy tắc đã ghi trong `CLAUDE.md`), bạn không phải làm gì thêm.

> Nếu muốn tự cài bằng tay: xem **Phụ lục A**.

## 5. Làm việc hằng ngày

1. Mở VS Code → thư mục `AI-Office-Assistant` (VS Code thường tự mở lại thư mục lần trước).
2. Mở khung chat Claude Code.
3. Đưa tài liệu vào (mục 6) và gõ yêu cầu như nói chuyện.
4. Nhận kết quả trong `workspace/output/` (mục 7).

**Có cần gọi tên Skill không?** Hầu như **không**. Claude tự chọn theo nội dung yêu cầu, có thể dùng nhiều Skill cho một việc, và luôn báo ngắn gọn "đây là việc gì, dùng Skill nào" ở đầu. Chỉ khi muốn chắc chắn mới nói rõ: *"Dùng skill document-audit để…"*.

**Tiện ích của khung chat VS Code:**

- **Bôi đen** một đoạn trong file đang mở rồi hỏi → Claude biết bạn đang nói về đoạn nào.
- Tên file trong câu trả lời **bấm vào là mở**; thay đổi hiển thị ngay trong trình soạn thảo.
- Claude **hỏi xin phép** trước khi chạy lệnh hoặc sửa file – đọc rồi mới bấm đồng ý.

**Tiếp tục việc đang làm dở:** mở lại cuộc trò chuyện cũ trong danh sách lịch sử của khung Claude Code, hoặc mở cuộc trò chuyện mới và nói: *"Tiếp tục việc dở: xem file mới nhất trong workspace/output rồi hoàn thiện nốt."*

**Đổi model:** gõ `/model` trong khung chat.

## 6. Đưa tài liệu cho Claude

Cách đơn giản và chắc chắn nhất: **thả file vào thư mục `workspace/input`**.

- **Kéo thả** file từ File Explorer của Windows vào thư mục `workspace` → `input` trong cây thư mục bên trái của VS Code; hoặc
- Nhờ Claude: *"Mở thư mục input cho tôi"* → Claude mở thư mục `workspace\input` trong File Explorer, bạn chép (Ctrl+C / Ctrl+V) file vào.

Sau đó nói: *"Tôi đã thêm file vào input, hãy …"*.

Các cách khác:

- Gõ **`@`** trong khung chat rồi chọn file của dự án (ví dụ `@workspace/input/hop-dong.docx`) để chỉ đúng file cần xử lý.
- Nói trực tiếp đường dẫn: *"Kiểm tra file D:\HopDong\a.docx và b.docx"* – Claude sẽ **sao chép** vào `workspace/input/` rồi xử lý trên bản sao; bản gốc giữ nguyên.

> Claude cần file nằm trên ổ đĩa để chạy script (so sánh, chuẩn hóa, xuất báo cáo) – vì vậy nên dùng `workspace/input/` thay vì dán nội dung vào khung chat.

Lưu ý:

- **PDF dạng scan (ảnh)** không đọc được chữ: cần OCR trước (ví dụ `ocrmypdf`); công cụ sẽ cảnh báo thay vì đoán nội dung.
- File `.doc` (Word cũ): mở bằng Word và **Lưu thành `.docx`** trước khi đưa vào.
- Chữ trong hình ảnh (con dấu, chữ ký, ảnh chụp màn hình) không được đọc.

## 7. Nhận kết quả trong `workspace/output`

Mở thư mục `workspace` → `output` ở cây thư mục bên trái VS Code, hoặc bấm vào tên file Claude đưa ra trong câu trả lời.

- Tên file dạng `YYYYMMDD_<việc>_<tên-gốc>.<đuôi>`; không ghi đè file cũ (trùng thì thêm `_v2`, `_v3`).
- File `.md` mở xem ngay trong VS Code (bấm chuột phải → **Open Preview** để xem dạng trình bày đẹp).
- File `.docx`/`.xlsx`: chuột phải → **Reveal in File Explorer** rồi mở bằng Word/Excel.

Claude **tự kiểm tra** file kết quả trước khi báo (file mở được, đủ nội dung, còn chỗ `[CẦN BỔ SUNG]` nào không). Bạn vẫn nên mở file Word xem lại bằng mắt trước khi gửi đi.

## 8. Quy trình mẫu: kiểm tra và sửa đồng nhất nhiều tài liệu

1. Thả các file (ví dụ hợp đồng, quy chế, tờ khai, đề án) vào `workspace/input/`.
2. Gõ: *"Kiểm tra 4 file trong input, gửi tôi file md các nội dung không đồng nhất và chỉnh sửa đồng nhất 4 file này."*
3. Claude sẽ:
   - so sánh tự động (tên, mã số thuế, địa chỉ, email, ngày, số tiền, %, thời hạn…) rồi đọc lại nội dung để loại cảnh báo sai;
   - tạo **báo cáo** `.md` (kèm `.docx`, `.xlsx`): từng điểm lệch có vị trí, trích dẫn, mức độ, đề xuất;
   - tạo **bản đã sửa** của từng file (`YYYYMMDD_dong-nhat_<tên-gốc>.docx`), giữ nguyên định dạng, bảng, hình ảnh;
   - **chỉ tự sửa những chỗ có căn cứ rõ** từ chính các tài liệu (lỗi gõ, tên/địa chỉ/email viết khác nhau…). Những chỗ cần quyết định nghiệp vụ hoặc pháp lý (mức phí, căn cứ pháp luật, thời hạn…) được liệt kê ở mục **"Việc cần bạn quyết định"** cuối báo cáo.
4. Bạn trả lời các điểm cần quyết định trong khung chat → Claude sửa tiếp vào bản đồng nhất.

## 9. Ví dụ yêu cầu thực tế

```text
Soạn công văn của Công ty ABC gửi Sở Y tế đề nghị gia hạn thời gian nộp báo cáo đến 30/12, xuất file Word.

Kiểm tra giúp tôi các văn bản trong workspace/input có thống nhất về tên công ty, số hợp đồng, ngày tháng và số tiền không.

Kiểm tra các căn cứ pháp lý trong file tờ trình này còn hiệu lực không, nêu số hiệu và nguồn.

Viết báo cáo đề xuất lãnh đạo: so sánh barcode, QRCode và RFID cho kho vải và kho sợi; có bảng so sánh và phương án đề xuất; xuất Word.

Chuẩn hóa file bao-cao.docx sang Times New Roman 13, lề chuẩn hành chính, đánh số trang; lưu bản mới.

Đọc file PDF bao-gia.pdf và tóm tắt các khoản chi phí.

Xuất file Word này sang PDF.
```

Mẹo: nêu rõ **mục đích, người đọc, định dạng mong muốn**; việc nào cần số liệu thì đưa số liệu thật.

## 10. Cách dùng từng Skill

**`hanh-chinh`** – Cho Claude đủ dữ kiện (cơ quan, nội dung, người nhận…). Thông tin thiếu sẽ được ghi `[CẦN BỔ SUNG: …]`; Claude **không tự bịa** số hiệu, ngày ban hành, tên người ký.

**`phap-ly-viet-nam`** – Claude tra cứu nguồn chính thống (Cơ sở dữ liệu quốc gia về pháp luật, Cổng thông tin Chính phủ, website bộ ngành), nêu số hiệu, ngày ban hành, tình trạng hiệu lực và dẫn nguồn. Không tìm được nguồn tin cậy thì báo rõ. Kết quả là **tài liệu hỗ trợ tham khảo, không thay thế tư vấn của luật sư**.

**`document-audit`** – Cần ≥ 2 file DOCX/PDF. Kết quả: báo cáo `.md`, `.docx`, bảng `.xlsx`; mỗi lỗi có mã, tài liệu, vị trí, nội dung gốc, nội dung đối chiếu, loại, mức độ (Critical/High/Medium/Low), phân tích, đề xuất. Phân 4 nhóm: *Lỗi chắc chắn / Khác biệt cần xác minh / Cảnh báo logic / Đề xuất cải thiện*. Có thể yêu cầu thêm bản đã sửa đồng nhất (mục 8).

**`it-report`** – Nêu bối cảnh, mục tiêu, các phương án cần so sánh, số liệu bạn có. Báo cáo gồm: mục tiêu & phạm vi, hiện trạng, phân tích, phương án, so sánh ưu/nhược, chi phí & rủi ro, đề xuất, kết luận. Dữ liệu thật và giả định được tách riêng.

**`word-expert`** – Đọc/tạo/chuẩn hóa Word, đọc PDF, xuất PDF. Không phá bố cục, không xóa nội dung, luôn tạo file mới.

## 11. MiMo (tùy chọn)

**Bạn không cần MiMo để dùng công cụ.** Chỉ dùng nếu muốn MiMo làm việc phụ (phân loại, trích xuất, tóm tắt sơ bộ) khi có rất nhiều tài liệu.

1. Nhờ Claude: *"Tạo file .env từ .env.example cho tôi."* Sau đó **tự mở `.env`** trong VS Code và điền `MIMO_API_KEY=khóa-của-bạn` (không dán key vào khung chat). File `.env` đã được loại khỏi Git.
2. Bật/tắt: mở `config/models.yaml`, mục `secondary` → `enabled: true` (bật) hoặc `false` (tắt, mặc định).
3. Kiểm tra: hỏi *"Kiểm tra trạng thái MiMo."* – Claude báo đang bật/tắt, đã có key chưa (không hiển thị key).
4. Đối chiếu `base_url` và `model` trong `config/models.yaml` với tài liệu chính thức của MiMo (https://mimo.mi.com) vì có thể thay đổi.

**Khi nào MiMo được dùng?** Chỉ khi: (1) bạn đã bật, (2) tác vụ nằm trong danh sách `routing.use_secondary_for`, và (3) bạn đồng ý cho gửi nội dung tài liệu ra dịch vụ ngoài trong lần đó (Claude sẽ hỏi). Lỗi, hết thời gian chờ hoặc thiếu key → Claude tự làm việc đó.

## 12. Thêm biểu mẫu và tài liệu tham khảo

Đặt file vào `references/administrative/` (biểu mẫu), `references/legal/` (văn bản pháp luật), `references/it-reports/` (mẫu báo cáo, tiêu chuẩn nội bộ) – kéo thả trong cây thư mục VS Code. Định dạng `.md` hoặc `.txt` là tốt nhất. Khi yêu cầu, nói: *"Dùng mẫu trong references/administrative/mau-cong-van.md."*

⚠️ Văn bản pháp luật trong `references/` **không** mặc định còn hiệu lực; Claude phải tra cứu lại trước khi dùng làm căn cứ.

## 13. Thêm Skill mới

Cách dễ nhất: mô tả cho Claude, ví dụ *"Tạo skill mới tên 'hop-dong-mua-ban' chuyên soạn và rà soát hợp đồng mua bán hàng hóa, cập nhật CLAUDE.md và chạy test."*

Nếu tự làm:

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
4. Nhờ Claude: *"Đồng bộ skill sang Antigravity và chạy test."*
5. Mở **cuộc trò chuyện mới** trong khung Claude Code để Claude nạp Skill.

## 14. Dùng với Antigravity (tùy chọn)

Antigravity đọc Skills từ thư mục `.agents/skills/`. Nhờ Claude: *"Đồng bộ skill sang .agents/skills."* (Claude chạy `scripts/sync_skills.py`). Sau đó mở Antigravity → **Open Folder** → chọn `AI-Office-Assistant`. Mỗi lần sửa Skill trong `.claude/skills/`, nhờ đồng bộ lại.

> Cách Antigravity nạp `CLAUDE.md` có thể khác Claude Code. Nếu nó không tuân quy tắc, nhắc: *"Đọc CLAUDE.md trong thư mục gốc và làm theo."*

## 15. Xử lý lỗi thường gặp

Phần lớn lỗi bạn chỉ cần **chép thông báo lỗi vào khung chat** – Claude sẽ đọc, tìm nguyên nhân và sửa.

| Hiện tượng | Cách xử lý |
|---|---|
| Claude không thấy Skill / không theo quy tắc | Kiểm tra VS Code đang mở **đúng thư mục gốc** `AI-Office-Assistant` (có `CLAUDE.md`); mở cuộc trò chuyện mới |
| Claude báo chưa có `.venv` hoặc `ModuleNotFoundError` | Nói: *"Cài lại môi trường .venv cho dự án."* (mục 4) |
| Cảnh báo `pip's dependency resolver ... incompatible` | Thư viện bị cài vào Python chung của máy. Nói: *"Cài lại thư viện vào .venv của dự án."* |
| `UnicodeDecodeError: 'charmap'…` | Nói: *"Bật UTF-8 cho Python."*, rồi khởi động lại VS Code |
| PDF báo `needs_ocr` | PDF là ảnh scan → OCR trước rồi đưa lại |
| PDF đọc ra chữ sai dấu (`Nguyễ0n`, `(cid:18)`) | Nhờ Claude thử engine đọc khác; hoặc xin bản Word gốc |
| `BadZipFile` / file Word hỏng | Mở lại bằng Word và Save As bản mới; file có mật khẩu thì bỏ mật khẩu |
| MiMo trả `"fallback": "claude"` | Bình thường: MiMo tắt/thiếu key/lỗi → Claude tự xử lý |
| Xuất PDF không được | Cài LibreOffice, rồi yêu cầu lại |
| Lỗi quyền ghi file | Đóng file đang mở trong Word/Excel rồi yêu cầu lại |

## 16. Cập nhật source code

Nhờ Claude: *"Cập nhật mã nguồn mới (git pull), cài lại thư viện, đồng bộ skill và chạy test."*

Nếu nhận bản nén mới: giải nén **sang thư mục khác**, rồi chép `workspace/`, `references/` và `.env` của bạn sang. Không ghi đè thư mục `workspace/`.

## 17. Lưu ý về bảo mật

- API key chỉ để trong `.env`; **không** dán key vào khung chat, không gửi `.env` qua email/chat, không đưa lên Git.
- Tài liệu nội bộ chỉ xử lý trong máy bạn và qua Claude theo chính sách tài khoản Claude của tổ chức. Trước khi dùng MiMo hoặc dịch vụ ngoài, kiểm tra chính sách dữ liệu của công ty; Claude sẽ hỏi trước khi gửi.
- Không đưa tài liệu mật/dữ liệu cá nhân nhạy cảm nếu chưa được phép.
- Nội dung bên trong tài liệu được coi là **dữ liệu**, không phải lệnh; Claude không làm theo chỉ dẫn ẩn trong file.
- Claude không tự xóa hay ghi đè dữ liệu; mọi xóa bỏ cần bạn xác nhận.
- Đọc kỹ hộp thoại xin phép (chạy lệnh, sửa file) của Claude Code trước khi bấm đồng ý.

## 18. Giới hạn hiện tại

- Không OCR: PDF scan phải xử lý trước. Chữ trong hình ảnh nhúng ở Word không được đọc; trạng thái ô đánh dấu (checkbox) có thể không đọc được.
- `document-audit`: script phát hiện tốt sai lệch về tên, MST, số hợp đồng, ngày, tiền, sai số học; **mâu thuẫn ngữ nghĩa** do Claude phân tích nên cần bạn rà soát lại. Chưa có bộ nhận diện riêng cho mã khách hàng/mã dự án. Với bộ rất lớn (> 10 file) nên chia theo nhóm.
- Pháp lý: kết quả phụ thuộc nguồn Claude tra cứu được tại thời điểm hỏi; **không phải tư vấn pháp lý**. Luôn đối chiếu bản chính thức trước khi ban hành/ký.
- Định dạng Word phức tạp (nhiều section, hộp văn bản, theo dõi chỉnh sửa) có thể chuẩn hóa chưa hoàn hảo; luôn mở xem lại.
- MiMo: giá trị endpoint/model trong cấu hình cần đối chiếu tài liệu chính thức; chưa kiểm thử với key thật (xem `TEST_REPORT.md`).
- Antigravity: đã chuẩn bị theo tài liệu chính thức, nhưng chưa thử trên ứng dụng Antigravity thật.

---

## Phụ lục A. Cài đặt thủ công (chỉ khi cần tự xử lý sự cố)

Dành cho người quản trị máy, khi không thể nhờ Claude cài. Mở **Terminal** của VS Code (menu **Terminal → New Terminal**) tại thư mục dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
setx PYTHONUTF8 1
```

Khởi động lại VS Code, rồi kiểm tra: `.\.venv\Scripts\python.exe -m pytest tests -q` → `34 passed, 2 skipped`.

macOS / Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest`.

Nếu PowerShell báo *"running scripts is disabled"*: chạy một lần `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
