# 🎓 IDOR Live Demo: "Đổi một con số, lấy cả lớp"

Đây là lab dùng để **trình diễn khi thuyết trình**, không phải bộ thử thách. Lab kể **một câu chuyện** và chỉ có **một lỗ hổng** là IDOR. Mọi gói tin giữa trình duyệt và server đều đi qua **mitmproxy**, nên cả lớp *nhìn thấy tận mắt* request được gửi đi như thế nào và server trả về những gì.

```
 Trình duyệt / script ──► mitmproxy :18080 ──► App :15200
                               │
                               └─► mitmweb :18081  (màn hình xem gói tin)
```

mitmproxy chạy ở **reverse mode**, nên không phải cấu hình proxy cho trình duyệt: chỉ cần mở `http://127.0.0.1:18080`, mọi gói tin đều tự đi qua mitmproxy.

**Không có màu, không có ghi chú tự động:** mitmweb chỉ hiện gói tin thật. Khán giả tự so sánh hai thứ trong mỗi request:
- **Cookie** `session=eyJtc3N2IjoyMzUyMDAwN30...`: *ai đang hỏi*. Phần đầu là Base64 của `{"mssv": 23520007}`. Cookie có chữ ký của server nên An không sửa được.
- **URL** `/students/23520008/grades`: *đang hỏi dữ liệu của ai*.

---

## Cài đặt (lần đầu tải về)

Cần **Python 3.10 trở lên**. Trên Windows nên dùng **WSL** (Ubuntu) để chạy được các file `.sh`.

```bash
git clone <link-repo-này>
cd <tên-repo>
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # cài Flask và mitmproxy
.venv/bin/python verify_demo.py               # phải in ALL CHECKS PASSED
```

Nếu `python3 -m venv` báo lỗi *ensurepip is not available*: chạy `sudo apt install python3-venv` rồi tạo lại.

Sau đó làm tiếp phần **Chuẩn bị** bên dưới. Các script `run.sh` và `run-mitm.sh` tự tìm thư mục `.venv`, không cần kích hoạt.

> ⚠ Lab chỉ chạy trên máy mình (`127.0.0.1`). Chỉ dùng để học, không dùng các kỹ thuật này với hệ thống của người khác.

## Chuẩn bị (5 phút trước giờ thuyết trình)

```bash
cd <tên-repo>
.venv/bin/python verify_demo.py      # phải in ALL CHECKS PASSED
./run.sh reset
```

**Terminal 1** chạy app (tắt kiểm tra quyền):

```bash
./run.sh
```

**Terminal 2** chạy mitmweb. Để nó chạy suốt buổi demo:

```bash
./run-mitm.sh
```

**Bố trí màn hình chiếu:** chia đôi màn hình.

| Bên trái: trang web | Bên phải: mitmweb |
|---|---|
| `http://127.0.0.1:18080/`, đăng nhập `an / an123` | `http://127.0.0.1:18081/` |
| Phóng to (Ctrl +) để **thanh địa chỉ** dễ đọc | Ô **Search** gõ `~u /students/ \| ~u /login` để ẩn các request file tĩnh |

Mở thêm **Terminal 3** cho Màn 3.

**Nhân vật:**
- **An** (MSSV 23520007): sinh viên bình thường, đóng vai kẻ tấn công.
- **Bình** (MSSV 23520008): ngồi cạnh An, **điểm cao nhất lớp và được học bổng**. Bình là nạn nhân.

---

## Kịch bản: 5 màn, khoảng 12 phút

### Màn 1: Đăng nhập, gói tin đầu tiên (2 phút)

**Làm:** đăng nhập `an / an123`, sau đó bấm **Xem bảng điểm**.

**Trên mitmweb, mở 2 flow:**

1. `POST /login`
   - Tab *Request*: body là `username=an&password=an123`.
   - Tab *Response*: header `Set-Cookie: session=...`.
   > 🗣 "Từ giờ, trình duyệt sẽ tự gửi kèm cookie này trong mọi request. Đây là cách server **nhận ra** An."

2. `GET /students/23520007/grades`
   ```http
   GET /students/23520007/grades HTTP/1.1
   Cookie: session=eyJtc3N2IjoyMzUyMDAwN30...      ← "tôi là An"
   ```
   > 🗣 "Một request mang **hai thông tin**: **Cookie** cho biết *ai đang hỏi*, còn **URL** cho biết *đang hỏi dữ liệu của ai*. Ở đây cả hai đều là 23520007, nên mọi thứ khớp nhau."

### Màn 2: Sửa một con số trong gói tin (3 phút)

**Cách A, trên trình duyệt** (dễ hiểu nhất): sửa `23520007` thành **`23520008`** trên thanh địa chỉ rồi nhấn Enter.

