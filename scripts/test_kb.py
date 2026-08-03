"""CLI smoke test cho knowledge base dịch vụ đại học K3.

Ví dụ:
    python scripts/test_kb.py
    python scripts/test_kb.py "Quy định chuyển đổi tín chỉ là gì?"
    python scripts/test_kb.py --data-dir data/k3_university --top-k 5
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Windows may inherit a legacy console encoding (for example cp1252), which
# cannot print Vietnamese text. Force UTF-8 for this CLI without requiring
# users to run `chcp 65001` first.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

from ingest import build_knowledge_base
from main import DEFAULT_DATA_DIR, _select_embedder
from src.chunking import RecursiveChunker


BENCHMARK_QUERIES = [
    {
        "query": "Sinh viên được công nhận tối đa bao nhiêu phần trăm tổng số tín chỉ của chương trình khi xin chuyển đổi tín chỉ?",
        "metadata_filter": None,
    },
    {
        "query": "Sinh viên đại học được mượn tối đa bao nhiêu cuốn sách và trong bao lâu tại thư viện?",
        "metadata_filter": None,
    },
    {
        "query": "Học bổng toàn phần bị tự động hạ bậc nếu GPA năm học nằm trong khoảng nào?",
        "metadata_filter": None,
    },
    {
        "query": "Nếu sinh viên rút học trong vòng 2 tuần kể từ ngày bắt đầu học kỳ, học phí được hoàn lại bao nhiêu phần trăm?",
        "metadata_filter": None,
    },
    {
        "query": "Theo quy chế sinh viên, hình thức kỷ luật cao nhất mà sinh viên có thể phải nhận là gì?",
        "metadata_filter": {"audience": "student"},
    },
]


def run(data_dir: str, queries: list[dict], top_k: int = 3) -> None:
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Data dir: {data_dir}")
    print(f"Embedding backend: {backend}")
    if backend == "mock embeddings fallback":
        print("Cảnh báo: mock embedding chỉ phù hợp smoke test, không đo chất lượng ngữ nghĩa.")

    store = build_knowledge_base(
        data_dir,
        embedding_fn=embedder,
        chunker=RecursiveChunker(chunk_size=500),
    )
    print(f"Loaded {store.get_collection_size()} chunks\n")

    for index, item in enumerate(queries, start=1):
        query = item["query"]
        metadata_filter = item.get("metadata_filter")
        print("=" * 80)
        print(f"[{index}] {query}")
        if metadata_filter:
            print(f"Filter: {metadata_filter}")

        hits = store.search_with_filter(
            query,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        if not hits:
            print("(Không có kết quả)")
            continue

        for rank, hit in enumerate(hits, start=1):
            metadata = hit["metadata"]
            snippet = hit["content"][:150].replace("\n", " ")
            print(
                f"#{rank} score={hit['score']:.4f} "
                f"doc_id={metadata.get('doc_id')} "
                f"source_url={metadata.get('source_url')}"
            )
            print(f"    {snippet}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test khả năng retrieval của knowledge base K3."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Câu hỏi tùy chọn; bỏ trống để chạy 5 câu benchmark.",
    )
    parser.add_argument(
        "--data-dir",
        help=f"Thư mục Markdown (mặc định: LAB_DATA_DIR hoặc {DEFAULT_DATA_DIR}).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Số kết quả cho mỗi câu hỏi (mặc định: 3).",
    )
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k phải lớn hơn hoặc bằng 1")
    return args


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    data_dir = args.data_dir or os.getenv("LAB_DATA_DIR", DEFAULT_DATA_DIR)
    ad_hoc_query = " ".join(args.query).strip()
    queries = (
        [{"query": ad_hoc_query, "metadata_filter": None}]
        if ad_hoc_query
        else BENCHMARK_QUERIES
    )
    run(data_dir, queries, top_k=args.top_k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
