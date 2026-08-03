# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** E1
**Thành viên:** 

Tên | ID
---|---
Nguyễn Mai Thanh Trúc | 2A202601473
Nguyễn Thị Khánh Ly | 2A202601403
Nguyễn Thị Tuyết Mai | 2A202601693

**Ngày:** 03-08-2026
**Phòng:** D303

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:** Quy định học vụ & dịch vụ sinh viên tại VinUniversity — đăng ký/chuyển đổi tín chỉ, thư viện, học bổng & hỗ trợ tài chính, học phí, quy chế/kỷ luật sinh viên và đời sống ký túc xá — lấy từ cổng chính sách công khai `policy.vinuni.edu.vn`.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Procedural Guidelines for Credit Transfer Requests | policy.vinuni.edu.vn/all-policies/credit-transfer-requests/ | 2026-07-30 / VUNI.13-V2.0 | 4,281 | doc_id, audience=student, department=office-of-university-registrar, category=course-registration, language=vi→en |
| 2 | Library Access & Services Policy | policy.vinuni.edu.vn/all-policies/library-policies-for-users/ | 2026-07-30 / POL-LLR-001-V4.0 | 6,492 | doc_id, audience=all, department=library, category=library-services, language=en |
| 3 | Guidelines for Maintaining Entry Scholarship and Financial Aid Support | policy.vinuni.edu.vn/all-policies/criteria-to-maintain-the-entry-scholarship-and-financial-aid-support/ | 2026-07-30 / GDL-SAM-004-V2.1 | 3,227 | doc_id, audience=student, department=student-affairs-management, category=scholarship, language=en |
| 4 | Guidelines for Student Financial Aid Support Request | policy.vinuni.edu.vn/all-policies/guidelines-for-student-financial-support-request/ | 2026-07-30 / GDL-FAO-001-V2.0 | 4,909 | doc_id, audience=student, department=financial-aid-office, category=financial-aid, language=en |
| 5 | Financial Regulations and Tariff (for student) | policy.vinuni.edu.vn/all-policies/financial-regulations-and-tariff-for-student-2/ | 2026-07-30 / VUNI_TS03_Student | 13,832 | doc_id, audience=student, department=finance-and-accounting, category=tuition-fees, language=en |
| 6 | Student Code of Conduct | policy.vinuni.edu.vn/all-policies/student-affairs-regulations-code-of-conduct/ | 2026-07-30 / VU_CTSV02.EN-V5.0 | 7,939 | doc_id, audience=student, department=student-affairs-management, category=student-conduct, language=en |
| 7 | Residential Life Guideline | policy.vinuni.edu.vn/all-policies/residential-life-guideline/ | 2026-07-30 / GDL-SAM-008-V5.0 | 6,981 | doc_id, audience=all, department=student-affairs-management, category=dormitory, language=en |
| 8 | Academic Regulations for Full-Time Undergraduate Programs | policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/ | 2026-07-30 / VU_HT03-V8.1 | 20,655 | doc_id, audience=student, department=academic-affairs, category=academic-regulations, language=en |

