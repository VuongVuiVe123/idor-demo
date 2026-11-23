# Hướng dẫn demo IDOR: làm, nói và kiến thức

Mỗi bước có 3 phần:
- 🖱 **Làm**: thao tác trên máy.
- 🗣 **Nói**: lời nói khi thao tác.
- 📚 **Kiến thức**: khái niệm cần nêu ở bước đó.

Toàn bộ demo dài khoảng 10–12 phút. Chèn vào sau **slide 6**, demo xong thì quay lại **slide 7**.

---

## 0. Chuẩn bị (làm trước giờ thuyết trình, khoảng 5 phút)

Mở 3 cửa sổ terminal WSL. Ở terminal nào cũng chạy:

```bash
cd <tên-repo>
```

**Terminal 1** kiểm tra lab, dựng lại dữ liệu và chạy app ở chế độ lỗi:

```bash
.venv/bin/python verify_demo.py
```

```bash
./run.sh reset
```

```bash
./run.sh
```

**Terminal 2** chạy mitmweb (để chạy suốt buổi, không tắt):

```bash
./run-mitm.sh
```

**Terminal 3** để trống, dùng ở Màn 3.

**Trình duyệt bên Windows**, chia đôi màn hình:
- **Trái:** `http://127.0.0.1:18080`. Bấm Ctrl + vài lần cho thanh địa chỉ to, dễ đọc.
- **Phải:** `http://127.0.0.1:18081` (mitmweb). Ở ô **Search** gõ `~u /students/ | ~u /login` để ẩn các request file tĩnh.

Kiểm tra lại trước khi lên:
- `verify_demo.py` in ra **ALL CHECKS PASSED**.
- mitmweb đang trống.
- Trình duyệt đang ở trang đăng nhập.
- Nếu trước đó từng đăng nhập thì mở tab ẩn danh cho sạch cookie.

---

## Mở đầu demo (30 giây)

🗣 *"Đây là một cổng thông tin sinh viên do em tự viết, có 30 sinh viên. Có hai nhân vật: **An**, MSSV 23520007, là sinh viên bình thường và lát nữa sẽ đóng vai kẻ tấn công. **Bình**, MSSV 23520008, ngồi ngay cạnh An, điểm cao nhất lớp và đang được học bổng. Bên phải là mitmproxy. Mọi gói tin giữa trình duyệt và server đều đi qua đây, nên mình sẽ thấy tận mắt từng request gửi đi và server trả về gì."*

📚 **mitmproxy** là proxy đứng giữa trình duyệt và server, cho phép xem, sửa và gửi lại gói tin HTTP. Ở đây nó chạy ở **reverse mode**: trình duyệt vào cổng 18080, mitmproxy ghi lại rồi chuyển tiếp tới app thật ở cổng 15200. Đây là công cụ hợp pháp mà pentester dùng hằng ngày (tương tự Burp Suite).

---

## Màn 1: Đăng nhập và gói tin đầu tiên (2 phút)

🖱 **Làm:**
1. Đăng nhập bằng `an` / `an123`.
2. Trên mitmweb, bấm flow **`POST /login`**:
   - Tab **Request**: chỉ vào body `username=an&password=an123`.
   - Tab **Response**: chỉ vào header `Set-Cookie: session=...`.

🗣 *"Khi đăng nhập, trình duyệt gửi username và mật khẩu lên. Server kiểm tra đúng thì trả về một **cookie session**. Từ giờ trình duyệt tự gửi kèm cookie này trong mọi request, và nhờ nó server biết người đang hỏi là An."*

📄 **Chỉ vào code** (mở `app.py` trong VS Code, bấm **Ctrl+G** rồi gõ số dòng để nhảy tới):

```python
# app.py:157 — trong hàm login(): đăng nhập đúng thì ghi MSSV vào cookie session
            session["mssv"] = row["mssv"]          # session = {"mssv": 23520007}

# app.py:116 — chạy TRƯỚC MỌI request: đọc cookie để biết người hỏi là ai
def load_user():
    g.user = None
    if "mssv" in session:
        g.user = get_db().execute(
            "SELECT mssv, username, full_name FROM students WHERE mssv=?",
            (session["mssv"],)).fetchone()     # g.user = An
```

