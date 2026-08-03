# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Tuyết Mai
**Nhóm:** E1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, cho thấy hai đoạn văn có ý nghĩa hoặc nội dung tương tự nhau. Giá trị cosine càng gần 1 thì mức độ tương đồng càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: Paracetamol có thể giúp giảm sốt
- Câu B: Paracetamol là thuốc dùng để hạ sốt.
- Tại sao tương đồng: Hai câu diễn đạt khác nhau nhưng cùng nói về công dụng của Paracetamol là hạ sốt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Paracetamol có thể giúp giảm sốt. 
- Câu B: Hôm nay trời có mưa lớn ở Hà Nội.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (thuốc và thời tiết), nên embedding của chúng sẽ ít giống nhau và độ tương tự cosine thấp.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity được ưu tiên vì nó đo góc giữa các vector, tập trung vào sự giống nhau về hướng (ý nghĩa của văn bản) và không bị ảnh hưởng nhiều bởi độ dài câu. Trong khi đó, khoảng cách Euclid phụ thuộc vào độ lớn vector, nên các câu dài/ngắn khác nhau có thể làm sai lệch kết quả tìm kiếm.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:* $\text{chunks} = \left\lceil \frac{10000 - 50}{450} \right\rceil$  
> *Đáp án:* 23

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng từ 50 lên 100, bước dịch giữa các chunk giảm từ 450 xuống 400 ký tự, nên số lượng chunk sẽ tăng lên.  
> Muốn overlap nhiều hơn để giữ lại nhiều ngữ cảnh giữa các chunk, giúp giảm việc cắt mất ý nghĩa của câu hoặc đoạn văn ở ranh giới chunk, nhưng sẽ làm tăng số lượng chunk và chi phí lưu trữ/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy (regex) tích hợp lookbehind `(?<=\. |\! |\? |\.\n)` để phân tách các câu dựa trên các ký tự phân tách như `. `, `! `, `? `, hoặc `.\n` mà không làm mất đi dấu câu kết thúc của từng câu. Edge cases được xử lý bằng cách sử dụng `.strip()` để loại bỏ hoàn toàn các phần tử rỗng hoặc khoảng trắng dư thừa, sau đó tiến hành gom cụm tối đa `max_sentences_per_chunk` câu lại với nhau bằng dấu cách `" "` thành một chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thực hiện phân tách đệ quy văn bản dựa trên độ ưu tiên giảm dần của danh sách các ký tự phân tách `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản đầu vào có độ dài nhỏ hơn hoặc bằng `chunk_size` thì sẽ dừng đệ quy và trả về chính nó; nếu danh sách ký tự phân tách đã cạn, nó sẽ tự động rơi vào cơ chế fallback là cắt nhỏ văn bản theo độ dài ký tự (`chunk_size`). Sau khi đệ quy phân tách thành các đoạn nhỏ hơn, thuật toán tiến hành ghép (merge) tuần tự các đoạn liền kề lại với nhau bằng ký tự phân tách hiện tại, miễn là tổng độ dài (bao gồm cả ký tự phân tách) không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Hỗ trợ song song cả cơ sở dữ liệu ChromaDB (nếu có sẵn) và in-memory fallback. Dữ liệu trong in-memory được lưu dưới dạng một danh sách các dictionary chứa thông tin gồm `id`, `content`, `metadata` và vector nhúng `embedding`. Lệnh `search` thực hiện nhúng câu hỏi truy vấn, sau đó tính toán độ tương tự cosine giữa vector truy vấn và toàn bộ các vector lưu trữ thông qua hàm `compute_similarity` rồi sắp xếp kết quả giảm dần theo điểm tương đồng để trả về top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thuật toán thực hiện lọc trước dữ liệu (pre-filtering) trước khi tính toán độ tương tự để tối ưu hóa hiệu năng và kết quả tìm kiếm. Với in-memory store, nó duyệt qua toàn bộ các bản ghi trong kho để tìm kiếm các bản ghi khớp với `metadata_filter` rồi mới tiến hành tìm kiếm tương tự trên tập con đó. Hàm `delete_document` lọc bỏ trực tiếp tất cả các bản ghi có `id` trùng khớp hoặc `metadata['doc_id']` trùng khớp khỏi kho lưu trữ và trả về `True` nếu số lượng bản ghi bị giảm đi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tác tử thực hiện tìm kiếm `top_k` đoạn ngữ cảnh có độ tương đồng cao nhất từ store bằng cách gọi `search()`, sau đó ghép nối nội dung của các chunk này bằng ký tự xuống dòng kép `\n\n`. Đoạn ngữ cảnh này sau đó được truyền (inject) trực tiếp vào một cấu trúc Prompt có sẵn bao gồm các chỉ dẫn ràng buộc rõ ràng (như chỉ được trả lời dựa trên ngữ cảnh và phải nói "không biết" nếu không tìm thấy thông tin) rồi gửi tới hàm `llm_fn` để lấy câu trả lời cuối cùng.


---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
=============== test session starts ================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- D:\AI - vinuni\DAY07_2A202601693_NguyenThiTuyetMai\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\AI - vinuni\DAY07_2A202601693_NguyenThiTuyetMai
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
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]     
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
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
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_sizePASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

================ 42 passed in 0.10s ================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên có thể gia hạn tài liệu thư viện trực tuyến qua cổng thông tin. | Quy định cho phép bạn tự gia hạn sách của thư viện trên mạng. | cao | 0.7264 | Đúng |
| 2 | Quy định về thời hạn đóng học phí của học kỳ 1. | Sinh viên đăng ký lớp học phần trước thời hạn công bố. | thấp / trung bình | 0.5392 | Đúng |
| 3 | Thư viện mở cửa từ 8 giờ sáng đến 10 giờ tối hàng ngày. | Món ăn yêu thích ở căng tin trường là bún chả. | thấp | 0.0161 | Đúng |
| 4 | Sinh viên không được phép sử dụng tài liệu trong phòng thi nếu không có sự đồng ý của giám thị. | Quy chế liêm chính học thuật cấm hành vi gian lận và đạo văn. | trung bình / cao | 0.5449 | Đúng |
| 5 | Làm thế nào để xin nghỉ học tạm thời? | Sinh viên cần nộp đơn xin nghỉ học tạm thời qua cổng dịch vụ một cửa trước tuần thứ 4. | cao | 0.6600 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp số 2 có điểm tương đồng khá cao (0.5392) mặc dù nói về hai việc khác nhau (học phí vs đăng ký học phần). Điều này cho thấy embeddings biểu diễn ý nghĩa bằng cách ánh xạ ngữ cảnh từ vựng chung (từ khóa "thời hạn", "quy định", "sinh viên") hơn là hiểu rõ logic ngữ dụng riêng biệt của từng hành vi cụ thể trong đời thực.


---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Cấu hình dùng để chạy:** `SentenceChunker(max_sentences_per_chunk=3)` + `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`) qua `build_knowledge_base()` trên toàn bộ `data/k3_university/` (8 tài liệu → 160 chunks). `llm_fn` truyền cho `KnowledgeBaseAgent` là hàm trích xuất dòng đầu tiên của context phục vụ mục đích kiểm thử và so sánh (không gọi LLM API ngoài).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên được công nhận tối đa bao nhiêu % tổng tín chỉ chương trình khi credit transfer? | `k3-credit-transfer-requests`: "...The total number of credit transfers should not be more than 50% of the total credits for the entire program..." | 0.7720 | **Có** (đúng ở top-1) | Trích đúng câu quy định không vượt quá 50%. |
| 2 | Sinh viên đại học được mượn tối đa bao nhiêu sách, trong bao lâu? | `k3-tuition-and-fees`: "...Library fee — overdue fines: 10,000 VND/day overdue/document..." | 0.6591 | **Không** (top-3 không chứa thông tin hạn mức mượn, nhầm sang phí phạt trễ hạn) | Trích sai thông tin phí phạt thay vì hạn mức mượn. |
| 3 | Học bổng toàn phần bị hạ bậc tự động nếu GPA năm học trong khoảng nào? | `k3-scholarship-maintenance`: "...Automatic downgrade of 1 level if the Academic Year GPA is between 0.0–2.49..." | 0.7820 | **Có** (đúng ở top-1) | Trích đúng khoảng GPA từ 0.0–2.49 bị hạ bậc. |
| 4 | Rút học trong vòng 2 tuần đầu học kỳ thì học phí hoàn lại bao nhiêu %? | `k3-academic-regulations`: "...undertaking at least 80% of a full-time load..." (quy định tải học tập tối thiểu) | 0.6490 | **Không** (cả top-3 đều không tìm thấy chính sách hoàn tiền 50% ở tuition-and-fees) | Trích sai đoạn về tải học tập. |
| 5 | Theo quy chế sinh viên, hình thức kỷ luật cao nhất là gì? (`metadata_filter={"audience": "student"}`) | `k3-scholarship-maintenance`: "...no major misconduct (Tier 3) or extremely serious misconduct (Tier 4)..." | 0.6593 | **Có** (Top-1 là điều kiện học bổng, nhưng Rank 2 và Rank 3 lấy đúng `k3-student-code-of-conduct` chứa thông tin kỷ luật) | Trích đoạn điều kiện duy trì học bổng (liên quan đến Tier 4). |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 (Câu 1, 3, 5 có chunk liên quan trong top-3; Câu 2 và 4 thất bại do không tìm thấy chunk chính xác).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua thảo luận thiết kế, tôi nhận thấy chiến lược `RecursiveChunker` của bạn Trúc có khả năng phân tách theo các mục tiêu đề tự nhiên (`\n\n`) rất hiệu quả, giúp giữ nguyên ngữ cảnh tốt hơn nhiều so với việc chỉ gom câu cứng nhắc của `SentenceChunker` (vốn dễ bị cắt ranh giới bảng và phân tách sai ngữ cảnh giữa các đoạn). Điều này giúp tôi hiểu rõ tầm quan trọng của việc thiết kế chunker phù hợp với cấu trúc tài liệu.

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

> Ghi chú cho mục "Kết quả truy xuất": Chấm theo đúng hướng dẫn `docs/SCORING.md` — Câu 1 (2đ, đúng top-1 + câu trả lời chính xác) + Câu 2 (0đ, không có chunk liên quan trong top-3) + Câu 3 (2đ, đúng top-1 + câu trả lời chính xác) + Câu 4 (0đ, không có chunk liên quan trong top-3) + Câu 5 (1đ, có chunk liên quan trong top-3 nhưng không ở top-1, câu trả lời chưa đầy đủ) = 5/10. Việc tự chấm thực chất giúp phản ánh trung thực năng lực của SentenceChunker trên dữ liệu thực tế.