Chi tiết đầy đủ (kèm `license_or_permission`) xem `data/k3_university/sources.csv`. Toàn bộ 8 tài liệu đều được đánh dấu `security_classification: Public` (hoặc công khai trên cổng chính sách) tại nguồn — không dùng tài liệu `Internal`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | enum (`student`\|`faculty`\|`staff`\|`all`) | `student` | Lọc trước bằng `search_with_filter(metadata_filter={"audience": "student"})` để loại tài liệu không dành cho sinh viên trước khi tính similarity — bắt buộc theo `K3_VARIANT.md`. |
| `category` | string | `tuition-fees`, `dormitory`, `course-registration` | Cho phép thu hẹp phạm vi tìm kiếm theo chủ đề dịch vụ cụ thể khi câu hỏi đã nêu rõ mảng nào (học phí, ký túc xá...), tránh nhiễu từ tài liệu khác chủ đề. |
| `department` | string | `library`, `financial-aid-office` | Giúp truy vết đơn vị ban hành/chịu trách nhiệm — hữu ích khi câu hỏi hỏi "liên hệ ai" hoặc cần phân biệt hai tài liệu cùng nói về tiền nhưng khác phòng ban (Finance vs Financial Aid Office). |
| `document_version` + `retrieved_at` | string / date | `POL-LLR-001-V4.0`, `2026-07-30` | Cho phép kiểm tra độ mới của quy định khi trả lời (agent có thể trích dẫn phiên bản) và phát hiện khi cần crawl lại nếu quy định đã đổi phiên bản. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(chunk_size=500)` trên 2 tài liệu dài, có cấu trúc heading/mục rõ ràng (dùng nội dung sau khi bỏ YAML front matter):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| academic-regulations.md (20,656 ký tự) | FixedSizeChunker (`fixed_size`) | 42 | 491.8 | Không — cắt cứng theo ký tự, thường xuyên cắt giữa câu/giữa bảng, không quan tâm ranh giới `Article`/`Chapter`. |
| academic-regulations.md | SentenceChunker (`by_sentences`) | 52 | 392.6 | Giữ trọn câu, nhưng không biết ranh giới Article/heading — có thể gộp câu cuối Article này với câu đầu Article sau. |
| academic-regulations.md | RecursiveChunker (`recursive`) | 53 | 387.9 | Tốt nhất trong 3: ưu tiên tách theo `\n\n` (đoạn văn/heading) trước, nên phần lớn chunk trùng khớp với ranh giới mục/Article tự nhiên của văn bản. |
| tuition-and-fees.md (13,833 ký tự) | FixedSizeChunker (`fixed_size`) | 28 | 494.0 | Không — nhiều bảng số liệu (học phí, phí thư viện...) bị cắt giữa dòng bảng. |
| tuition-and-fees.md | SentenceChunker (`by_sentences`) | 27 | 507.9 | Kém với bảng Markdown — một "câu" theo regex có thể là cả một hàng bảng dài, phá vỡ cấu trúc bảng. |
| tuition-and-fees.md | RecursiveChunker (`recursive`) | 37 | 372.4 | Tốt hơn nhưng vẫn có rủi ro cắt ngay trước số liệu quan trọng khi một đoạn dài hơn `chunk_size` (xem phân tích lỗi Câu 4, Phần 3 bên dưới). |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Mai Thanh Trúc**
- **Loại chiến lược:** RecursiveChunker (built-in, `chunk_size=500`)
- **Mô tả & lý do chọn cho chủ đề này:** Corpus gồm nhiều văn bản quy chế dài, có cấu trúc phân cấp rõ (Chapter/Article, heading Markdown `##`/`###`, bảng số liệu). `RecursiveChunker` thử tách theo `\n\n` trước (ranh giới đoạn/heading) rồi mới rơi xuống `\n`, `. `, `" "` — nên tôn trọng cấu trúc tài liệu tốt hơn hẳn so với cắt cứng theo ký tự (`FixedSizeChunker`) hoặc theo câu bất kể ngữ cảnh (`SentenceChunker`), đặc biệt với các bảng Markdown (phí, học bổng) mà `SentenceChunker` dễ phá vỡ do coi cả hàng bảng dài là "một câu".
- **Kết quả thực nghiệm (OpenAI `text-embedding-3-small`, 8 tài liệu → 180 chunk):** 3/5 câu hỏi benchmark có chunk liên quan trong top-3 (2/5 đúng ngay top-1). 2 ca thất bại đều do ranh giới chunk cắt ngay trước số liệu cốt lõi hoặc do bảng quan trọng bị tách rời khỏi từ khoá ngữ cảnh xung quanh — xem chi tiết ở `REPORT_NGUYENMAITHANHTRUC_2A202601473.md`, Phần 5.

