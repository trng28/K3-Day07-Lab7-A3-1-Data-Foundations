# Spec — VinUni K3 Policy Assistant (Chatbot Demo)

Tài liệu này mô tả **workflow và phương pháp** của ứng dụng chatbot RAG (`backend/` + `frontend/`)
được xây trên nền tảng bài Lab 7 (`src/`, `ingest.py`, `data/k3_university/`). Đây là phần mở
rộng **ngoài phạm vi chấm điểm của lab** (xem `README.md`, `docs/SCORING.md`) — mục tiêu là biến
kho tri thức đã xây ở Giai đoạn 1-2 thành một trợ lý hỏi-đáp thật, có trích dẫn nguồn, chạy qua
giao diện web.

> Không sửa `src/`, `tests/`, `ingest.py` hay `main.py` cho phần này — toàn bộ logic ứng dụng nằm
> trong `backend/` và `frontend/` để không ảnh hưởng tới bài nộp lab (`pytest tests/ -v`).

---

## 1. Mục tiêu & phạm vi

- Cho phép hỏi-đáp bằng ngôn ngữ tự nhiên (chủ yếu tiếng Việt) về quy định/dịch vụ đại học
  VinUniversity dựa trên corpus công khai đã thu thập ở `data/k3_university/` (8 tài liệu, xem
  `docs/DATA_COLLECTION.md` và `report/REPORT_NHOM.md`).
- Mỗi câu trả lời phải **có căn cứ** (grounded): chỉ dùng nội dung truy xuất được từ corpus, kèm
  trích dẫn số nguồn `[1]`, `[2]`... người dùng bấm vào xem được `source_url` gốc.
- Không phải sản phẩm production: không có auth, rate limit, hay lưu trữ hội thoại lâu dài — xem
  mục 7 (Giới hạn đã biết).

---

## 2. Kiến trúc tổng thể

```
data/k3_university/*.md            (nguồn: chính sách công khai VinUni, front matter YAML)
        │  ingest.build_knowledge_base()   [ingest.py — dùng lại nguyên vẹn từ lab]
        ▼
RecursiveChunker(chunk_size=500)  →  chunk + gắn metadata (doc_id, title, audience, category, ...)
        │  embedding_fn (OpenAIEmbedder / LocalEmbedder / mock — main.py._select_embedder)
        ▼
EmbeddingStore (src/store.py)     — in-memory vector store, load 1 lần khi backend khởi động
        ▼
CitingChatAgent (backend/chat_agent.py)
   1. Query analyst (LLM rẻ)  → sinh tối đa 4 truy vấn phụ (đồng nghĩa, thuật ngữ tiếng Anh)
   2. store.search_with_filter(enriched_query, top_k, metadata_filter)
   3. Đánh số kết quả thành "nguồn" [1..k] kèm metadata
   4. Chat model (OpenAI) trả lời CHỈ dựa trên các nguồn, trích dẫn [n]
        ▼
FastAPI (backend/main.py)  →  POST /api/chat, GET /api/health
        ▼  (Vite dev proxy "/api" → http://127.0.0.1:8000)
React + Vite (frontend/)   →  giao diện chat, hiển thị câu trả lời (Markdown) + panel nguồn trích dẫn
```

**Nguyên tắc tách lớp quan trọng:** `backend/chat_agent.py` (`CitingChatAgent`) là một agent
**độc lập** với `src/agent.py` (`KnowledgeBaseAgent` — bài nộp lab). Hai agent dùng chung
`EmbeddingStore` nhưng không phụ thuộc lẫn nhau, để phần app không rủi ro phá vỡ phần code được
chấm điểm.

---

## 3. Workflow xử lý một lượt chat

1. **Frontend** gửi `POST /api/chat` với `{message, top_k, audience?}` (xem mục 5 — API).
2. **Query expansion** (`CitingChatAgent._expand_queries`): gọi `chat_model` với
   `QUERY_ANALYST_PROMPT`, yêu cầu trả về JSON `{"queries": [...]}` — tối đa 4 câu truy vấn phụ
   (thuật ngữ tiếng Anh xuất hiện trong văn bản chính sách gốc, số liệu/bảng cần tìm, cách diễn đạt
   đồng nghĩa). Câu hỏi gốc luôn được giữ lại là truy vấn đầu tiên. Bước này giải quyết lệch ngôn
   ngữ: người dùng hỏi tiếng Việt nhưng nội dung tài liệu lưu bằng tiếng Anh.
   - Nếu bước này lỗi/timeout (ví dụ API tạm gián đoạn) → âm thầm bỏ qua, dùng lại câu hỏi gốc.