**Cách B, ngay trong mitmweb** (để cả lớp thấy *gói tin bị sửa*):
1. Chọn flow `GET /students/23520007/grades`.
2. Bấm **Duplicate** để tạo bản sao, rồi trong tab *Request* sửa path thành `/students/23520008/grades`.
3. Bấm **Replay**.

**Khán giả thấy:**
- Trang web hoặc tab *Response*: bảng điểm của **Trần Thị Bình**, ĐTB 9.46, ✔ đủ điều kiện học bổng.
- Trên mitmweb, flow mới: **Cookie vẫn là của An**, URL là `23520008`, response `200 OK` kèm bảng điểm của Bình.

**Đặt hai flow cạnh nhau để so sánh:**

| | Flow Màn 1 | Flow Màn 2 |
|---|---|---|
| Cookie | session của An | **vẫn là session của An** |
| URL | `/students/23520007/...` | `/students/2352000`**`8`**`/...` |
| Bên trong cookie | `{"mssv": 23520007}` | **`{"mssv": 23520007}`** |
| Dữ liệu trả về | điểm của An | **điểm của Bình** |

> 🗣 "Chỉ có **một ký tự** thay đổi. Server biết rõ người hỏi là An (cookie ghi `{"mssv": 23520007}`), nhưng nó **không so sánh** người hỏi với chủ của dữ liệu. Server mới hỏi *bạn là ai*, chưa hỏi *bạn có quyền không*. Đó chính là **IDOR**."

### Màn 3: Một vòng lặp lấy cả lớp (2 phút)

**Làm:** ở Terminal 3, chạy

```bash
.venv/bin/python enumerate.py
```

Script này đi qua mitmproxy (cổng 18080), nên mọi request đều hiện trên mitmweb.

**Khán giả thấy:**
- mitmweb: **30 flow** liên tiếp `GET /students/23520001…23520030/grades`, tất cả đều `200 OK` với **cùng một cookie** của An.
- Terminal: in lần lượt MSSV, họ tên và điểm trung bình, cuối cùng là "Đọc được 30/30 bảng điểm".

> 🗣 "MSSV có ba đặc điểm: **tăng dần**, **in trên thẻ sinh viên**, và **ai cũng biết**. Nhìn sang mitmweb: các gói tin giống hệt nhau, cùng một cookie, chỉ có con số trên URL tăng lên. Có 30 hay 9,8 triệu bản ghi thì vẫn là vòng lặp này. Năm 2022, nhà mạng **Optus** ở Úc bị lộ dữ liệu của khoảng 9,8 triệu khách hàng theo đúng cách đó: một API trả dữ liệu theo `contactid` tăng dần."

### Màn 4: Không chỉ xem, mà còn sửa được (2 phút)

**Làm:**
1. Mở `http://127.0.0.1:18080/students/23520008/profile`. Trang hiện form thông tin nhận học bổng **của Bình**.
2. Sửa *Số tài khoản nhận học bổng* thành `9999999999` rồi bấm **Lưu**.

**Trên mitmweb,** mở flow `POST /students/23520008/profile`:

```http
POST /students/23520008/profile HTTP/1.1
Cookie: session=...                     ← vẫn là An
Content-Type: application/x-www-form-urlencoded

phone=09xxxxxxxx&bank_account=9999999999
```


> 🗣 "Đến kỳ trả học bổng, tiền của Bình sẽ chuyển vào tài khoản do An chọn. IDOR không chỉ làm **lộ** dữ liệu (mất tính bí mật). Nó còn cho phép **sửa** dữ liệu (mất tính toàn vẹn), và khi đó là **mất tiền thật**."

### Màn 5: Vá lỗi chỉ bằng một dòng, rồi so sánh gói tin trước và sau (3 phút)

**Làm:**