🗣 *"Đây là phần xác thực: server lấy MSSV từ cookie, rồi lưu người đang hỏi vào biến `g.user`. Từ giờ trong mọi request, `g.user` luôn là An. Mọi người nhớ biến này, lát nữa sẽ thấy server **có** nó nhưng **không dùng**."*

📚 **Xác thực (Authentication)** trả lời câu hỏi *"Bạn là ai?"*. Ở đây server xác thực bằng mật khẩu, sau đó dùng cookie session để nhớ người dùng vì HTTP là giao thức không trạng thái (stateless).
*(Nếu có ai hỏi vì sao thấy được mật khẩu: vì lab chạy HTTP trên localhost. Web thật dùng HTTPS, nhưng HTTPS **không** chống được IDOR. Lát nữa sẽ thấy lý do.)*

🖱 **Làm tiếp:**
3. Bấm **Xem bảng điểm**.
4. Trên mitmweb, bấm flow **`GET /students/23520007/grades`**:
   - Tab Request: chỉ vào **URL** và dòng **Cookie**.
   - (Tuỳ chọn) Copy phần cookie trước dấu chấm đầu tiên, mở Console của trình duyệt (F12) gõ `atob("eyJtc3N2IjoyMzUyMDAwN30")` → ra `{"mssv":23520007}`.

🗣 *"Mọi người để ý: một request mang **hai thông tin**. **Cookie** cho biết *ai đang hỏi*, đó là An. **Con số trên URL** cho biết *đang hỏi dữ liệu của ai*, cũng là 23520007. Hai thứ khớp nhau nên mọi thứ bình thường. Cookie này nhìn thì lạ, nhưng thực ra chỉ là `{"mssv": 23520007}` được mã hoá Base64 và có chữ ký của server, nên An không sửa được. Nhờ nó server **biết chắc** người hỏi là An."*

📚 **Tham chiếu trực tiếp đến đối tượng (Direct Object Reference):** URL `/students/23520007/grades` chứa thẳng khoá chính (MSSV) của bản ghi trong database. Bản thân việc này chưa phải lỗi. Lỗi là khi server **tin** con số đó mà không kiểm tra.

---

## Màn 2: Sửa một con số (3 phút), cao trào của demo

🖱 **Làm (cách A, trên trình duyệt):** sửa `23520007` thành **`23520008`** trên thanh địa chỉ rồi nhấn Enter.

🗣 *"Giờ An thử sửa **đúng một chữ số**: 7 thành 8..."* (dừng 1–2 giây cho khán giả nhìn) *"...và đây là bảng điểm của **Trần Thị Bình**: điểm trung bình 9,46, đủ điều kiện học bổng. An không hack mật khẩu của Bình, không cần công cụ gì đặc biệt, chỉ sửa URL."*

🖱 **Làm:** trên mitmweb, bấm flow mới `GET /students/23520008/grades`. Chỉ vào **Cookie** (vẫn là cookie của An), **URL** (`23520008`) và response **`200 OK`** kèm bảng điểm của Bình.

🗣 *"So hai gói tin này với nhau: **cookie vẫn là của An**, bên trong vẫn ghi `{"mssv": 23520007}`. Tức là server biết người hỏi là An, nhưng nó **không so sánh** người hỏi với chủ của dữ liệu. Server mới hỏi *'bạn là ai'*, chưa hỏi *'bạn có quyền không'*. Đó chính là **IDOR**."*

| | Màn 1 | Màn 2 |
|---|---|---|
| Cookie | An | **vẫn là An** |
| URL | `.../23520007/...` | `.../2352000`**`8`**`/...` |
| Dữ liệu trả về | điểm của An | **điểm của Bình** |

📄 **Chỉ vào code: vì sao đổi 07 thành 08 lại ra điểm của Bình.** Đi theo đường đi của request `GET /students/23520008/grades`:

```python
# app.py:169 — số trên URL được gán vào biến mssv
@app.route("/students/<int:mssv>/grades")        # mssv = 23520008  ← do An gõ
def grades(mssv):
    student = load_student(mssv)                 # → nhảy xuống hàm kiểm tra
    rows = get_db().execute("SELECT subject, score FROM grades WHERE mssv = ?",
                            (mssv,)).fetchall()  # ← tra điểm theo số TRÊN URL
```

