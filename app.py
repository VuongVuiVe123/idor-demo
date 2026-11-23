#!/usr/bin/env python3
"""
IDOR Live Demo — "Cổng thông tin sinh viên"

A presentation lab, not a CTF: one story, one vulnerability (IDOR), watched
packet by packet in mitmproxy (see run-mitm.sh).

The fix is the two commented-out lines in load_student(): remove the "# "
during Act 5 and restart. `./run.sh reset` comments them out again.

LOCALHOST / LAB USE ONLY. All people and numbers are fictional.
"""
import os
import random
import re
import secrets
import sqlite3
import string
import sys

from flask import (
    Flask, abort, flash, g, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("DEMO_PORT", "15200"))

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config.update(
    DB_PATH=os.environ.get("DEMO_DB", os.path.join(BASE, "school.db")),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# ---------------------------------------------------------------------------
# Seed data: 30 students in one class, MSSV are sequential (like real schools)
# ---------------------------------------------------------------------------
FIRST_MSSV = 23520001
AN, BINH = 23520007, 23520008          # attacker and victim sit next to each other
NAMES = [
    "Phạm Quốc Bảo", "Lý Thu Hà", "Võ Minh Khang", "Đặng Ngọc Lan", "Bùi Gia Huy",
    "Hồ Thị Mai", "Nguyễn Văn An", "Trần Thị Bình", "Lê Hoàng Cường", "Phan Thảo Duyên",
    "Đỗ Tuấn Kiệt", "Ngô Bảo Ngọc", "Dương Minh Quân", "Mai Phương Thảo", "Huỳnh Đức Trí",
    "Tô Khánh Linh", "Châu Gia Bảo", "Lâm Mỹ Tiên", "Vũ Hải Đăng", "Trịnh Thu Trang",
    "Cao Nhật Minh", "Hà Kim Ngân", "Kiều Anh Tú", "Lương Bích Phượng", "Tạ Quang Vinh",
    "Quách Diễm My", "Đinh Công Sơn", "La Thanh Vy", "Mạc Đình Phúc", "Thái Ngọc Hân",
]
SUBJECTS = ["Lập trình Python", "Cơ sở dữ liệu", "Mạng máy tính",
            "An toàn thông tin", "Toán rời rạc"]
BANKS = ["Vietcombank", "BIDV", "Techcombank", "MB Bank", "ACB", "VPBank"]
ACCOUNTS = {AN: ("an", "an123"), BINH: ("binh", "binh123")}
SCHOLARSHIP_GPA = 8.5


def init_db():
    rng = random.Random(2026)
    con = sqlite3.connect(app.config["DB_PATH"])
    con.executescript("""
        DROP TABLE IF EXISTS grades;
        DROP TABLE IF EXISTS students;
        CREATE TABLE students (
            mssv INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            bank_account TEXT NOT NULL
        );
        CREATE TABLE grades (
            mssv INTEGER NOT NULL REFERENCES students(mssv),
            subject TEXT NOT NULL,
            score REAL NOT NULL
        );
    """)
    for i, name in enumerate(NAMES):
        mssv = FIRST_MSSV + i
        user, pw = ACCOUNTS.get(mssv, (f"sv{mssv}", secrets.token_hex(8)))
        phone = "09" + "".join(rng.choice(string.digits) for _ in range(8))
        acct = "".join(rng.choice(string.digits) for _ in range(10))
        con.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?)",
                    (mssv, user, generate_password_hash(pw), name, phone,
                     rng.choice(BANKS), acct))
        lo, hi = (8.8, 10.0) if mssv == BINH else (5.0, 9.6)
        for subj in SUBJECTS:
            con.execute("INSERT INTO grades VALUES (?,?,?)",
                        (mssv, subj, round(rng.uniform(lo, hi), 1)))
    con.commit()
    con.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_e):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Authentication: WHO are you?  (decided by the session cookie)
# ---------------------------------------------------------------------------
@app.before_request
def load_user():
    g.user = None
    if "mssv" in session:
        g.user = get_db().execute(
            "SELECT mssv, username, full_name FROM students WHERE mssv=?",
            (session["mssv"],)).fetchone()


# ---------------------------------------------------------------------------
# Authorization: MAY you access THIS student's data?  ← the whole lesson
# ---------------------------------------------------------------------------
def load_student(mssv):
    if g.user is None:
        abort(redirect(url_for("login")))                     # ✔ Bạn là AI?
    student = get_db().execute("SELECT * FROM students WHERE mssv = ?",
                               (mssv,)).fetchone()
    if student is None:
        abort(404)
    # if student["mssv"] != g.user["mssv"]:               # ✘ Bạn có QUYỀN?
    #     abort(404)
    return student


# ---------------------------------------------------------------------------
# Student portal
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if g.user is None:
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        row = get_db().execute("SELECT mssv, pw_hash FROM students WHERE username=?",
                               (request.form.get("username", ""),)).fetchone()
        if row and check_password_hash(row["pw_hash"], request.form.get("password", "")):
            session.clear()
            session["mssv"] = row["mssv"]
            return redirect(url_for("index"))
        error = "Sai tên đăng nhập hoặc mật khẩu"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/students/<int:mssv>/grades")
def grades(mssv):
    student = load_student(mssv)
    rows = get_db().execute("SELECT subject, score FROM grades WHERE mssv = ?",
                            (mssv,)).fetchall()
    gpa = round(sum(r["score"] for r in rows) / len(rows), 2)
    return render_template("grades.html", owner=student, rows=rows, gpa=gpa,
                           scholarship=gpa >= SCHOLARSHIP_GPA)


@app.route("/students/<int:mssv>/profile", methods=["GET", "POST"])
def profile(mssv):
    student = load_student(mssv)
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        acct = request.form.get("bank_account", "").strip()
        if not (re.fullmatch(r"0\d{9}", phone) and re.fullmatch(r"\d{6,16}", acct)):
            flash("Số điện thoại hoặc số tài khoản không hợp lệ.")
            return redirect(url_for("profile", mssv=mssv))
        db = get_db()
        db.execute("UPDATE students SET phone=?, bank_account=? WHERE mssv = ?",
                   (phone, acct, mssv))
        db.commit()
        flash("Đã lưu thông tin nhận học bổng.")
        return redirect(url_for("profile", mssv=mssv))
    return render_template("profile.html", owner=student)


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    if not os.path.exists(app.config["DB_PATH"]):
        init_db()
    print(f"🎓 IDOR Live Demo — app trên http://127.0.0.1:{PORT}")
    fixed = re.search(r'^\s*if student\["mssv"\] != g\.user\["mssv"\]:',
                      open(__file__, encoding="utf-8").read(), re.M)
    print(f"   Kiểm tra quyền sở hữu: {'BẬT (đã vá)' if fixed else 'TẮT (IDOR)'}")
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