3. **Retrieval**: nối tất cả truy vấn (gốc + mở rộng) thành **một** chuỗi, embed **một lần**, gọi
   `EmbeddingStore.search_with_filter(enriched_query, top_k, metadata_filter)`.
   - `metadata_filter` chỉ áp dụng khi frontend gửi `audience` (dropdown "Sinh viên" / "Tất cả").
   - Đây là lựa chọn đơn giản hoá có chủ đích: **không** chạy nhiều truy vấn song song rồi hợp nhất
     kết quả (multi-query fan-out) để giữ độ trễ và chi phí thấp cho bản demo — xem mục 7.
4. **Dựng nguồn trích dẫn** (`_build_citations`): mỗi chunk truy xuất được đánh số `[1..k]`, giữ
   `doc_id`, `title`, `source_url`, `category`, `audience`, `score` (làm tròn 4 số), và tối đa 1200
   ký tự đầu của nội dung chunk làm `snippet`.
   - Nếu không có kết quả nào → trả thẳng câu trả lời "không tìm thấy tài liệu liên quan", không
     gọi thêm chat model (tiết kiệm 1 lượt gọi LLM khi rõ ràng không có gì để trả lời).
5. **Sinh câu trả lời**: ghép các nguồn thành khối `context` (`[n] title\nsnippet`), gửi cho chat
   model cùng `SYSTEM_PROMPT` (mục 4.4) và câu hỏi gốc. Nhiệt độ (`temperature=0.2`) thấp để câu trả
   lời ổn định, bám sát nguồn.
   - Nếu bước này lỗi → fallback: trả trực tiếp 3 snippet liên quan nhất kèm thông báo "dịch vụ tổng
     hợp câu trả lời đang gián đoạn" thay vì để request thất bại hoàn toàn.
6. **Response**: `{answer, citations[]}` trả về frontend.
7. **Frontend** render `answer` dạng Markdown (bảng, danh sách...) qua `react-markdown` +
   `remark-gfm`, và render `citations` thành panel "Nguồn trích dẫn" — mỗi nguồn hiện tiêu đề, đoạn
   trích, độ tương đồng (`score`), và link ngoài tới `source_url`.

---

## 4. Phương pháp theo từng thành phần

### 4.1 Dữ liệu & chunking

- Nguồn dữ liệu, quy trình thu thập, metadata schema: xem `docs/DATA_COLLECTION.md` và
  `report/REPORT_NHOM.md` (mục 1). Không lặp lại ở đây.
- Chunking dùng `RecursiveChunker(chunk_size=500)` (`src/chunking.py`, phần lập trình của lab) —
  ưu tiên tách theo `\n\n` (đoạn/heading Markdown) trước khi rơi xuống `\n`, `. `, `" "`, nên tôn
  trọng cấu trúc Chapter/Article/bảng tốt hơn cắt cứng theo ký tự. Lý do chọn & so sánh với 2 chiến
  lược còn lại: xem `report/REPORT_NHOM.md` mục 2 (Baseline Analysis).

### 4.2 Embedding

- Chọn backend qua biến môi trường `EMBEDDING_PROVIDER` (dùng lại nguyên hàm
  `main._select_embedder()` từ lab, không viết lại):
  - `mock` (mặc định nếu không set) — không cần API key, nhưng **ngữ nghĩa vô nghĩa** (hash-based),
    chỉ dùng để chạy backend offline/kiểm tra hạ tầng.
  - `local` — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chạy offline sau khi
    tải model.
  - `openai` — `text-embedding-3-small` (mặc định) hoặc theo `OPENAI_EMBEDDING_MODEL`, cần
    `OPENAI_API_KEY`.
- Toàn bộ corpus (180 chunk) được embed **một lần khi backend khởi động** (`lifespan` handler của
  FastAPI) và giữ trong bộ nhớ (`EmbeddingStore._store`) — không persist ra đĩa, không dùng
  ChromaDB (dù `EmbeddingStore` có hỗ trợ dual-write nếu `chromadb` cài sẵn).

### 4.3 Retrieval

- `EmbeddingStore.search_with_filter`: lọc theo metadata **trước**, tính similarity (dot product
  trên embedding đã chuẩn hoá độ dài 1 ⇒ tương đương cosine similarity) **sau**, cắt `top_k`.
