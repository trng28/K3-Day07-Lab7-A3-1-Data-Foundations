"""A citation-aware chat agent on top of the Lab 7 EmbeddingStore.

This is intentionally separate from src/agent.py's KnowledgeBaseAgent (the
graded lab deliverable) so the small app built on top of the lab never risks
touching the code that gets unit-tested/submitted for the lab itself.

Flow: retrieve top-k chunks (optionally metadata-filtered) -> number them as
sources -> ask an OpenAI chat model to answer using ONLY those sources and
cite them as [1], [2], ... -> return the answer plus the structured source
list so the frontend can render clickable citations.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

SYSTEM_PROMPT = """\
Bạn là trợ lý trả lời câu hỏi về quy định/dịch vụ đại học VinUniversity, \
chỉ dựa trên các đoạn tài liệu (nguồn) được cung cấp bên dưới, không được bịa \
thêm thông tin ngoài các nguồn đó.

Quy tắc:
- Trả lời bằng tiếng Việt trừ khi câu hỏi được đặt bằng tiếng Anh.
- Mỗi khẳng định quan trọng phải kèm trích dẫn số nguồn dạng [1], [2], v.v., \
khớp với số thứ tự nguồn được cung cấp.
- Nếu các nguồn không đủ thông tin để trả lời, hãy nói rõ là không tìm thấy \
thông tin trong tài liệu, đừng đoán.
- Phân biệt rõ "không có một con số chính thức" với "không có dữ liệu". Nếu nguồn có
  nhiều mức theo chương trình/đối tượng, hãy liệt kê các mức liên quan trước.
- Được phép tính toán từ các con số trong nguồn (ví dụ trung bình cộng), nhưng phải ghi
  rõ công thức, phạm vi, giả định và gọi đó là số tự tính — không phải số VinUni công bố.
- Với câu hỏi mơ hồ như "trung bình", hãy đưa ra cách hiểu hợp lý nhất và nêu rõ các
  cách hiểu khác; không từ chối nếu vẫn có thể trả lời hữu ích từ dữ liệu.
- Ngắn gọn, đi thẳng vào quy định/con số cụ thể (thời hạn, tỷ lệ %, điều kiện).\
"""

QUERY_ANALYST_PROMPT = """\
Bạn là retrieval analyst cho kho quy định VinUniversity bằng tiếng Anh, còn người dùng
có thể hỏi bằng tiếng Việt. Hãy chuyển câu hỏi thành tối đa 4 truy vấn tìm kiếm ngắn,
bao gồm thuật ngữ tiếng Anh trong văn bản chính sách, số liệu/bảng cần tìm và cách diễn
đạt đồng nghĩa. Chỉ trả về JSON hợp lệ dạng {"queries": ["..."]}; không giải thích.\
"""


@dataclass
class Citation:
    index: int
    doc_id: str
    title: str
    source_url: str
    category: str | None
    audience: str | None
    score: float
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "doc_id": self.doc_id,
            "title": self.title,
            "source_url": self.source_url,
            "category": self.category,
            "audience": self.audience,
            "score": self.score,
            "snippet": self.snippet,
        }


@dataclass
class ChatResponse:
    answer: str
    citations: list[Citation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "citations": [c.to_dict() for c in self.citations]}


class CitingChatAgent:
    """RAG chat agent that retrieves from an EmbeddingStore and cites its sources."""

    def __init__(self, store, client, chat_model: str = "gpt-4o-mini") -> None:
        self.store = store
        self.client = client
        self.chat_model = chat_model

    def _build_citations(self, hits: list[dict[str, Any]]) -> list[Citation]:
        citations: list[Citation] = []
        for i, hit in enumerate(hits, start=1):
            meta = hit["metadata"]
            citations.append(
                Citation(
                    index=i,
                    doc_id=meta.get("doc_id", "unknown"),
                    title=meta.get("title", meta.get("doc_id", "unknown")),
                    source_url=meta.get("source_url", ""),
                    category=meta.get("category"),
                    audience=meta.get("audience"),
                    score=round(float(hit["score"]), 4),
                    snippet=hit["content"][:1200].strip(),
                )
            )
        return citations

    def _build_context(self, citations: list[Citation]) -> str:
        blocks = [f"[{c.index}] {c.title}\n{c.snippet}" for c in citations]
        return "\n\n".join(blocks)

    def _expand_queries(self, question: str) -> list[str]:
        """Use a lightweight analyst pass to bridge Vietnamese queries to English policy text."""
        try:
            planner_client = (
                self.client.with_options(timeout=12.0, max_retries=0)
                if hasattr(self.client, "with_options")
                else self.client
            )
            completion = planner_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": QUERY_ANALYST_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            payload = json.loads(completion.choices[0].message.content or "{}")
            generated = payload.get("queries", [])
        except Exception:
            generated = []

        queries = [question]
        for query in generated:
            if isinstance(query, str) and query.strip() and query.strip() not in queries:
                queries.append(query.strip())
        return queries[:5]

    def _retrieve(
        self,
        question: str,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Retrieve once using an analyst-enriched query to keep API latency bounded."""
        expanded_queries = self._expand_queries(question)
        enriched_query = "\n".join(expanded_queries)
        try:
            return self.store.search_with_filter(
                enriched_query,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        except Exception:
            return []

    def ask(self, question: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None) -> ChatResponse:
        hits = self._retrieve(question, top_k=top_k, metadata_filter=metadata_filter)
        citations = self._build_citations(hits)

        if not citations:
            return ChatResponse(
                answer="Không tìm thấy tài liệu liên quan trong cơ sở tri thức để trả lời câu hỏi này.",
                citations=[],
            )

        context = self._build_context(citations)
        user_content = (
            f"Các nguồn tài liệu:\n\n{context}\n\n"
            f"Câu hỏi gốc: {question}\n\n"
            "Hãy tổng hợp trực tiếp từ các nguồn trên. Nếu câu hỏi yêu cầu một phép "
            "tính không được công bố sẵn, hãy tính và ghi rõ giả định."
        )

        try:
            answer_client = (
                self.client.with_options(timeout=25.0, max_retries=0)
                if hasattr(self.client, "with_options")
                else self.client
            )
            completion = answer_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
            )
            answer = completion.choices[0].message.content or ""
        except Exception:
            # Keep the demo useful when the chat provider temporarily returns
            # 429/5xx: retrieval evidence remains available and cited.
            source_lines = [
                f"- [{citation.index}] {citation.snippet}"
                for citation in citations[:3]
            ]
            answer = (
                "Dịch vụ tổng hợp câu trả lời đang tạm thời gián đoạn. "
                "Dưới đây là các thông tin liên quan truy xuất trực tiếp từ tài liệu:\n\n"
                + "\n\n".join(source_lines)
            )
        return ChatResponse(answer=answer.strip(), citations=citations)
