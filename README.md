# Hệ Thống Gợi Ý Phim (Movie Recommendation System)

Đây là Đồ án về Hệ thống Gợi ý Phim, áp dụng các kỹ thuật Học máy để đưa ra những đề xuất phim chính xác và cá nhân hóa cho người dùng. 

Dự án bao gồm việc xây dựng một 파ypline xử lý dữ liệu, huấn luyện các mô hình **Lọc cộng tác (Collaborative Filtering)** thông qua Matrix Factorization (SGD) và **Lọc dựa trên nội dung (Content-Based Filtering)** qua TF-IDF. Từ đó, kết hợp thành một mô hình **Hybrid** hoàn chỉnh. Ngoài phần phân tích và huấn luyện trên Jupyter Notebook, đồ án còn cung cấp một ứng dụng web đầy đủ tính năng xây dựng bằng **FastAPI** để trực quan hóa và ứng dụng mô hình vào thực tế.

---

## 🌟 Tính năng chính

- **Trang chủ & Khám phá phim**: Hiển thị các bộ phim thịnh hành, phân loại theo thể loại, hỗ trợ tìm kiếm phim.
- **Hệ thống Gợi ý Hybrid**: Đề xuất các bộ phim dựa trên sự kết hợp giữa:
  - Hành vi đánh giá phim trong quá khứ của người dùng (Collaborative Filtering).
  - Độ tương đồng về nội dung phim (Content-Based Filtering).
- **Giải quyết bài toán Cold-Start**: Người dùng mới đăng ký sẽ trải qua bước *Onboarding* để chọn các thể loại phim yêu thích, hệ thống sẽ dùng dữ liệu này để đưa ra các gợi ý ban đầu.
- **Tương tác phim**: Người dùng có thể xem chi tiết phim, thực hiện đánh giá (rating) và thêm vào danh sách yêu thích (watchlist).
- **Quản lý Tài khoản (Auth)**: Hỗ trợ đăng ký, đăng nhập, và quản lý hồ sơ, lịch sử xem, lịch sử đánh giá phim.

---

## 🏗 Kiến trúc Dự án (Mô hình 3 Lớp - 3 Tier Architecture)

Dự án được xây dựng và phân chia theo mô hình 3 lớp nhằm đảm bảo tính bảo trì, linh hoạt và đáp ứng đúng tiêu chuẩn học thuật:
- **Lớp Data Transfer Object (DTO) - `dto.py`**: Định nghĩa các Object Models (thông qua Pydantic) để truyền tải và kiểm soát kiểu dữ liệu giữa các layer (ví dụ: `UserDTO`, `AuthResultDTO`).
- **Lớp Business Logic Layer (BLL) - `bll.py`**: Chứa các quy tắc nghiệp vụ như mã hóa mật khẩu, kiểm tra điều kiện đăng ký, phân quyền, trước khi gọi xuống tầng thao tác dữ liệu.
- **Lớp Data Access Layer (DAL) - `dal.py`**: Tầng giao tiếp trực tiếp với cơ sở dữ liệu SQLite, thực thi các câu lệnh SQL để truy vấn và cập nhật dữ liệu.
- `app/main.py`: Lớp Presentation (Controller) định tuyến các yêu cầu web FastAPI, kết hợp Jinja2 Templates để hiển thị giao diện và chỉ gọi các hàm từ tầng BLL.
- `recommender.py`: Lớp cốt lõi chứa logic gợi ý phim, sử dụng các mô hình Machine Learning `*.pkl`.
- `build_database.py` & `code.ipynb`: Tiện ích tự động tạo DB mẫu và Notebook xử lý ML.

---

## 🚀 Hướng dẫn Cài đặt & Chạy ứng dụng

### 1. Yêu cầu hệ thống
- Python 3.8 trở lên.
- Đảm bảo đã cài đặt các thư viện cần thiết trong môi trường Python của bạn:
  ```bash
  pip install fastapi uvicorn jinja2 python-multipart pandas numpy scikit-learn joblib
  ```

### 2. Chuẩn bị Cơ sở dữ liệu
Chạy script dưới đây để tự động tạo file `app.db` và nạp vào danh sách phim cùng với các tài khoản dùng thử và dữ liệu lịch sử đánh giá mẫu.
```bash
python build_database.py
```
*(Quá trình này có thể mất một vài giây để xử lý hàng ngàn dòng phim và tính toán số liệu).*

### 3. Khởi chạy Ứng dụng Web
Sử dụng `uvicorn` để chạy server FastAPI:
```bash
python -m uvicorn app.main:app --reload
```
Hoặc có thể chạy trực tiếp:
```bash
python app/main.py
```
- Mở trình duyệt và truy cập: **`http://127.0.0.1:8000`**

### 4. Tài khoản Demo
Sau khi chạy `build_database.py`, bạn có thể trải nghiệm ngay mà không cần tạo tài khoản mới bằng các tài khoản sau:
- **Tài khoản có sẵn dữ liệu đánh giá (Khuyên dùng để xem Demo hệ thống gợi ý CF/Hybrid):**
  - Username: `alice` | Password: `alice123`
  - Username: `bob`   | Password: `bob123`
- **Tài khoản quản trị:**
  - Username: `admin` | Password: `admin123`
- **Tài khoản trắng (để thử nghiệm Cold-Start):**
  - Username: `demo`  | Password: `demo123`

---

## 📊 Về Mô hình Máy học

Hệ thống cung cấp kết quả qua việc xử lý các tệp đã lưu trong quá trình huấn luyện:
- `cf_custom_model.pkl`: Các tham số ma trận `P`, `Q` và các vector `bias` của thuật toán Matrix Factorization (Stochastic Gradient Descent).
- `cbf_tfidf_matrix.pkl` / `cbf_vectorizer.pkl`: Ma trận TF-IDF chứa trích xuất đặc trưng văn bản từ thể loại, từ khóa, tag của phim dùng cho tính toán Cosine Similarity.
- `movie_database.pkl`: Dữ liệu phim đã được làm sạch và chuẩn hóa tối ưu nhất phục vụ cho truy vấn trên RAM.

---
**Trân trọng cảm ơn bạn đã quan tâm đến dự án này!**
