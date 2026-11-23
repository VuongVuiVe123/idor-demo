#!/usr/bin/env python3
"""
Pre-presentation self-check. Uses Flask's test client and a throw-away DB,
so it opens no port and leaves school.db and app.py untouched.

It tests two in-memory copies of app.py:
  before the fix (2 lines commented out) → An can read and modify Bình's data
  after the fix  (the "# " removed)      → the same requests get 404,
                                           An can still use her own pages
and tells you which state app.py is in right now.

Usage:  python verify_demo.py
"""
import os
import re
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "app.py")
os.environ["DEMO_DB"] = os.path.join(tempfile.mkdtemp(prefix="idor-demo-"), "t.db")

ACTIVE = re.compile(r'^    if student\["mssv"\] != g\.user\["mssv"\]:(.*)\n        abort\(404\)\n', re.M)
COMMENTED = re.compile(r'^    # if student\["mssv"\] != g\.user\["mssv"\]:(.*)\n    #     abort\(404\)\n', re.M)

SRC = open(APP, encoding="utf-8").read()
VULN_SRC = ACTIVE.sub(r'    # if student["mssv"] != g.user["mssv"]:\1\n    #     abort(404)\n', SRC)
FIXED_SRC = COMMENTED.sub(r'    if student["mssv"] != g.user["mssv"]:\1\n        abort(404)\n', SRC)

ok = True


def expect(name, cond):
    global ok
    ok &= bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def load(name, src):
    """Run a copy of app.py's source as its own module (templates still resolve)."""
    mod = types.ModuleType(name)
    mod.__file__ = APP
    sys.modules[name] = mod
    exec(compile(src, APP, "exec"), mod.__dict__)
    return mod


print("== app.py right now:",
      "FIXED (fix lines active)" if ACTIVE.search(SRC) else
      "IDOR (fix lines commented out)" if COMMENTED.search(SRC) else "fix lines NOT FOUND")
expect("fix lines found in load_student()", COMMENTED.search(VULN_SRC) and ACTIVE.search(FIXED_SRC))

for fixed, src in ((False, VULN_SRC), (True, FIXED_SRC)):
    demo = load("app_fixed" if fixed else "app_vuln", src)
    AN, BINH = demo.AN, demo.BINH

    def bank_of(mssv):
        with demo.app.app_context():
            return demo.get_db().execute(
                "SELECT bank_account FROM students WHERE mssv=?", (mssv,)).fetchone()[0]

    demo.init_db()
    c = demo.app.test_client()
    print(f"== {'after the fix' if fixed else 'before the fix'}")

    expect("/login renders", c.get("/login").status_code == 200)
    r = c.post("/login", data={"username": "an", "password": "an123"})
    expect("login sets session cookie", "session=" in r.headers.get("Set-Cookie", ""))
    expect("home renders", c.get("/").status_code == 200)
    expect("own grades 200", c.get(f"/students/{AN}/grades").status_code == 200)

    r = c.get(f"/students/{BINH}/grades")
    expect(f"Bình's grades → {404 if fixed else 200}", r.status_code == (404 if fixed else 200))

    before = bank_of(BINH)
    r = c.post(f"/students/{BINH}/profile",
               data={"phone": "0900000000", "bank_account": "9999999999"})
    expect(f"edit Bình's bank → {404 if fixed else 302}", r.status_code == (404 if fixed else 302))
    expect(f"Bình's account {'unchanged' if fixed else 'changed'}", (bank_of(BINH) == before) == fixed)

    r = c.post(f"/students/{AN}/profile",
               data={"phone": "0911111111", "bank_account": "1234567890"})
    expect("own profile update still works", r.status_code == 302 and bank_of(AN) == "1234567890")

    readable = sum(c.get(f"/students/{m}/grades").status_code == 200
                   for m in range(demo.FIRST_MSSV, demo.FIRST_MSSV + len(demo.NAMES)))
    expect(f"enumeration reads {1 if fixed else 30}/30", readable == (1 if fixed else 30))

    expect("unknown MSSV → 404", c.get("/students/1/grades").status_code == 404)
    c.get("/logout")
    expect("logged out → redirect to login", c.get(f"/students/{AN}/grades").status_code == 302)

print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
if ok and ACTIVE.search(SRC):
    print("⚠ app.py đang ở trạng thái ĐÃ VÁ — chạy ./run.sh reset trước khi demo.")
sys.exit(0 if ok else 1)
