#!/usr/bin/env python3
"""Đồng bộ Skills từ .claude/skills/ (nguồn chính, cho Claude Code) sang .agents/skills/ (Antigravity).

Theo tài liệu chính thức của Google (codelab "Authoring Google Antigravity Skills"), Antigravity đọc
Skills của dự án ở <project>/.agents/skills/ với cùng định dạng SKILL.md (name + description).
Script chỉ sao chép, không xóa gì ở thư mục đích.

  python scripts/sync_skills.py          # sao chép
  python scripts/sync_skills.py --check  # chỉ kiểm tra có lệch không (mã thoát 1 nếu lệch)
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / ".claude" / "skills", ROOT / ".agents" / "skills"


def differences():
    diffs = []
    for f in sorted(p for p in SRC.rglob("*") if p.is_file()):
        rel = f.relative_to(SRC)
        g = DST / rel
        if not g.exists() or not filecmp.cmp(f, g, shallow=False):
            diffs.append(rel)
    return diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not SRC.exists():
        print(f"[LỖI] Không thấy {SRC}", file=sys.stderr)
        sys.exit(2)
    diffs = differences()
    if a.check:
        print("Đã đồng bộ." if not diffs else "Lệch ở: " + ", ".join(map(str, diffs)))
        sys.exit(1 if diffs else 0)
    for rel in diffs:
        (DST / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC / rel, DST / rel)
    print(f"Đã sao chép {len(diffs)} file vào {DST}" if diffs else "Không có gì cần đồng bộ.")


if __name__ == "__main__":
    main()
