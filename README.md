# AI Office Assistant

Trợ lý AI cá nhân cho công việc văn phòng: **văn bản hành chính, rà soát pháp lý Việt Nam, kiểm tra đồng nhất nhiều tài liệu, báo cáo CNTT, xử lý Word/PDF**.

Đây là một workspace nhỏ chạy trực tiếp trong **Claude Code CLI** (hoặc **Antigravity**). Không có web app, không server, không database.

> Hướng dẫn chi tiết cho người dùng: [`HUONG_DAN_SU_DUNG.md`](HUONG_DAN_SU_DUNG.md) · Kết quả kiểm thử: [`TEST_REPORT.md`](TEST_REPORT.md)

## Kiến trúc

```
Người dùng (ngôn ngữ tự nhiên)
        │
   Claude Code ── đọc CLAUDE.md (quy tắc) ── tự chọn Skill phù hợp
        │
   .claude/skills/  (5 Skills)        scripts/ (Python: đọc, so sánh, xuất file)
        │                                   │
   references/ (biểu mẫu, tài liệu)   workspace/input → workspace/output
        │
   MiMo API (tùy chọn, mặc định tắt; lỗi thì Claude tự làm)
```

- **Claude** là AI chính: hiểu yêu cầu, chọn Skill, phân tích, viết kết luận.
- **Python** làm phần xác định được bằng máy: trích xuất, so sánh chuỗi/số/ngày, kiểm tra số học, dựng DOCX/Excel.
- **MiMo** chỉ là phụ trợ (phân loại, trích xuất, tóm tắt sơ bộ), tắt mặc định, không gửi tài liệu đi nếu chưa được đồng ý.

## 5 Skills

| Skill | Việc |
|---|---|
| `hanh-chinh` | Soạn/chuẩn hóa công văn, thông báo, quyết định, tờ trình, biên bản, báo cáo, kế hoạch |
| `phap-ly-viet-nam` | Tra cứu, kiểm tra căn cứ pháp lý và hiệu lực (luôn tra cứu nguồn chính thống, không bịa số hiệu) |
| `document-audit` | Đối chiếu ≥ 2 tài liệu: tên, MST, số hợp đồng, ngày, tiền, điều khoản, logic; báo cáo DOCX + MD + Excel |
| `it-report` | Báo cáo phân tích/đề xuất giải pháp CNTT (so sánh phương án, chi phí, rủi ro) |
| `word-expert` | Đọc/tạo/chuẩn hóa DOCX, đọc PDF, xuất PDF |

## Cấu trúc thư mục

```
AI-Office-Assistant/
├── CLAUDE.md                  Quy tắc làm việc cho Claude
├── .claude/skills/            5 Skills (nguồn chính, Claude Code)
├── .agents/skills/            Bản sao cho Antigravity (tạo bằng scripts/sync_skills.py)
├── config/models.yaml         Bật/tắt MiMo, endpoint, model, timeout
├── references/                Biểu mẫu, tài liệu pháp luật/kỹ thuật của bạn
├── scripts/
│   ├── extract_docx.py        Đọc DOCX (đoạn, bảng, vị trí)
│   ├── extract_pdf.py         Đọc PDF (nhiều engine, cảnh báo scan/lỗi dấu)
│   ├── compare_documents.py   So sánh nhiều tài liệu → phát hiện có cấu trúc
│   ├── build_audit_report.py  Phát hiện → báo cáo DOCX/MD/XLSX
│   ├── document_validator.py  Kiểm tra file đầu ra
│   ├── md_to_docx.py          Markdown → DOCX (chuẩn hành chính / báo cáo)
│   ├── docx_standardize.py    Chuẩn hóa font, cỡ chữ, lề trên bản sao
│   ├── mimo_client.py         Tích hợp MiMo (tùy chọn)
│   └── sync_skills.py         Đồng bộ Skills sang Antigravity
├── tests/                     36 test tự động (pytest)
└── workspace/input | output   Đầu vào / kết quả
```

## Công nghệ

Python 3.10+, `python-docx`, `openpyxl`, `PyYAML`, `requests`, `pdfplumber` (+ `PyMuPDF` khuyến nghị), LibreOffice (tùy chọn, để xuất PDF).

## Bắt đầu nhanh

```bash
pip install -r requirements.txt
claude            # mở trong thư mục dự án, rồi nói yêu cầu bằng tiếng Việt
```