```python
# app.py:127 — hàm "kiểm tra" trước khi trả dữ liệu
def load_student(mssv):
    if g.user is None:                                   # ① Đã đăng nhập chưa?
        abort(redirect(url_for("login")))                #    An: rồi → qua
    student = get_db().execute("SELECT * FROM students WHERE mssv = ?",
                               (mssv,)).fetchone()
    if student is None:                                  # ② MSSV có tồn tại?
        abort(404)                                       #    08 có thật → qua
    # if student["mssv"] != g.user["mssv"]:             # ③ Có QUYỀN? → đang bị comment
    #     abort(404)                                     #    = không chạy
    return student                                       # → trả hồ sơ Bình
```

🗣 *"Request đi qua ba cửa. **Cửa 1**: An đã đăng nhập chưa? Rồi, cho qua. **Cửa 2**: MSSV 08 có tồn tại không? Có, cho qua. **Cửa 3** là cửa duy nhất hỏi *'dữ liệu này có phải của bạn không'*: nó so `student["mssv"]` (chủ dữ liệu, 08) với `g.user["mssv"]` (người hỏi, 07). Nhưng hai dòng này đang có dấu `#` ở đầu, tức là bị **comment**: Python bỏ qua, **coi như không có cửa thứ ba**, giống như lập trình viên quên viết. Kết quả là câu SQL ở dòng 172 chạy với `WHERE mssv = 23520008` và trả điểm của Bình."*

🗣 *(câu chốt khi chỉ code)* *"Server có **cả hai** con số: 07 từ cookie và 08 từ URL. Nhưng nó chỉ dùng con số trên URL để lấy dữ liệu, và **không bao giờ đặt hai số cạnh nhau để so sánh**. Thiếu đúng một phép so sánh đó chính là IDOR."*

> 💡 Mẹo chiếu: trong VS Code bấm **Ctrl +** cho chữ to, và bôi đen dòng 134–135 khi nói "cửa thứ ba".

📚 **Kiến thức chính của cả bài:**
- **Phân quyền (Authorization)** trả lời *"Bạn được động vào cái gì?"*.
- **IDOR (Insecure Direct Object Reference)** là lỗi server dùng ID do người dùng gửi lên để lấy dữ liệu, nhưng **không kiểm tra người đó có phải chủ sở hữu không**.
- IDOR thuộc nhóm **Broken Access Control**, **hạng #1 trong OWASP Top 10:2025**, mã **CWE-639**. Trong API, OWASP gọi lỗi này là **BOLA**.
- Kiểu này là **leo thang theo chiều ngang**: An xem dữ liệu của một người **cùng cấp**.

🖱 **Làm (cách B, nếu còn thời gian, rất ấn tượng):**
1. Trên mitmweb chọn flow `GET /students/23520007/grades` cũ.
2. Bấm **Duplicate**, rồi trong tab Request sửa path thành `/students/23520008/grades`.
3. Bấm **Replay**.

🗣 *"Có người sẽ nói 'vậy ẩn URL đi là xong'. Nhưng ở đây em không cần trình duyệt nữa: em sửa thẳng gói tin và gửi lại. **Mọi thứ ở phía client đều kiểm soát được**, nên giấu nút hay giấu link trên giao diện không bảo vệ được gì."*

📚 Nguyên tắc: **không bao giờ tin dữ liệu từ client**. Kiểm tra quyền phải nằm ở **server**.

---

## Màn 3: Một vòng lặp lấy cả lớp (2 phút)

🖱 **Làm:** ở **Terminal 3** chạy:

```bash
.venv/bin/python enumerate.py
```

Chỉ cho khán giả thấy hai bên:
- mitmweb hiện **30 request** liên tiếp, tất cả `200 OK`, **cùng một cookie**, chỉ có số trên URL tăng dần.
- Terminal in ra MSSV, họ tên và điểm trung bình từng người, cuối cùng là "Đọc được 30/30 bảng điểm".

🗣 *"MSSV có ba đặc điểm: **tăng dần**, **in trên thẻ sinh viên**, và **ai cũng biết**. Nên chỉ cần một vòng lặp vài dòng là lấy được cả lớp trong một giây. Nhìn sang mitmproxy: các gói tin giống hệt nhau, cùng một cookie, chỉ có con số tăng lên. Lớp có 30 người hay hệ thống có 9,8 triệu người thì cũng là vòng lặp này. Năm 2022, nhà mạng **Optus** ở Úc bị lộ dữ liệu khoảng **9,8 triệu khách hàng** đúng theo cách đó."*