- Tham số `audience` từ frontend (dropdown "Mọi đối tượng" / "Sinh viên" / "Tất cả") ánh xạ thẳng
  sang `metadata_filter={"audience": ...}` — đúng yêu cầu K3 phải có ít nhất 1 kịch bản dùng
  metadata filter (`K3_VARIANT.md`).

### 4.4 Sinh câu trả lời (chat generation)

- Model mặc định: `gpt-4o-mini` (đổi qua `OPENAI_CHAT_MODEL`), dùng **cùng `OPENAI_API_KEY`** với
  embedding — quyết định dùng LLM sinh văn bản (thay vì chỉ trích đoạn) đã được xác nhận rõ ràng với
  người phụ trách trước khi triển khai (phát sinh chi phí thật, dù rất nhỏ cho quy mô demo).
- `SYSTEM_PROMPT` (tiếng Việt, xem `backend/chat_agent.py`) ép buộc:
  1. Chỉ trả lời dựa trên nguồn được cung cấp, không bịa thêm.
  2. Mỗi khẳng định quan trọng phải kèm `[n]` khớp số nguồn.
  3. Nếu nguồn không đủ thông tin → nói rõ "không tìm thấy", không đoán.
  4. Được phép tự tính toán (vd. trung bình) từ số liệu trong nguồn nhưng phải nêu rõ công thức/giả
     định và gọi rõ là "số tự tính", không phải số VinUni công bố chính thức.
  5. Với câu hỏi mơ hồ, đưa cách hiểu hợp lý nhất + nêu các cách hiểu khác, không từ chối trả lời
     nếu vẫn có dữ liệu hữu ích.
  6. Trả lời tiếng Việt trừ khi hỏi bằng tiếng Anh; ngắn gọn, đi thẳng vào con số/điều kiện.

### 4.5 Xử lý lỗi & suy giảm nhẹ nhàng (graceful degradation)

| Tình huống | Hành vi |
|---|---|
| Không có `OPENAI_API_KEY` khi khởi động | `state["agent"] = None`; `POST /api/chat` trả `503` kèm thông báo rõ ràng; `GET /api/health` vẫn chạy được (`chat_enabled: false`) để biết server sống nhưng thiếu key. |
| Query-analyst call lỗi/timeout | Bỏ qua, dùng lại câu hỏi gốc làm truy vấn duy nhất. |
| Retrieval lỗi (embedding provider down) | Trả `[]`, agent trả lời "không tìm thấy tài liệu liên quan". |
| Không có chunk nào truy xuất được | Trả lời cố định, **không** gọi thêm chat model. |
| Chat completion lỗi/timeout | Fallback trích 3 snippet liên quan nhất kèm thông báo dịch vụ tổng hợp đang gián đoạn — người dùng vẫn thấy bằng chứng thô thay vì lỗi trắng trang. |
| Lỗi không lường trước trong `POST /api/chat` | `main.py` bắt `Exception` quanh `agent.ask(...)`, trả `200` với câu trả lời fallback thay vì `500`, để frontend luôn có nội dung hiển thị. |

---

## 5. API

### `GET /api/health`

```json
{
  "status": "ok",
  "embedding_backend": "text-embedding-3-small",
  "collection_size": 180,
  "chat_enabled": true
}
```

### `POST /api/chat`

Request:

```json
{
  "message": "Sinh viên được mượn tối đa bao nhiêu sách ở thư viện?",
  "top_k": 5,
  "audience": "student"
}
```

- `message` (string, bắt buộc, ≥1 ký tự)
- `top_k` (int, mặc định 5, giới hạn 1–10)
- `audience` (string | null, tuỳ chọn) — lọc `metadata_filter={"audience": audience}`

Response (`200`):

```json
{
  "answer": "Sinh viên đại học được mượn tối đa 3 cuốn sách trong 2 tuần... [2]",
  "citations": [
    {
      "index": 2,
      "doc_id": "k3-library-services",
      "title": "Library Access & Services Policy",
      "source_url": "https://policy.vinuni.edu.vn/all-policies/library-policies-for-users/",
      "category": "library-services",
      "audience": "all",
      "score": 0.4437,
      "snippet": "..."
    }
  ]
}
```

Lỗi: `503` nếu server chưa cấu hình `OPENAI_API_KEY` (chat bị tắt).

---

## 6. Cấu trúc thư mục & cách chạy

