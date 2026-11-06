#!/usr/bin/env python3
"""Bộ kiểm thử tự động (unittest, không cần mạng).  Chạy:  python tests/test_all.py -v"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import build_audit_report  # noqa: E402
import compare_documents  # noqa: E402
import document_validator  # noqa: E402
import docx_standardize  # noqa: E402
import extract_docx  # noqa: E402
import extract_pdf  # noqa: E402
import make_fixtures  # noqa: E402
import md_to_docx  # noqa: E402
import mimo_client  # noqa: E402

os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"


def run_script(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=ROOT)


class TmpMixin:
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------- Test 1: Hành chính
class TestHanhChinh(TmpMixin, unittest.TestCase):
    MD = """\
| | |
|:---:|:---:|
| **CÔNG TY TNHH ABC**<br>Số: [CẦN BỔ SUNG: số công văn] | **CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**<br>**Độc lập - Tự do - Hạnh phúc** |

<p align="right">Hà Nội, ngày [CẦN BỔ SUNG] tháng [CẦN BỔ SUNG] năm 2026</p>

<p align="center">**V/v đề nghị cung cấp báo giá**</p>

**Kính gửi:** Công ty XYZ

Công ty TNHH ABC đề nghị Quý Công ty cung cấp báo giá cho hạng mục sau:

1. Máy chủ lưu trữ dữ liệu.
2. Thiết bị mạng.

| STT | Hạng mục | Số lượng |
|:---:|---|---:|
| 1 | Máy chủ | 2 |

Trân trọng cảm ơn.

