# Báo Cáo Cá Nhân — Lab 07: Embedding & Vector Store

**Họ tên:** Nguyễn Mai Thanh Trúc
**Nhóm:** E1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có vector embedding gần như "cùng hướng" trong không gian nhiều chiều — tức là mô hình cho rằng chúng mang cùng ý nghĩa/chủ đề, dù cách diễn đạt (từ ngữ, độ dài câu) có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên cần đóng học phí trước khi bắt đầu học kỳ."
- Câu B: "Học phí phải được thanh toán trước ngày khai giảng."
- Tại sao tương đồng: cùng diễn đạt một quy định (đóng học phí trước khi học kỳ bắt đầu) chỉ khác cách dùng từ ("đóng"/"thanh toán", "bắt đầu học kỳ"/"ngày khai giảng"). Đo thực tế bằng `text-embedding-3-small` + `compute_similarity()`: **0.7141**.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Học bổng được duy trì nếu điểm trung bình đạt yêu cầu."
- Câu B: "Con mèo đang ngủ trên ghế sofa."
- Tại sao khác: hai câu không liên quan gì về chủ đề (học vụ vs. đời sống thường ngày), không chia sẻ khái niệm hay ngữ cảnh nào. Đo thực tế: **0.2414** (gần 0, đúng như kỳ vọng cho hai câu không liên quan).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến **góc/hướng** giữa hai vector, bỏ qua độ lớn (magnitude) của chúng — mà độ lớn của embedding có thể bị ảnh hưởng bởi độ dài văn bản/số token chứ không phản ánh ý nghĩa. Khoảng cách Euclid thì cộng dồn cả sai khác về độ lớn lẫn hướng, nên dễ đánh giá sai hai câu cùng ý nghĩa nhưng độ dài khác nhau là "khác xa nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> `số lượng chunk = ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))`
> `= ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
>
> Đã kiểm chứng lại bằng chính `FixedSizeChunker(chunk_size=500, overlap=50)` trong `src/chunking.py` trên chuỗi 10,000 ký tự thật: kết quả trả về đúng **23 chunks**, khớp công thức.
>
> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks (tăng từ 23 lên 25, đã kiểm chứng bằng code thật). Overlap lớn hơn làm bước nhảy (`chunk_size - overlap`) nhỏ hơn nên cần nhiều chunk hơn để phủ hết văn bản — đổi lại, mỗi câu/ý nằm ở ranh giới giữa hai chunk có nhiều khả năng xuất hiện trọn vẹn ở ít nhất một chunk, giảm rủi ro cắt đứt ngữ cảnh (context) ngay tại điểm nối, dù tốn thêm dung lượng lưu trữ và tính toán do nội dung bị lặp lại nhiều hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"\. |! |\? |\.\n", text)` để tách câu theo đúng 4 dấu phân cách được yêu cầu (dấu câu + khoảng trắng, hoặc dấu chấm + xuống dòng), sau đó `strip()` từng câu và loại câu rỗng. Các câu được nhóm lại theo lô kích thước `max_sentences_per_chunk` (dùng `range(0, len(sentences), step)`), rồi nối lại bằng khoảng trắng. Edge case xử lý: văn bản rỗng trả về `[]` ngay từ đầu; câu cuối cùng sau dấu câu kết thúc văn bản sinh ra chuỗi rỗng khi split — bị lọc bỏ bởi điều kiện `if s.strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy theo kiểu LangChain's `RecursiveCharacterTextSplitter`: thử tách văn bản bằng separator ưu tiên cao nhất (`\n\n`); nếu một phần vẫn dài hơn `chunk_size`, đệ quy tiếp phần đó với danh sách separator còn lại (`\n`, `. `, `" "`, `""`). Sau khi có các mảnh đủ nhỏ, thuật toán gộp tham lam (greedy merge) các mảnh liền kề lại bằng chính separator đã dùng để tách, miễn sao tổng độ dài không vượt `chunk_size`. Base case: `len(current_text) <= chunk_size` → trả `[current_text]` ngay; và khi hết separator để thử (`remaining_separators` rỗng) → fallback cắt cứng theo `chunk_size` ký tự để đảm bảo luôn có tiến triển (progress), tránh đệ quy vô hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuyển thành một "record" (`_make_record`) gồm `id`, `content`, `metadata` và `embedding` (gọi `self._embedding_fn(doc.content)`), rồi append vào danh sách in-memory `self._store` — đây là nguồn dữ liệu chính cho mọi truy vấn; nếu `chromadb` có sẵn, dữ liệu được ghi thêm (dual-write) vào collection Chroma để có thể kiểm tra/khai thác bên ngoài, nhưng không phải là nguồn đọc chính (tránh phụ thuộc vào việc chuẩn hoá kết quả trả về của Chroma cho một tính năng chưa được test). `search` embed câu hỏi rồi tính **dot product** giữa vector câu hỏi và từng vector đã lưu (`_dot`, dùng lại từ `chunking.py`) — vì các embedding đều được chuẩn hoá về độ dài 1 (unit-normalized) nên dot product tương đương cosine similarity, sau đó sắp xếp giảm dần và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** khi tính similarity: `search_with_filter` duyệt `self._store`, giữ lại các record mà mọi cặp `key: value` trong `metadata_filter` khớp với `record["metadata"]`, rồi mới gọi lại `_search_records` (hàm dùng chung với `search`) trên tập con này — cách này đảm bảo `top_k` luôn được tính trong đúng phạm vi đã lọc metadata thay vì lọc sau khi đã có top_k (có thể làm thiếu kết quả liên quan). `delete_document` tìm mọi record có `metadata.get("doc_id") == doc_id` **hoặc** `id == doc_id` (để tương thích cả chunk đã gắn `doc_id` qua `ingest.py` lẫn Document thêm trực tiếp không có metadata), xoá khỏi `self._store` bằng list-comprehension lọc ngược lại, và trả `True`/`False` tuỳ có tìm thấy hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer()` gọi `self.store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối nội dung (`content`) của chúng bằng `"\n\n"` thành một khối `context`. Prompt được dựng theo khuôn RAG chuẩn: hướng dẫn mô hình chỉ trả lời dựa trên `context`, chèn khối context, rồi tới câu hỏi và nhãn `"Answer:"` để mô hình tiếp tục sinh câu trả lời — cuối cùng gọi `self.llm_fn(prompt)` (được tiêm/inject từ bên ngoài qua constructor) để lấy câu trả lời cuối cùng, giữ cho `KnowledgeBaseAgent` độc lập với nhà cung cấp LLM cụ thể.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\vinuni-lab\K3-Day07-Lab7-A3-1-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Đo bằng `OpenAIEmbedder` (`text-embedding-3-small`, cấu hình trong `.env`) + `compute_similarity()` đã tự lập trình ở Phần 3.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần đóng học phí trước khi bắt đầu học kỳ. | Học phí phải được thanh toán trước ngày khai giảng. | cao (paraphrase) | 0.7141 | Đúng |
| 2 | Thư viện mở cửa từ 8 giờ sáng đến 9 giờ tối. | Ký túc xá có giờ giới nghiêm sau 11 giờ đêm. | thấp (khác chủ đề, chỉ chung "mốc giờ") | 0.3859 | Đúng |
| 3 | Sinh viên vi phạm quy chế có thể bị đình chỉ học tập. | Vi phạm nội quy có thể dẫn đến việc bị tạm ngừng học. | cao (paraphrase) | 0.6364 | Đúng |
| 4 | Học bổng được duy trì nếu điểm trung bình đạt yêu cầu. | Con mèo đang ngủ trên ghế sofa. | thấp (không liên quan) | 0.2414 | Đúng |
| 5 | Sinh viên được mượn tối đa 3 cuốn sách trong 2 tuần. | Giảng viên được mượn tối đa 5 cuốn sách trong 6 tháng. | trung bình (cùng chủ đề mượn sách nhưng khác chủ ngữ & số liệu) | 0.8384 | **Sai** |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **Cặp 5**: tôi dự đoán "trung bình" vì hai câu nói về hai đối tượng khác nhau (sinh viên/giảng viên) với số liệu khác nhau (3 cuốn/2 tuần vs 5 cuốn/6 tháng), nhưng điểm thực tế (0.8384) lại **cao hơn cả hai cặp paraphrase thực sự** (Cặp 1, 3). Điều này cho thấy embedding câu dựa nhiều vào **cấu trúc cú pháp và trường từ vựng chung** ("được mượn tối đa ... cuốn sách trong ...") hơn là khác biệt ngữ nghĩa cụ thể ở chủ ngữ/con số — mô hình nắm bắt "đây là quy định mượn sách thư viện" tốt hơn là phân biệt "áp dụng cho ai, với hạn mức bao nhiêu". Đây cũng là lý do vì sao câu hỏi truy vấn (retrieval) nêu số liệu cụ thể (ví dụ "50%", "2 tuần") có thể bị nhầm với các đoạn có cùng khuôn mẫu nhưng số liệu khác — quan sát này khớp với thất bại thực tế ở Câu hỏi 4/5 trong Phần 5 bên dưới.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Cấu hình dùng để chạy:** `RecursiveChunker(chunk_size=500)` + `OpenAIEmbedder` (`text-embedding-3-small`, key thật lấy từ `.env`, `EMBEDDING_PROVIDER=openai`) qua `build_knowledge_base()` trên toàn bộ `data/k3_university/` (8 tài liệu → 180 chunks). `llm_fn` truyền cho `KnowledgeBaseAgent` là một hàm trích xuất đơn giản (trả về đoạn context đầu tiên) chứ **không** gọi API sinh văn bản (chat completion) — chỉ dùng OpenAI cho embedding như đã thống nhất, nên cột "Câu trả lời của Agent" dưới đây là trích dẫn (extractive), không phải văn bản do LLM tổng hợp.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên được công nhận tối đa bao nhiêu % tổng tín chỉ chương trình khi credit transfer? | `k3-credit-transfer-requests`: "...should not be more than 50% of the total credits for the entire program..." | 0.5940 | **Có** (đúng ở top-1) | Trích đúng câu "không quá 50%..." — đúng ý |
| 2 | Sinh viên đại học được mượn tối đa bao nhiêu sách, trong bao lâu? | `k3-tuition-and-fees`: đoạn về phí phạt trả sách trễ (overdue fines) — **không phải** bảng hạn mức mượn | 0.4752 | Top-1: **Không**; chunk đúng (`k3-library-services`, bảng "Undergraduate Students \| 3 \| 2 weeks \| 1 time") chỉ ở hạng #2, score 0.4439 | Trích nhầm đoạn phí phạt — không trả lời được số sách/thời hạn |
| 3 | Học bổng toàn phần bị hạ bậc tự động nếu GPA năm học trong khoảng nào? | `k3-scholarship-maintenance`: "...Automatic downgrade of 1 level if the Academic Year GPA is between 0.0–2.49..." | 0.5520 | **Có** (đúng ở top-1) | Trích đúng khoảng GPA 0.0–2.49 — đúng ý |
| 4 | Rút học trong vòng 2 tuần đầu học kỳ thì học phí hoàn lại bao nhiêu %? | `k3-tuition-and-fees`: đoạn về phí xác nhận học bổng/giữ chỗ (Confirmation/Retention Fee) — **không phải** chính sách hoàn học phí | 0.4544 | **Không** — cả top-3 đều không chứa con số hoàn lại (50%); đoạn "Tuition Refund" đúng chủ đề chỉ lọt vào hạng #3 nhưng bị chunk cắt ngay trước khi tới số liệu ("...Partial refun[d]") | Trích sai đoạn — không có số % hoàn học phí |
| 5 | Theo quy chế sinh viên, hình thức kỷ luật cao nhất là gì? (`metadata_filter={"audience": "student"}`) | `k3-tuition-and-fees`: "Violations of financial policy may result in discipline from reprimand up to dismissal..." | 0.4419 | **Không** — kể cả sau khi lọc `audience=student`, top-3 vẫn không có đoạn nêu đúng bảng 4 mức kỷ luật (Tier 1-4) của `k3-student-code-of-conduct` | Trích sai đoạn (kỷ luật tài chính, không phải Tier 4 – Dismissal/Expulsion) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 (Câu 1, 2, 3 có chunk liên quan trong top-3; Câu 4, 5 không truy xuất được chunk liên quan dù đã thử áp metadata filter ở Câu 5).

> **Phân tích lỗi (2 trường hợp thất bại):** Câu 4 và Câu 5 đều thất bại vì lý do khác nhau. Câu 4: `RecursiveChunker(chunk_size=500)` cắt đúng ngay trước con số quan trọng (chunk hạng #3 kết thúc ở "...Partial refun" — bị cắt cụt do gộp tham lam theo `chunk_size` mà không biết trước nội dung phía sau là số liệu cốt lõi). Câu 5: `metadata_filter={"audience": "student"}` giúp loại các tài liệu `audience: all` (thư viện, ký túc xá) khỏi kết quả, nhưng **không** giải quyết được vấn đề gốc — bảng 4 mức kỷ luật (Tier 1-4) trong `k3-student-code-of-conduct` có vẻ bị chunk tách khỏi các từ khoá "kỷ luật/vi phạm" ở phần khác của tài liệu, nên vector của nó không đủ gần với câu hỏi; đồng thời câu hỏi lại tình cờ khớp ngữ nghĩa với đoạn nói về "discipline" trong chính sách tài chính (`k3-tuition-and-fees`) — đúng như quan sát ở Cặp 5, Phần 4: embedding dễ bị nhầm bởi từ khoá/cấu trúc câu chung dù chủ đề khác nhau.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Phần demo của nhóm chưa diễn ra tại thời điểm nộp báo cáo này — mục này sẽ được cập nhật sau buổi trình bày, không tự suy diễn kết quả của thành viên khác khi chưa thực sự chạy chung.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 5 / 10 |
| **Tổng phần cá nhân** | **55 / 60** |

> Ghi chú cho mục "Kết quả truy xuất": chấm theo đúng thang 2 điểm/câu ở `docs/SCORING.md` — Câu 1 (2đ, đúng top-1) + Câu 2 (1đ, liên quan nhưng không ở top-1) + Câu 3 (2đ, đúng top-1) + Câu 4 (0đ, không truy xuất được) + Câu 5 (0đ, không truy xuất được dù đã lọc metadata) = 5/10. Tự chấm thấp ở mục này vì ưu tiên phản ánh đúng chất lượng truy xuất thật, thay vì làm đẹp số liệu.