**Thành viên 2 — Nguyễn Thị Khánh Ly**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=500`) + LocalEmbedder (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
- **Mô tả & lý do chọn:** Giữ cùng cách tách đệ quy theo ranh giới đoạn/heading như cấu hình chuẩn của nhóm, nhưng dùng embedding đa ngữ chạy cục bộ để đo ảnh hưởng của mô hình embedding và tạo một cấu hình không phụ thuộc API. Cách này ưu tiên `\n\n`, `\n`, dấu kết thúc câu rồi mới cắt theo ký tự, nên phù hợp với quy chế có cấu trúc; điểm yếu vẫn là bảng Markdown hoặc đoạn dài có thể bị chia khỏi tiêu đề.
- **Kết quả thực nghiệm:** 4/5 câu có chunk liên quan trong top-3; chấm 7/10. Câu 1 và 3 đúng ở top-1, Câu 4 tìm được chính sách hoàn 50% trong top-3, Câu 5 trả về đúng phần kỷ luật `Tier 4 – Dismissal/Expulsion`; Câu 2 nhầm nhóm đối tượng mượn sách.

**Thành viên 3 — Nguyễn Thị Tuyết Mai**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`) + LocalEmbedder (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
- **Mô tả & lý do chọn:** Gom tối đa 3 câu giúp giữ câu hoàn chỉnh và tạo các chunk có đơn vị ngữ nghĩa tự nhiên hơn cắt cứng theo ký tự. Cách này phù hợp với phần văn xuôi của quy chế, nhưng kém hiệu quả với bảng Markdown và các mục dài không có dấu kết thúc câu rõ ràng.
- **Kết quả thực nghiệm (8 tài liệu → 160 chunk):** 3/5 câu có chunk liên quan trong top-3; chấm 5/10. Câu 1 và 3 đúng ở top-1; Câu 5 có chunk đúng ở hạng 2–3 nhưng top-1 bị nhiễu từ tài liệu học bổng; Câu 2 và 4 thất bại.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trúc | RecursiveChunker (500) | 5/10 (2đ+1đ+2đ+0đ+0đ theo thang `docs/SCORING.md`) | Tôn trọng ranh giới đoạn/heading/bảng tốt hơn 2 chiến lược còn lại | Vẫn có thể cắt ngay trước số liệu quan trọng khi một đoạn dài hơn `chunk_size`; không "biết" đâu là thông tin cốt lõi cần giữ nguyên vẹn |
| Ly | RecursiveChunker (500) + LocalEmbedder | 7/10 (2đ+0đ+2đ+1đ+2đ) | Kết quả tổng thể cao nhất; mô hình đa ngữ cục bộ tìm được câu hoàn học phí và mức kỷ luật trong top-3 | Vẫn bị ảnh hưởng bởi bảng/ranh giới chunk; Câu 2 nhầm nhóm đối tượng dù cùng tài liệu thư viện |
| Mai | SentenceChunker (3 câu/chunk) + LocalEmbedder | 5/10 (2đ+0đ+2đ+0đ+1đ) | Giữ câu nguyên vẹn; số chunk thấp nhất (160), truy xuất ổn định với các câu quy định dạng văn xuôi | Không bảo toàn tốt bảng Markdown; dễ gộp các câu khác mục và bỏ lỡ số liệu trong bảng |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Trên bộ 5 câu hỏi chung, **cấu hình RecursiveChunker + LocalEmbedder của Ly đạt điểm cao nhất (7/10)**, nhờ tìm được thông tin hoàn học phí trong top-3 và mức kỷ luật ở top-1. So với cùng RecursiveChunker dùng OpenAI Embedder của Trúc (5/10), kết quả cũng cho thấy mô hình embedding có thể làm thay đổi thứ hạng đáng kể; còn SentenceChunker của Mai (5/10) giữ câu tốt nhưng yếu với bảng. Vì vậy, “chiến lược” tốt nhất phải xét cả chunker, embedder và metadata filter thay vì chỉ một thành phần.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.
>
> *Bộ câu hỏi dưới đây do Trúc đề xuất (phủ 5/8 tài liệu, đa dạng loại quy định: đăng ký/chuyển tín chỉ, thư viện, học bổng, học phí, kỷ luật) — nhóm rà soát và có thể chỉnh sửa trước khi chốt để mọi thành viên chạy chung.*

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên được công nhận tối đa bao nhiêu phần trăm tổng số tín chỉ của chương trình khi xin chuyển đổi tín chỉ (credit transfer)? | Không quá 50% tổng số tín chỉ của toàn bộ chương trình (theo Article 13 Quy chế học vụ). | `credit-transfer-requests.md` mục 3.2 |
| 2 | Sinh viên đại học (undergraduate) được mượn tối đa bao nhiêu cuốn sách và trong bao lâu tại thư viện? | 3 cuốn, thời hạn 2 tuần, được gia hạn 1 lần. | `library-services.md` bảng "Circulation Privileges" (mục 2.2) |
| 3 | Học bổng toàn phần (Full scholarship) bị tự động hạ bậc nếu GPA năm học nằm trong khoảng nào? | GPA năm học từ 0.0 đến 2.49 (dưới mức học lực Tốt). | `scholarship-maintenance.md` bảng mục 3, hàng 1 |
| 4 | Nếu sinh viên rút học trong vòng 2 tuần kể từ ngày bắt đầu học kỳ, học phí đã đóng được hoàn lại bao nhiêu phần trăm? | Hoàn lại 50% học phí thực đóng cho học kỳ/khóa học ngắn hạn đó. | `tuition-and-fees.md` mục D.4 "Tuition Refund" |
| 5 | Theo quy chế sinh viên, hình thức kỷ luật cao nhất mà sinh viên có thể phải nhận là gì? (**cần `metadata_filter={"audience": "student"}`** để loại tài liệu `audience: all` như thư viện/ký túc xá) | Tier 4 – Dismissal/Expulsion (buộc thôi học/đuổi học). | `student-code-of-conduct.md` mục 3.1, bảng 4 mức kỷ luật (Tier 1-4) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).
>
> Bảng dưới đây tổng hợp kết quả tốt nhất của cả ba thành viên trên cùng 5 câu hỏi. Do Ly và Mai dùng LocalEmbedder còn Trúc dùng OpenAI Embedder, điểm similarity tuyệt đối chỉ dùng để đọc trong từng cấu hình; việc so sánh chính dựa trên thứ hạng và thang điểm retrieval.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Credit transfer tối đa bao nhiêu % | Cả 3 chiến lược — 2đ | Có (top-1 ở cả 3 cấu hình) | Kết quả ổn định vì câu nguồn chứa trực tiếp cụm “50% of the total credits”. |
| 2 | Mượn sách thư viện | RecursiveChunker + OpenAI Embedder (Trúc) — 1đ | Có ở top-2 (score 0.444) | Cấu hình Local của Ly nhầm nhóm người dùng; SentenceChunker và top-1 của Trúc bị nhiễu bởi phí phạt. Nên lọc `category=library-services` và giữ nguyên hàng bảng. |
| 3 | Học bổng toàn phần hạ bậc khi GPA nào | Cả 3 chiến lược — 2đ | Có (top-1 ở cả 3 cấu hình) | Cụm “Automatic downgrade” và khoảng `0.0–2.49` tạo tín hiệu ngữ nghĩa rõ. |
| 4 | Hoàn học phí rút học trong 2 tuần | RecursiveChunker + LocalEmbedder (Ly) — 1đ | Có ở top-3 | Chỉ cấu hình của Ly truy xuất được thông tin hoàn 50% trong top-3; cấu hình OpenAI của Trúc bị cắt ngay trước con số, SentenceChunker không tìm thấy chính sách hoàn tiền. |
| 5 | Kỷ luật cao nhất theo quy chế sinh viên | RecursiveChunker + LocalEmbedder (Ly) — 2đ | Có ở top-1; SentenceChunker có ở hạng 2–3 | Lọc `audience=student` giảm nhiễu; cấu hình của Ly truy xuất đúng `Tier 4 – Dismissal/Expulsion`, trong khi cấu hình OpenAI của Trúc vẫn bị nhiễu bởi chính sách tài chính. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rõ nhất ở **Câu 5**. `metadata_filter={"audience": "student"}` loại các tài liệu `audience: all` (thư viện, ký túc xá), giúp cấu hình Recursive + LocalEmbedder của Ly đưa đúng phần `Tier 4 – Dismissal/Expulsion` lên top-1 và SentenceChunker của Mai tìm được chunk đúng ở hạng 2–3. Tuy vậy, cấu hình Recursive + OpenAI Embedder của Trúc vẫn thất bại vì bảng Tier 1–4 bị tách khỏi từ khóa ngữ cảnh. Điều này cho thấy metadata filtering giảm không gian tìm kiếm nhưng không thể bù hoàn toàn cho chunk boundary hoặc thứ hạng embedding kém.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- Chunk boundary và mô hình embedding cùng ảnh hưởng trực tiếp đến khả năng tìm số liệu: với câu hỏi hoàn học phí, một cấu hình bỏ lỡ giá trị `50%`, trong khi cấu hình khác đưa được thông tin đúng vào top-3.
- Embedding thường nhận diện chủ đề/cấu trúc câu tốt hơn các chi tiết như đối tượng và con số; vì vậy truy vấn mượn sách dễ nhầm giữa sinh viên, khách và đoạn phí phạt.
- Metadata filter và chunking bổ trợ nhau: lọc `audience=student` giảm nhiễu ở câu kỷ luật, nhưng chỉ chiến lược giữ đúng ngữ cảnh bảng mới đưa được câu trả lời lên thứ hạng cao.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus và bộ câu hỏi, các cấu hình tạo ra thứ hạng rất khác nhau: Recursive + LocalEmbedder đạt 7/10, còn Recursive + OpenAI Embedder và Sentence + LocalEmbedder cùng đạt 5/10. Điều này cho thấy khác biệt không chỉ đến từ chunking: mô hình embedding và metadata filter cũng quyết định chunk nào lọt top-3. Vì vậy cần đánh giá toàn bộ pipeline trên câu hỏi thật thay vì chọn riêng chunker từ trực giác.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ dùng chunker lai theo cấu trúc: tách trước theo heading/Article, giữ nguyên bảng cùng tiêu đề, sau đó mới chia đoạn dài với overlap khoảng 50–100 ký tự. Nhóm cũng sẽ chuẩn hóa metadata theo từng chunk và áp dụng filter `category`, `audience`, `department` khi truy vấn nêu rõ phạm vi; cuối cùng chạy grid search cho kích thước chunk/overlap trên bộ câu hỏi mở rộng trước khi chốt cấu hình.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **39 / 40** |