📚 **Enumeration (liệt kê):** khi ID **dễ đoán** (số tự tăng), một lỗi IDOR trên một bản ghi biến thành rò rỉ **toàn bộ** database. Đây là lý do IDOR thường gây ra những vụ lộ dữ liệu cực lớn (First American 2019: khoảng 885 triệu hồ sơ).

---

## Màn 4: Không chỉ xem, mà còn sửa được (2 phút)

🖱 **Làm:**
1. Mở `http://127.0.0.1:18080/students/23520008/profile`. Trang hiện form nhận học bổng **của Bình**.
2. Sửa **Số tài khoản nhận học bổng** thành `9999999999` rồi bấm **Lưu**.
3. Trên mitmweb, mở flow `POST /students/23520008/profile` và chỉ vào body `bank_account=9999999999` cùng cookie (vẫn là An).

🗣 *"Không chỉ xem. An còn **sửa** được số tài khoản nhận học bổng của Bình. Đến kỳ trả học bổng, tiền của Bình sẽ chuyển vào tài khoản do An chọn. Đây không còn là lộ thông tin nữa, mà là **mất tiền thật**."*

📄 **Chỉ vào code:**

```python
# app.py:179 — trang sửa hồ sơ học bổng, cũng lấy mssv từ URL
@app.route("/students/<int:mssv>/profile", methods=["GET", "POST"])
def profile(mssv):
    student = load_student(mssv)          # ← vẫn là hàm thiếu cửa thứ ba
    ...
        db.execute("UPDATE students SET phone=?, bank_account=? WHERE mssv = ?",
                   (phone, acct, mssv))   # app.py:189 — GHI vào hồ sơ của mssv trên URL
```

🗣 *"Trang sửa hồ sơ dùng **chung** hàm `load_student()` đã thấy ở Màn 2, nên cũng thiếu bước kiểm tra quyền. Câu `UPDATE` ở dòng 189 ghi thẳng vào hồ sơ có MSSV trên URL, tức là hồ sơ của Bình."*

📚 **Hậu quả theo CIA:**
- Đọc dữ liệu: mất **tính bí mật (Confidentiality)**.
- Sửa hoặc xoá dữ liệu: mất **tính toàn vẹn (Integrity)**.

Theo STRIDE, đó là **Information Disclosure** và **Tampering**. IDOR xảy ra với **mọi hành động** (GET, POST, PUT, DELETE), không chỉ việc xem.

---

## Màn 5: Vá lỗi bằng hai dòng code, gõ trực tiếp (3 phút)

🖱 **Làm:**
1. Mở `app.py` trong VS Code, bấm **Ctrl+G** gõ **134**. Đây là hàm `load_student()` đã chiếu ở Màn 2:
   ```python
       if student is None:
           abort(404)
       # if student["mssv"] != g.user["mssv"]:               # ✘ Bạn có QUYỀN?
       #     abort(404)
       return student
   ```
