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

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trúc | RecursiveChunker (500) | 5/10 (2đ+1đ+2đ+0đ+0đ theo thang `docs/SCORING.md`) | Tôn trọng ranh giới đoạn/heading/bảng tốt hơn 2 chiến lược còn lại | Vẫn có thể cắt ngay trước số liệu quan trọng khi một đoạn dài hơn `chunk_size`; không "biết" đâu là thông tin cốt lõi cần giữ nguyên vẹn |
| *(chờ thành viên 2)* | | | | |
| *(chờ thành viên 3)* | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Chưa đủ dữ liệu để kết luận — mới có kết quả của 1/[số thành viên] thành viên. Sẽ hoàn thiện sau khi cả nhóm chạy xong cùng 5 câu hỏi ở Phần 3 để so sánh công bằng trên cùng bộ câu hỏi.*

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
> *Bảng dưới đây mới có kết quả của Trúc (`RecursiveChunker`, chunk_size=500, OpenAI `text-embedding-3-small`) — cần bổ sung cột/kết quả của các thành viên khác để so sánh chéo chiến lược.*

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Credit transfer tối đa bao nhiêu % | RecursiveChunker (Trúc) — 2đ | Có (top-1, score 0.594) | Đúng ngay top-1, không cần so sánh thêm ở đây |
| 2 | Mượn sách thư viện | RecursiveChunker (Trúc) — 1đ | Có, nhưng ở top-2 (score 0.444), top-1 lại là đoạn phí phạt sai chủ đề | Cần thử `metadata_filter={"category":"library-services"}` hoặc chunk nhỏ hơn để kiểm tra có cải thiện không |
| 3 | Học bổng toàn phần hạ bậc khi GPA nào | RecursiveChunker (Trúc) — 2đ | Có (top-1, score 0.552) | Đúng ngay top-1 |
| 4 | Hoàn học phí rút học trong 2 tuần | *(chưa có chiến lược nào thành công)* — 0đ | Không | **Ca lỗi:** chunk hạng #3 đúng chủ đề ("Tuition Refund") nhưng bị cắt ngay trước con số 50% — gợi ý cần chunk theo heading/mục (`##`) thay vì theo `chunk_size` cứng cho phần bảng phí, hoặc tăng `chunk_size` |
| 5 | Kỷ luật cao nhất theo quy chế sinh viên | *(chưa có chiến lược nào thành công)* — 0đ | Không (dù đã lọc `audience=student`) | **Ca lỗi:** metadata filter loại đúng tài liệu sai đối tượng nhưng không sửa được việc bảng Tier 1-4 bị tách khỏi ngữ cảnh "kỷ luật/vi phạm" trong chunk của nó — nên thử chunking theo heading để giữ trọn bảng cùng đoạn giới thiệu |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có giúp ích một phần ở **Câu 5** — `metadata_filter={"audience": "student"}` loại bỏ đúng các tài liệu `audience: all` (thư viện, ký túc xá) khỏi danh sách ứng viên, giảm nhiễu từ các tài liệu không liên quan đến đối tượng câu hỏi. Tuy nhiên với chiến lược `RecursiveChunker` của Trúc, việc lọc **không đủ** để câu 5 trả lời đúng, vì vấn đề gốc nằm ở chunk boundary (bảng Tier 1-4 bị tách khỏi từ khoá ngữ cảnh) chứ không phải do lẫn tài liệu sai đối tượng — cho thấy metadata filtering và chất lượng chunking là hai đòn bẩy độc lập, cần cả hai mới đủ.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