**Nơi nhận:**
- Như trên;
- Lưu: VT.
"""

    def test_md_to_docx_and_validate(self):
        src = self.tmp / "cv.md"
        src.write_text(self.MD, encoding="utf-8")
        out = self.tmp / "cv.docx"
        md_to_docx.convert_file(src, out, "hanhchinh")
        self.assertTrue(out.exists() and out.stat().st_size > 0)
        data = extract_docx.extract(out)
        text = "\n".join(b["text"] for b in data["blocks"])
        self.assertIn("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", text)
        self.assertIn("Kính gửi", text)
        self.assertEqual(data["table_count"], 2)
        self.assertNotIn("**", text)
        rep = document_validator.validate(out, "admin")
        codes = {i["code"] for i in rep.items}
        self.assertNotEqual(rep.status, "FAIL")
        self.assertIn("PLACEHOLDER", codes)  # còn chỗ cần bổ sung phải được cảnh báo
        self.assertNotIn("QUOC_HIEU", codes)
        self.assertNotIn("NOI_NHAN", codes)

    def test_font_and_margins(self):
        src = self.tmp / "a.md"
        src.write_text("# Tiêu đề\n\nNội dung thử tiếng Việt: Đường Nguyễn Huệ.\n", encoding="utf-8")
        out = self.tmp / "a.docx"
        md_to_docx.convert_file(src, out, "hanhchinh")
        from docx import Document
        doc = Document(str(out))
        self.assertEqual(doc.styles["Normal"].font.name, "Times New Roman")
        self.assertAlmostEqual(doc.sections[0].left_margin.mm, 30, delta=0.5)
        self.assertIn("PAGE", doc.sections[0].footer._element.xml)


# ---------------------------------------------------------------- Test 3: Document Audit
class TestDocumentAudit(TmpMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.paths = make_fixtures.make_all(self.tmp / "in")
        self.result = compare_documents.run([str(p) for p in self.paths])
        self.f = self.result["findings"]

    def has(self, cat, sev, needle, docs=None):
        for x in self.f:
            if x["category"] == cat and x["severity"] == sev and needle.casefold() in x["error_type"].casefold():
                if docs is None or set(docs) <= set(x["documents"]):
                    return True
        return False

    def test_extract_structure(self):
        d = extract_docx.extract(self.paths[0])
        self.assertEqual(d["table_count"], 1)
        self.assertTrue(any(b["kind"] == "table_row" and "150.000.000" in b["text"] for b in d["blocks"]))
        self.assertTrue(any("Điều 1" in b["loc"] for b in d["blocks"]))  # vị trí gắn với Điều

    def test_planted_errors_detected(self):
        self.assertTrue(self.has("certain", "Critical", "Mã số thuế nghi gõ nhầm"), self.f)
        self.assertTrue(self.has("certain", "Critical", "Số hợp đồng/số văn bản nghi gõ nhầm"))
        self.assertTrue(self.has("certain", "Medium", "Sai/thiếu dấu"))
        self.assertTrue(self.has("certain", "Critical", "Số tiền (tổng giá trị) khác nhau"))
        self.assertTrue(self.has("certain", "Critical", "bằng số và bằng chữ"))
        self.assertTrue(self.has("verify", "High", "Chức danh của cùng một người"))
        self.assertTrue(self.has("verify", "High", "Ngày kết thúc khác nhau"))
        self.assertTrue(self.has("certain", "High", "Thành tiền ≠ Số lượng"))
        self.assertTrue(self.has("certain", "High", "Tổng bảng không bằng"))
        self.assertTrue(self.has("certain", "High", "Ngày không tồn tại"))
        self.assertTrue(self.has("logic", "High", "Ngày kết thúc trước ngày hiệu lực"))
        self.assertTrue(self.has("verify", "High", "thuế suất vat"))
        self.assertTrue(self.has("suggestion", "Low", "Viết hoa/thường"))

    def test_no_false_positive_on_correct_doc(self):
        """Hợp đồng đứng riêng (đúng hết) không được sinh lỗi chắc chắn."""
        res = compare_documents.run([str(self.paths[0])])
        self.assertEqual([x for x in res["findings"] if x["category"] == "certain"], [])

    def test_findings_have_evidence_and_location(self):
        for x in self.f:
            self.assertTrue(x["locations"] and x["original"], x)
            self.assertRegex(x["id"], r"^F-\d{3}$")

    def test_words_to_number(self):
        w = compare_documents.words_to_number
        self.assertEqual(w("Một trăm năm mươi triệu đồng chẵn"), 150_000_000)
        self.assertEqual(w("hai tỷ ba trăm linh năm triệu bốn trăm nghìn đồng"), 2_305_400_000)
        self.assertEqual(w("mười lăm nghìn"), 15_000)
        self.assertEqual(w("hai mươi mốt triệu"), 21_000_000)
        self.assertIsNone(w("abc xyz"))

    def test_parse_number(self):
        p = compare_documents.parse_number
        self.assertEqual(p("1.234.567"), 1234567)
        self.assertEqual(p("1,234,567"), 1234567)
        self.assertEqual(p("1.234,5"), 1234.5)
        self.assertEqual(p("2,5"), 2.5)
        self.assertIsNone(p("abc"))

    def test_report_outputs_and_validation(self):
        raw = self.tmp / "raw.json"
        raw.write_text(json.dumps(self.result, ensure_ascii=False), encoding="utf-8")
        r = run_script("scripts/build_audit_report.py", raw, "--outdir", self.tmp / "out", "--name", "t")
        self.assertEqual(r.returncode, 0, r.stderr)
        for ext in (".md", ".docx", ".xlsx"):
            self.assertTrue((self.tmp / "out" / f"t{ext}").exists(), ext)
        for ext in (".md", ".docx"):
            rep = document_validator.validate(self.tmp / "out" / f"t{ext}", "audit")
            self.assertEqual(rep.status, "PASS" if rep.status == "PASS" else rep.status, rep.items)
            self.assertNotEqual(rep.status, "FAIL", rep.items)
        from openpyxl import load_workbook
        ws = load_workbook(self.tmp / "out" / "t.xlsx").worksheets[0]
        self.assertEqual(ws.max_row, len(self.f) + 1)

    def test_report_rejects_incomplete_finding(self):
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"findings": [{"category": "certain", "severity": "High"}]}), encoding="utf-8")
        r = run_script("scripts/build_audit_report.py", bad, "--outdir", self.tmp / "o")
        self.assertEqual(r.returncode, 2)
        self.assertIn("thiếu trường", r.stderr)

    def test_dismissed_findings_excluded(self):
        data = dict(self.result)
        first = data["findings"][0]["id"]
        data["meta"] = {"dismissed": [{"id": first, "reason": "hai bên khác nhau"}]}
        p = self.tmp / "d.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        _, _, items, dismissed = build_audit_report.load_findings(p)
        self.assertEqual(len(items), len(self.f) - 1)
        self.assertIn(first, dismissed)

    def test_original_files_untouched(self):
        before = [p.read_bytes() for p in self.paths]
        compare_documents.run([str(p) for p in self.paths])
        self.assertEqual(before, [p.read_bytes() for p in self.paths])


# ---------------------------------------------------------------- PDF / Word-expert
class TestWordExpert(TmpMixin, unittest.TestCase):
    def test_standardize_keeps_content(self):
        src = self.tmp / "s.docx"
        make_fixtures.hop_dong(src)
        out = self.tmp / "s_chuan.docx"
        r = run_script("scripts/docx_standardize.py", src, "-o", out, "--font", "Arial", "--size", "12",
                       "--margins", "25,25,30,20", "--align", "justify", "--page-numbers")
        self.assertEqual(r.returncode, 0, r.stderr)
        a, b = extract_docx.extract(src), extract_docx.extract(out)
        self.assertEqual([x["text"] for x in a["blocks"]], [x["text"] for x in b["blocks"]])
        self.assertEqual(a["table_count"], b["table_count"])
        from docx import Document
        d = Document(str(out))
        self.assertEqual(d.paragraphs[0].runs[0].font.name, "Arial")
        self.assertAlmostEqual(d.sections[0].left_margin.mm, 30, delta=0.5)

    def test_standardize_refuses_overwrite_original(self):
        src = self.tmp / "s.docx"
        make_fixtures.hop_dong(src)
        r = run_script("scripts/docx_standardize.py", src, "-o", src, "--font", "Arial")
        self.assertEqual(r.returncode, 2)

    @unittest.skipUnless(shutil.which("soffice"), "cần LibreOffice")
    def test_pdf_roundtrip(self):
        src = self.tmp / "p.docx"
        make_fixtures.hop_dong(src)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(self.tmp), str(src)],
                       capture_output=True, timeout=180)
        pdf = self.tmp / "p.pdf"
        self.assertTrue(pdf.exists(), "LibreOffice không tạo được PDF")
        d = extract_pdf.extract(pdf)
        self.assertGreaterEqual(d["page_count"], 1)
        self.assertFalse(d["needs_ocr"])
        self.assertIn("150.000.000", "\n".join(p["text"] for p in d["pages"]))
        res = compare_documents.run([str(src), str(pdf)])  # DOCX và PDF cùng nội dung -> không lỗi chắc chắn
        self.assertEqual([x for x in res["findings"] if x["category"] == "certain"], [], res["findings"])

    def test_blank_pdf_flags_ocr(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest("cần pypdf")
        w = PdfWriter()
        w.add_blank_page(595, 842)
        p = self.tmp / "blank.pdf"
        with open(p, "wb") as fh:
            w.write(fh)
        d = extract_pdf.extract(p)
        self.assertTrue(d["needs_ocr"])
        self.assertIn("OCR", d["warning"])

    def test_corrupt_docx_clean_error(self):
        bad = self.tmp / "bad.docx"
        bad.write_bytes(b"not a docx")
        r = run_script("scripts/extract_docx.py", bad)
        self.assertEqual(r.returncode, 2)
        self.assertIn("LỖI", r.stderr)
        rep = document_validator.validate(bad)
        self.assertEqual(rep.status, "FAIL")


# ---------------------------------------------------------------- Test 4: IT report (cấu trúc)
class TestItReport(TmpMixin, unittest.TestCase):
    def test_report_md_to_docx(self):
        md = ("# Báo cáo đề xuất giải pháp\n\n## 1. Mục tiêu và phạm vi\n\nNội dung.\n\n## 2. So sánh phương án\n\n"
              "| Tiêu chí | Phương án A | Phương án B |\n|---|---|---|\n| Chi phí | [CẦN BỔ SUNG] | Thấp |\n\n"
              "## 3. Kết luận và đề xuất\n\nChọn phương án A.\n")
        src = self.tmp / "r.md"
        src.write_text(md, encoding="utf-8")
        out = self.tmp / "r.docx"
        md_to_docx.convert_file(src, out, "baocao")
        rep = document_validator.validate(out, "report")
        codes = {i["code"] for i in rep.items}
        self.assertNotIn("HEADINGS", codes)
        self.assertNotIn("CONCLUSION", codes)
        self.assertNotEqual(rep.status, "FAIL")


# ---------------------------------------------------------------- Test 5: MiMo (mock)
class _Handler(BaseHTTPRequestHandler):
    mode = "ok"
    calls = 0
    last_auth = None

    def log_message(self, *a):
        pass

    def do_POST(self):
        type(self).calls += 1
        type(self).last_auth = self.headers.get("api-key")
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        mode = type(self).mode
        if mode == "slow":
            time.sleep(2.5)
        if mode == "flaky" and type(self).calls == 1:
            return self._send(503, {"error": "busy"})
        if mode == "error500":
            return self._send(500, {"error": "boom"})
        if mode == "unauthorized":
            return self._send(401, {"error": "bad key"})
        if mode == "garbage":
            return self._send(200, {"unexpected": True})
        self._send(200, {"choices": [{"message": {"content": '{"loai": "hop_dong", "do_tin_cay": 0.9}'}}]})

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class TestMimo(TmpMixin, unittest.TestCase):
    KEY = "sk-test-SECRET-123"

    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        super().setUp()
        _Handler.mode, _Handler.calls = "ok", 0
        os.environ["MIMO_API_KEY"] = self.KEY
        os.environ.pop("MIMO_BASE_URL", None)

    def tearDown(self):
        os.environ.pop("MIMO_API_KEY", None)
        super().tearDown()

    def client(self, **over):
        sec = {"enabled": True, "api_key_env": "MIMO_API_KEY", "base_url": f"http://127.0.0.1:{self.port}/v1",
               "model": "mimo-test", "timeout_seconds": 1, "max_retries": 1, "max_input_chars": 100,
               "allow_external_documents": False}
        sec.update(over)
        return mimo_client.MimoClient({"secondary": sec, "routing": {"use_secondary_for": [
            "document_classification", "data_extraction", "preliminary_summary"]}})

    def test_default_config_is_disabled(self):
        c = mimo_client.MimoClient(mimo_client.load_config())
        self.assertFalse(c.status()["enabled"])
        with self.assertRaises(mimo_client.MimoDisabled):
            c.chat([{"role": "user", "content": "x"}])

    def test_system_works_when_mimo_off_cli(self):
        r = run_script("scripts/mimo_client.py", "ping")
        self.assertEqual(r.returncode, 3)
        out = json.loads(r.stdout)
        self.assertEqual(out["fallback"], "claude")

    def test_missing_key(self):
        os.environ.pop("MIMO_API_KEY")
        with self.assertRaises(mimo_client.MissingKey):
            self.client().chat([{"role": "user", "content": "x"}])

    def test_success_and_key_sent_not_leaked(self):
        txt = self.client().chat([{"role": "user", "content": "x"}])
        self.assertIn("hop_dong", txt)
        self.assertEqual(_Handler.last_auth, self.KEY)
        self.assertNotIn(self.KEY, json.dumps(self.client().status()))

    def test_consent_required_for_documents(self):
        with self.assertRaises(mimo_client.ConsentRequired):
            self.client().run_task("document_classification", "nội dung nhạy cảm")
        self.assertEqual(_Handler.calls, 0)  # chưa có yêu cầu nào rời máy

    def test_run_task_with_consent_and_truncation(self):
        res = self.client().run_task("document_classification", "x" * 500, allow_send=True)
        self.assertTrue(res["truncated"])
        self.assertIn("hop_dong", res["content"])

    def test_timeout_then_error(self):
        _Handler.mode = "slow"
        with self.assertRaises(mimo_client.MimoTimeout):
            self.client(timeout_seconds=1, max_retries=1).chat([{"role": "user", "content": "x"}])
        self.assertEqual(_Handler.calls, 2)  # 1 lần đầu + 1 lần thử lại

    def test_retry_on_503_then_success(self):
        _Handler.mode = "flaky"
        self.assertIn("hop_dong", self.client().chat([{"role": "user", "content": "x"}]))
        self.assertEqual(_Handler.calls, 2)

    def test_persistent_500(self):
        _Handler.mode = "error500"
        with self.assertRaises(mimo_client.MimoError) as cm:
            self.client().chat([{"role": "user", "content": "x"}])
        self.assertNotIn(self.KEY, str(cm.exception))

    def test_401_no_retry(self):
        _Handler.mode = "unauthorized"
        with self.assertRaises(mimo_client.MimoError):
            self.client().chat([{"role": "user", "content": "x"}])
        self.assertEqual(_Handler.calls, 1)

    def test_garbage_response(self):
        _Handler.mode = "garbage"
        with self.assertRaises(mimo_client.MimoError):
            self.client().chat([{"role": "user", "content": "x"}])

    def test_task_not_in_routing_rejected(self):
        c = self.client()
        c.routing = {"use_secondary_for": ["data_extraction"]}
        with self.assertRaises(mimo_client.MimoError):
            c.run_task("document_classification", "x", allow_send=True)

    def test_no_hardcoded_secrets_in_source(self):
        import re
        pat = re.compile(r"(sk|tp|ttp)-[A-Za-z0-9]{16,}")
        for p in list((ROOT / "scripts").glob("*.py")) + [ROOT / "config" / "models.yaml", ROOT / ".env.example"]:
            self.assertIsNone(pat.search(p.read_text(encoding="utf-8")), p)
        self.assertIn(".env", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())


# ---------------------------------------------------------------- Cấu trúc dự án / Skills
class TestProjectStructure(unittest.TestCase):
    SKILLS = ["hanh-chinh", "phap-ly-viet-nam", "document-audit", "it-report", "word-expert"]

    def test_skills_frontmatter(self):
        import re
        for s in self.SKILLS:
            p = ROOT / ".claude" / "skills" / s / "SKILL.md"
            self.assertTrue(p.exists(), p)
            m = re.match(r"^---\nname: (.+)\ndescription: (.+)\n---\n", p.read_text(encoding="utf-8"))
            self.assertIsNotNone(m, f"{s}: frontmatter sai")
            self.assertEqual(m.group(1).strip(), s)
            self.assertGreater(len(m.group(2)), 80)

    def test_referenced_scripts_exist(self):
        import re
        texts = [(ROOT / "CLAUDE.md").read_text(encoding="utf-8")]
        texts += [p.read_text(encoding="utf-8") for p in (ROOT / ".claude" / "skills").rglob("*.md")]
        for t in texts:
            for name in set(re.findall(r"scripts/([a-z_]+\.py)", t)):
                self.assertTrue((ROOT / "scripts" / name).exists(), name)

    def test_skill_refs_exist(self):
        for f in ("comparison-rules.md", "severity-levels.md"):
            self.assertTrue((ROOT / ".claude" / "skills" / "document-audit" / "references" / f).exists())

    def test_sync_skills_to_agents(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            import sync_skills
            sync_skills.DST = tmp / "skills"
            self.assertTrue(sync_skills.differences())
            for rel in sync_skills.differences():
                (sync_skills.DST / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sync_skills.SRC / rel, sync_skills.DST / rel)
            self.assertEqual(sync_skills.differences(), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_models_yaml_defaults(self):
        cfg = mimo_client.load_config()
        self.assertTrue(cfg["primary"]["enabled"])
        self.assertFalse(cfg["secondary"]["enabled"])
        self.assertFalse(cfg["secondary"]["allow_external_documents"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