2. Bôi đen 2 dòng 134–135, bấm **Ctrl+/** để bỏ dấu `#` (hoặc xoá tay `# ` ở đầu mỗi dòng):
   ```python
       if student["mssv"] != g.user["mssv"]:               # ✘ Bạn có QUYỀN?
           abort(404)
   ```
3. Bấm **Ctrl+S** để lưu.

🗣 *"Đây là toàn bộ bản vá: **hai dòng** so sánh *chủ của dữ liệu* (`student["mssv"]`, lấy từ URL) với *người đang hỏi* (`g.user["mssv"]`, lấy từ cookie). Không khớp thì trả 404. Vì cả trang bảng điểm và trang sửa hồ sơ đều gọi `load_student()`, **hai dòng này vá cả hai lỗi**: đọc ở Màn 2 và sửa ở Màn 4."*

🖱 **Làm tiếp:**
4. Ở **Terminal 1**: nhấn **Ctrl+C**, rồi chạy lại `./run.sh`. Terminal in *"Kiểm tra quyền sở hữu: BẬT (đã vá)"*. **Không** tắt mitmweb.
5. Trên trình duyệt, đăng nhập lại `an` / `an123` (khởi động lại app thì session cũ hết hạn).
6. Mở `/students/23520008/grades`: nhận **404**. Trên mitmweb, đặt flow này cạnh flow cũ ở Màn 2: request giống hệt, nhưng response từ `200` thành `404`.
7. Ở Terminal 3 chạy lại `enumerate.py`: chỉ còn **1/30**, là dữ liệu của chính An.
8. Mở `/students/23520007/grades`: An **vẫn dùng bình thường**.

🗣 *"Đặt hai gói tin trước và sau khi vá cạnh nhau: **request giống hệt từng byte**. Thứ thay đổi là **server**, giờ nó hỏi thêm một câu. Không cần mã hoá URL, không cần đổi MSSV sang UUID, không cần tường lửa."*

| | Trước khi vá | Sau khi vá |
|---|---|---|
| Request | `GET /students/23520008/grades` + cookie An | **giống hệt** |
| Server | dòng kiểm tra quyền **tắt** | dòng kiểm tra quyền **bật** |
| Response | `200` + điểm của Bình | **`404`** |

❓ **Hỏi khán giả:** *"Vì sao em trả 404 mà không phải 403 Forbidden?"*

📚 **Trả lời:** nếu trả 403, kẻ tấn công vẫn biết *"MSSV này tồn tại"* và vẫn liệt kê được danh sách. Trả 404 thì không lộ thông tin gì, vì với kẻ tấn công, dữ liệu của người khác coi như *không tồn tại*.

📚 **Nguyên tắc phòng chống** (sẽ nói kỹ ở slide 13–14):
- Kiểm tra quyền sở hữu ở **server** cho **mọi** request.
- Mặc định **từ chối (deny by default)**.

---

## Câu chốt demo (20 giây), rồi quay lại slide 7

🗣 *"Tóm lại: **xác thực** là *'bạn là ai'*, **phân quyền** là *'bạn được động vào cái gì'*. IDOR xảy ra khi server chỉ hỏi câu thứ nhất. Và trên đường truyền, gói tin IDOR **trông hoàn toàn hợp lệ**: cookie thật, status 200. Nên chỉ có server mới chặn được nó. Vậy vì sao một lỗi đơn giản như vậy lại phổ biến đến thế? Mời mọi người xem slide tiếp theo."*

➡ **QUAY LẠI SLIDE 7.**

---

## Nếu khán giả hỏi

| Câu hỏi | Trả lời ngắn |
|---|---|
| Dùng HTTPS có chặn được không? | Không. HTTPS chống người **ở giữa** đọc gói tin. Ở đây chính An gửi request bằng tài khoản thật của mình. |
| Đổi MSSV sang UUID là xong? | Không. UUID chỉ khó đoán hơn, ID vẫn lộ qua link chia sẻ, log hay API khác. Server **vẫn phải** kiểm tra quyền. |
| Ẩn nút, ẩn link trên giao diện thì sao? | Màn 2 cách B đã cho thấy: sửa gói tin trực tiếp, không cần giao diện. |
| Scanner tự động có tìm ra không? | Rất khó, vì gói tin trông bình thường (status 200). Cần test với **2 tài khoản**, giống `verify_demo.py`. |

## Sự cố khi demo

| Sự cố | Cách xử lý |
|---|---|
| Trang 18080 không mở được | Kiểm tra Terminal 1 (app) và Terminal 2 (mitmweb) còn chạy không. |
| mitmweb quá nhiều dòng | Gõ lại bộ lọc `~u /students/ \| ~u /login`. |
| Sau khi chạy lại `./run.sh` bị đẩy về trang đăng nhập | Bình thường: app khởi động lại nên session cũ hết hạn. Đăng nhập lại. |
| Dữ liệu hoặc code còn ở trạng thái của lần tập trước | Ctrl+C ở Terminal 1, chạy `./run.sh reset` (dựng lại dữ liệu **và** comment lại 2 dòng vá), rồi `./run.sh`. |
| Terminal in *"BẬT (đã vá)"* ngay từ đầu | Lần tập trước quên reset. Chạy `./run.sh reset` rồi `./run.sh`. |
| Màn 5: chạy lại `./run.sh` báo `IndentationError` | Gõ sai thụt lề. Bấm Ctrl+Z trong VS Code cho đến khi về như cũ, rồi bôi đen 2 dòng và bấm Ctrl+/. Dòng `if` thụt **4** dấu cách, dòng `abort` thụt **8**. |
| Báo cổng đang bị dùng | Chạy `fuser -k 15200/tcp`, rồi chạy lại `./run.sh`. |