1. Mở [`app.py`](app.py), hàm `load_student()`. Hai dòng kiểm tra quyền đang bị comment:
   ```python
   def load_student(mssv):
       if g.user is None:
           abort(redirect(url_for("login")))                     # ✔ Bạn là AI?
       student = db.execute("SELECT * FROM students WHERE mssv = ?", (mssv,)).fetchone()
       ...
       # if student["mssv"] != g.user["mssv"]:               # ✘ Bạn có QUYỀN?
       #     abort(404)
       return student
   ```
   Bôi đen 2 dòng đó, bấm **Ctrl+/** để bỏ dấu `#`, rồi **Ctrl+S**.

2. Ở **Terminal 1**: nhấn Ctrl+C, rồi chạy lại `./run.sh` (terminal in *"BẬT (đã vá)"*). **Không tắt mitmweb**, vì các flow cũ được giữ lại để so sánh.

3. Đăng nhập lại `an / an123`, rồi lặp lại đúng các thao tác cũ:
   - Mở `/students/23520008/grades`: nhận **404**, response không còn dữ liệu của Bình.
   - Chạy lại `enumerate.py`: chỉ còn **1/30** (dữ liệu của chính An).
   - Mở `/students/23520007/grades`: An **vẫn dùng bình thường**.

**Đặt hai flow cạnh nhau trên mitmweb:**

| | Trước khi vá | Sau khi vá |
|---|---|---|
| Request | `GET /students/23520008/grades` + cookie An | **giống hệt** |
| Server | dòng kiểm tra quyền **tắt** | dòng kiểm tra quyền **bật** |
| Response | `200` + bảng điểm của Bình | **`404`**, không có dữ liệu |

> 🗣 "Gói tin tấn công **không đổi một byte nào**. Thứ thay đổi là server: giờ nó tự hỏi thêm một câu. Không cần mã hoá URL, không cần đổi MSSV sang UUID, không cần tường lửa. Chỉ cần **một dòng kiểm tra quyền** ở server."

**Câu hỏi để cả lớp suy nghĩ:** *"Vì sao trả về 404 chứ không phải 403?"*
Trả lời: nếu trả 403, kẻ tấn công biết được *"MSSV này có tồn tại"* và vẫn liệt kê được danh sách. Trả 404 thì không lộ thông tin gì.

---

## Câu kết

> **Xác thực** trả lời *"Bạn là ai?"*. **Phân quyền** trả lời *"Bạn được động vào cái gì?"*. IDOR xảy ra khi server chỉ hỏi câu thứ nhất.
> Trên đường truyền, một gói tin IDOR **trông hoàn toàn hợp lệ**: cookie thật, status 200. Vì vậy chỉ có **server** mới chặn được nó.

**Dẫn chứng để chốt bài:**
- OWASP Top 10:2025: **Broken Access Control đứng #1**, và IDOR thuộc nhóm này.
- CISA, NSA và ACSC phát hành khuyến cáo riêng về IDOR: [AA23-208A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-208a) (07/2023).
- First American (2019): đổi số trong link là đọc được khoảng 885 triệu hồ sơ ([Krebs](https://krebsonsecurity.com/2019/05/first-american-financial-corp-leaked-hundreds-of-millions-of-title-insurance-records/)).

---

## Câu hỏi từ khán giả

| Câu hỏi | Trả lời ngắn |
|---|---|
| "Dùng HTTPS thì có chặn được không?" | Không. HTTPS chỉ chống người *ở giữa* đọc gói tin. Ở đây chính An gửi request bằng tài khoản của mình, và request đó hoàn toàn hợp lệ về mặt giao thức. |
| "Đổi MSSV sang UUID là xong?" | Không. Đó chỉ là lớp bổ sung, vì ID vẫn có thể lộ qua link chia sẻ, log hay API khác. Server vẫn phải kiểm tra quyền. |
| "Ẩn nút, ẩn link trên giao diện thì sao?" | Ở Màn 2 (cách B), request được sửa và gửi lại thẳng từ mitmweb, không cần đến giao diện web. |
| "Scanner có tìm ra lỗi này không?" | Rất khó, vì gói tin trông bình thường (status 200). Cần test với **2 tài khoản** và viết test tự động giống `verify_demo.py`. |

---

## Cấu trúc lab

| File | Vai trò |
|---|---|
| `app.py` | Cổng sinh viên. Toàn bộ bài học nằm trong hàm `load_student()`. Không có code riêng cho demo. |
| `run.sh` | Terminal 1: chạy app (`./run.sh`). `./run.sh reset` dựng lại dữ liệu và comment lại 2 dòng vá, đưa lab về trạng thái trước demo. |
| `run-mitm.sh` | Terminal 2: mitmweb reverse proxy `:18080` → app `:15200`, giao diện tại `:18081`. |
| `enumerate.py` | Script cho Màn 3, mặc định đi qua mitmproxy. Chỉ chạy được với `127.0.0.1` / `localhost`. |
| `verify_demo.py` | Tự kiểm tra bản lỗi và bản đã vá, và cho biết `app.py` đang ở trạng thái nào. Không mở cổng mạng, không sửa `school.db` hay `app.py`. |

App chỉ có **một** lỗ hổng là IDOR: SQL dùng tham số `?`, mật khẩu được hash, template tự escape, và server chỉ lắng nghe `127.0.0.1`. Mọi người và số liệu trong lab đều là hư cấu.

**Dùng trên PowerShell (Windows):**
- Terminal 1: `python app.py`
- Terminal 2: `mitmweb --mode reverse:http://127.0.0.1:15200@18080 --set web_port=18081`
