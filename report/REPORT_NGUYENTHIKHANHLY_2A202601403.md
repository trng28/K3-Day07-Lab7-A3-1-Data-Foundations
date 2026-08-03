# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Khánh Ly
**Nhóm:** E1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, do đó hai đoạn văn bản có ý nghĩa tương tự nhau. Giá trị cosine càng gần 1 thì sự tương đồng giữa hai văn bản càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: Paracetamol có thể giúp giảm sốt.
- Câu B: Paracetamol là thuốc dùng để hạ sốt.
- Tại sao tương đồng: Hai câu nói cùng một ý, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Paracetamol có thể giúp giảm sốt.
- Câu B: Hôm nay trời mưa lớn ở Hà Nội.
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, nên phù hợp hơn để đo “nghĩa” của văn bản trong không gian embedding. Euclidean distance lại nhạy hơn với độ lớn vector, nên dễ bị ảnh hưởng bởi độ dài câu.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: bước dịch giữa các chunk là `chunk_size - overlap = 500 - 50 = 450` ký tự.
>
> Số chunk là: `ceil((10000 - 500) / 450) + 1 = 22 + 1 = 23`.
>
> **Đáp án:** 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước dịch giảm xuống còn 400 ký tự, nên số lượng chunk sẽ tăng lên. 
> Muốn overlap nhiều hơn để giữ ngữ cảnh giữa các chunk và giảm nguy cơ cắt mất ý nghĩa ở ranh giới chunk, nhưng đồng thời sẽ làm tăng số lượng chunk và chi phí lưu trữ/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tiếp cận theo kiểu tách văn bản bằng regex theo dấu kết thúc câu như `. `, `! `, `? `, hoặc `.
`. Sau khi tách xong, tôi dùng `strip()` để bỏ khoảng trắng thừa và gom theo số câu tối đa trong từng chunk. Với edge case như văn bản rỗng hoặc có khoảng trắng thừa, hàm vẫn trả về danh sách sạch và không làm vỡ luồng xử lý.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy ưu tiên tách theo các separator theo thứ tự `\n\n`, `\n`, `. `, ` `, rồi mới xuống fallback cắt theo ký tự khi không còn separator. Base case là khi văn bản đã ngắn hơn hoặc bằng `chunk_size`, lúc đó hàm trả về chính đoạn đó. Nếu một phần còn dài hơn ngưỡng, nó sẽ tiếp tục đệ quy cho đến khi đủ nhỏ rồi ghép trở lại theo nguyên tắc “đủ nhỏ nhưng vẫn giữ ngữ cảnh”.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi tài liệu được chuyển thành `Document`, sau đó nhúng nội dung bằng hàm embedding và lưu vào bộ nhớ in-memory dưới dạng record chứa `id`, `content`, `metadata` và `embedding`. Hàm `search` sẽ nhúng câu truy vấn rồi tính độ tương đồng giữa query vector và các vector lưu trữ, sau đó sắp xếp giảm dần theo điểm similarity và trả về top_k chunk phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc metadata trước khi tính toán similarity, nhằm loại bỏ các candidate không phù hợp và giảm nhiễu. `delete_document` xóa các record có `id` hoặc `metadata['doc_id']` trùng với document cần xóa khỏi kho lưu trữ, và trả về `True` nếu xóa thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` trước tiên gọi `search()` để lấy `top_k` chunk có độ liên quan cao nhất. Sau đó nó nối nội dung các chunk thành một khối ngữ cảnh và inject vào prompt theo định dạng “Chỉ trả lời dựa trên context dưới đây…”. Prompt này sẽ được gửi cho `llm_fn` để sinh câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform win32 -- Python 3.13.3, pytest-9.1.1, pluggy-1.6.0
collected 42 items

... 42 passed in 0.10s
============================= 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Paracetamol có thể giúp giảm sốt. | Paracetamol là thuốc dùng để hạ sốt. | cao | 0.9444 | Đúng |
| 2 | Paracetamol có thể giúp giảm sốt. | Hôm nay trời có mưa lớn ở Hà Nội. | thấp | 0.0711 | Đúng |
| 3 | Sinh viên có thể gia hạn tài liệu thư viện trực tuyến qua cổng thông tin. | Quy định cho phép bạn tự gia hạn sách của thư viện trên mạng. | cao | 0.7264 | Đúng |
| 4 | Quy định về thời hạn đóng học phí của học kỳ 1. | Sinh viên đăng ký lớp học phần trước thời hạn công bố. | thấp | 0.6616 | Sai |
| 5 | Thư viện mở cửa từ 8 giờ sáng đến 10 giờ tối hàng ngày. | Món ăn yêu thích ở căng tin trường là bún chả. | thấp | 0.0161 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là **Cặp 4**: hai câu nằm trong hai chủ đề khác nhau nhưng lại có điểm similarity khá cao (0.6616) khi chạy trên `LocalEmbedder`. Điều này cho thấy embedding theo mô hình đa ngữ có xu hướng nắm bắt các mẫu ngôn ngữ chung và “khung câu” hơn là phân biệt đúng chủ đề ở mức rất nhạy. Vì vậy, với truy xuất thông tin, các câu hỏi có cùng khuôn mẫu hoặc cùng nhịp văn bản có thể dễ bị nhầm với nhau dù nội dung thực tế khác biệt.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> Ghi chú: các kết quả dưới đây được lấy trực tiếp từ lệnh benchmark sau khi đã kích hoạt backend `local` embedder bằng biến môi trường `EMBEDDING_PROVIDER=local` trong repo hiện tại. Đây là dữ liệu thực thi có kiểm chứng, không phải suy đoán.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên được công nhận tối đa bao nhiêu phần trăm tổng số tín chỉ của chương trình khi xin chuyển đổi tín chỉ? | `k3-credit-transfer-requests` — chứa câu “The total number of credit transfers should not be more than 50% of the total credits for the entire program…” | 0.5977 | Có | Trả lời đúng: không quá 50% tổng số tín chỉ chương trình. |
| 2 | Sinh viên đại học được mượn tối đa bao nhiêu cuốn sách và trong bao lâu tại thư viện? | `k3-library-services` — top-1 hiện đoạn về “Guests / Interns / Alumni” không phải quy định mượn sách chính thức của sinh viên. | 0.6135 | Không | Không trả lời đúng về giới hạn mượn 3 cuốn / 2 tuần / gia hạn 1 lần. |
| 3 | Học bổng toàn phần bị tự động hạ bậc nếu GPA năm học nằm trong khoảng nào? | `k3-scholarship-maintenance` — chứa rõ mệnh đề “Automatic downgrade of 1 level if the Academic Year GPA is between 0.0–2.49.” | 0.7748 | Có | Trả lời đúng khoảng GPA 0.0–2.49. |
| 4 | Nếu sinh viên rút học trong vòng 2 tuần kể từ ngày bắt đầu học kỳ, học phí được hoàn lại bao nhiêu phần trăm? | `k3-academic-regulations` — top-1 là đoạn rút học/withdrawal, không phải nội dung refund học phí. | 0.6550 | Có (ở top-3) | Câu trả lời đạt được thông tin đúng ở top-3 về “Tuition Refund” 50% nếu rút học trong 2 tuần. |
| 5 | Theo quy chế sinh viên, hình thức kỷ luật cao nhất mà sinh viên có thể phải nhận là gì? | `k3-student-code-of-conduct` — top-1 trả về phần “Disciplinable Conduct / Forms of Disciplinary Actions.” | 0.6904 | Có | Trả lời đúng: kỷ luật cao nhất là Tier 4 – Dismissal/Expulsion. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua thực nghiệm, tôi thấy chunking theo ranh giới mục/heading và việc gắn metadata phù hợp giúp retrieval ổn định hơn. Một số câu hỏi thất bại vì chunk bị cắt ở vị trí không giữ đủ ngữ cảnh, nên dù embedding tốt thì nếu chunk không mạch lạc vẫn khó trả lời đúng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 |
| **Tổng phần cá nhân** | **56 / 60** |
