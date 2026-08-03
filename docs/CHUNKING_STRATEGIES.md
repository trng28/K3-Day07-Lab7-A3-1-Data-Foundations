# Các chiến lược Chunking

Ba chiến lược khác nhau ở cách chia một tài liệu dài thành các đoạn nhỏ trước khi tạo embedding.

## 1. Recursive

Recursive thử tách văn bản theo thứ tự ưu tiên:

```text
Đoạn văn → dòng → câu → từ → ký tự
```

Ví dụ:

```text
## Học bổng

Sinh viên phải duy trì GPA từ 3.2 trở lên.

Nếu GPA thấp hơn 3.2, học bổng có thể bị hạ bậc.
```

Hệ thống ưu tiên giữ nguyên đoạn văn. Chỉ khi đoạn dài hơn 500 ký tự, nó mới tiếp tục tách theo dòng, câu hoặc từ.

### Ưu điểm

- Giữ cấu trúc tài liệu tương đối tốt.
- Ít cắt ngang câu.
- Phù hợp với Markdown và văn bản policy.
- Cân bằng giữa chất lượng retrieval và số lượng chunk.

### Hạn chế

- Không có overlap trong implementation hiện tại.
- Điều kiện và kết luận ở hai đoạn khác nhau có thể bị tách rời.
- Bảng dài có thể bị chia thành nhiều chunk.

Đây là lựa chọn mặc định và phù hợp nhất với corpus hiện tại.

## 2. Fixed-size + overlap

Văn bản được chia theo đúng số ký tự:

```text
Chunk size: 500 ký tự
Overlap: 50 ký tự
```

Ví dụ:

```text
Chunk 1: ký tự 0 → 499
Chunk 2: ký tự 450 → 949
Chunk 3: ký tự 900 → 1399
```

Phần cuối 50 ký tự của chunk trước được lặp lại ở đầu chunk tiếp theo.

### Ưu điểm

- Đơn giản và ổn định.
- Không làm mất thông tin ngay tại ranh giới chunk.
- Overlap giúp giữ liên kết giữa điều kiện và kết luận.
- Kích thước các chunk khá đồng đều.

### Hạn chế

- Có thể cắt giữa câu, từ hoặc dòng bảng.
- Nội dung bị lặp làm tăng số lượng embedding.
- Có thể xuất hiện nhiều kết quả gần giống nhau.
- Không hiểu cấu trúc heading, đoạn hay bảng Markdown.

Phù hợp để làm baseline hoặc so sánh trong thí nghiệm.

## 3. Sentence

Văn bản được tách thành câu, sau đó gom tối đa ba câu vào một chunk:

```text
Chunk 1: câu 1–3
Chunk 2: câu 4–6
Chunk 3: câu 7–9
```

### Ưu điểm

- Ít cắt ngang ý.
- Chunk có nội dung ngắn và tập trung.
- Tốt với câu hỏi yêu cầu một điều kiện hoặc con số cụ thể.
- Có thể ranking chính xác hơn cho các quy định ngắn.

### Hạn chế

- Không có overlap.
- Bộ nhận diện câu hiện còn đơn giản.
- Không xử lý tốt bảng Markdown và danh sách.
- Điều kiện ở câu trước có thể bị tách khỏi kết luận ở chunk sau.
- Tạo ra nhiều chunk có kích thước không đồng đều.

Phù hợp với tài liệu chủ yếu là văn xuôi, ít bảng.

## So sánh

| Chiến lược | Giữ cấu trúc | Không cắt câu | Giữ ngữ cảnh biên | Xử lý bảng | Số chunk |
|---|---:|---:|---:|---:|---:|
| Recursive | Tốt | Khá tốt | Trung bình | Khá | Trung bình |
| Fixed + overlap | Thấp | Thấp | Tốt | Thấp | Nhiều |
| Sentence | Trung bình | Tốt | Thấp | Thấp | Nhiều |

## Khuyến nghị

- Dùng `Recursive` cho vận hành chính.
- Dùng `Fixed + overlap` làm baseline đánh giá.
- Dùng `Sentence` để thử nghiệm với câu hỏi tìm điều kiện, thời hạn hoặc con số ngắn.