```
backend/
├── __init__.py
├── main.py          ← FastAPI app, lifespan (build KB 1 lần), /api/health, /api/chat
└── chat_agent.py     ← CitingChatAgent (query expansion → retrieval → citation → chat completion)
frontend/
├── src/
│   ├── App.tsx        ← Giao diện chat (state hội thoại, gợi ý câu hỏi, panel trích dẫn)
│   ├── api.ts          ← askQuestion() gọi POST /api/chat
│   └── types.ts        ← Kiểu ChatResponse/Citation/ChatMessage dùng chung
└── vite.config.ts     ← Proxy dev "/api" → http://127.0.0.1:8000 (không cần cấu hình CORS thủ công khi dev)
scripts/
└── test_kb.py         ← Script kiểm tra retrieval độc lập (không qua backend/LLM), chạy 5 câu hỏi benchmark của nhóm
requirements-backend.txt ← requirements.txt (lab) + fastapi, openai, uvicorn[standard]
scripts/install_requirements.ps1 / .cmd ← tạo .venv + cài requirements-backend.txt
```

**Chạy backend:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

**Chạy frontend** (thư mục `frontend/`):

```bash
npm install
npm run dev      # http://localhost:5173, tự proxy /api sang backend:8000
```

**Biến môi trường cần thiết** (`.env` ở gốc repo):

```
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small   # tuỳ chọn
OPENAI_CHAT_MODEL=gpt-4o-mini                   # tuỳ chọn
LAB_DATA_DIR=data/k3_university                 # tuỳ chọn, mặc định đã đúng
```

**Kiểm tra chỉ riêng retrieval** (không tốn phí chat completion):

```bash
python3 scripts/test_kb.py                     # chạy 5 câu hỏi benchmark của nhóm
python3 scripts/test_kb.py "câu hỏi tuỳ ý"
```

---

## 7. Giới hạn đã biết & hướng cải thiện tiếp theo

- **Không persist embedding**: mỗi lần restart backend, toàn bộ corpus được embed lại từ đầu (~180
  lượt gọi OpenAI embedding). Chấp nhận được ở quy mô demo (vài giây, chi phí không đáng kể), nhưng
  cần cache ra đĩa (hoặc dùng `ChromaDB` với `CHROMA_PERSIST_DIR` đã có sẵn trong `.env.example`)
  nếu corpus lớn hơn.
- **Không có bộ nhớ hội thoại (conversation memory)**: mỗi lượt chat độc lập, không gửi lịch sử hội
  thoại trước đó cho chat model — câu hỏi nối tiếp kiểu "còn học phí Y học thì sao?" sẽ không hiểu
  ngữ cảnh câu trước.
- **Chunk boundary vẫn có thể cắt mất số liệu quan trọng** và **metadata filter không sửa được lỗi
  chunking gốc** — hai ca lỗi thật đã ghi nhận ở `report/REPORT_NGUYENMAITHANHTRUC_2A202601473.md`
  (mục 5): câu hỏi hoàn học phí và câu hỏi mức kỷ luật cao nhất đều không truy xuất đúng chunk dù
  đã thử metadata filter. Hướng cải thiện: chunking theo heading/mục (`##`/`###`) để giữ trọn bảng
  cùng đoạn giới thiệu, thay vì cắt cứng theo `chunk_size`.
- **Query expansion là 1 lần gọi LLM + 1 lần search gộp**, không phải multi-query fan-out có hợp
  nhất/re-rank kết quả — đơn giản, rẻ, nhưng có thể bỏ lỡ trường hợp một truy vấn phụ đáng ra tìm
  đúng chunk mà truy vấn gộp lại làm loãng.
- **Không auth, không rate limit** — CORS hiện chỉ mở cho `localhost:5173`/`127.0.0.1:5173`
  (dev). Triển khai thật cần thêm xác thực, giới hạn tần suất gọi, và reverse-proxy `/api` ở tầng
  production (Vite dev proxy trong `vite.config.ts` **chỉ hoạt động khi chạy `npm run dev`**, không
  áp dụng cho bản build tĩnh `npm run build`/`dist/`).
- **Chưa có test tự động cho `backend/`** (khác với `src/` đã có `tests/test_solution.py` với 42
  test) — nếu mở rộng thêm, nên thêm test cho `CitingChatAgent` (mock `client`/`store`) và test
  tích hợp cho `POST /api/chat` bằng `TestClient` của FastAPI.
