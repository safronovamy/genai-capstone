import os
import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

from travelmate.services.metrics_service import MetricsService

load_dotenv()

DATA_PATH = "travelmate/data/knowledge_base"
VECTOR_STORE_PATH = "travelmate/data/vector_store"
COLLECTION_NAME = "travelmate"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

client = OpenAI()

chroma_client = chromadb.PersistentClient(
    path=VECTOR_STORE_PATH,
    settings=chromadb.Settings(anonymized_telemetry=False),
)

collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def reset_collection():
    global collection

    existing = chroma_client.list_collections()
    existing_names = [c.name for c in existing]

    if COLLECTION_NAME in existing_names:
        chroma_client.delete_collection(name=COLLECTION_NAME)

    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def _embedding(text: str):
    MetricsService.increment_embedding_calls()

    return client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    ).data[0].embedding


def sanitize_metadata(metadata: dict) -> dict:
    """
    Chroma metadata supports only:
    str, int, float, bool.

    Convert lists/dicts to strings.
    """

    cleaned = {}

    for key, value in metadata.items():
        if isinstance(value, list):
            cleaned[key] = ", ".join(str(v) for v in value)

        elif isinstance(value, dict):
            cleaned[key] = json.dumps(value, ensure_ascii=False)

        elif isinstance(value, (str, int, float, bool)) or value is None:
            cleaned[key] = value

        else:
            cleaned[key] = str(value)

    return cleaned

def split_markdown_by_headings(text: str, max_chars: int = 1200) -> list[dict]:
    """
    Split markdown into semantic chunks by headings.
    Keeps chunks small enough for precise retrieval and lower token usage.
    """
    lines = text.splitlines()

    chunks = []
    current_title = "Introduction"
    current_lines = []

    def flush_chunk():
        nonlocal current_lines, current_title

        content = "\n".join(current_lines).strip()
        if not content:
            return

        # If section is still too large, split by character window.
        if len(content) <= max_chars:
            chunks.append(
                {
                    "title": current_title,
                    "content": content,
                }
            )
        else:
            for i in range(0, len(content), max_chars):
                part = content[i:i + max_chars].strip()
                if part:
                    chunks.append(
                        {
                            "title": f"{current_title} part {i // max_chars + 1}",
                            "content": part,
                        }
                    )

        current_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            flush_chunk()
            current_title = stripped.replace("## ", "").strip()
            current_lines = [line]
        elif stripped.startswith("### "):
            flush_chunk()
            current_title = stripped.replace("### ", "").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_chunk()

    return chunks

def rebuild_index() -> int:
    """
    Rebuild persistent Chroma index from the local knowledge base.

    Run this only when the dataset changes:
    python -m travelmate.scripts.build_index
    """

    reset_collection()

    index = 0

    # ---------------------------------------------------
    # Load city POI datasets
    # ---------------------------------------------------

    for city_folder in os.listdir(DATA_PATH):
        city_path = os.path.join(DATA_PATH, city_folder)

        if not os.path.isdir(city_path):
            continue

        if city_folder == "travel_rules":
            continue

        poi_file = os.path.join(city_path, "poi_dataset.json")

        if not os.path.exists(poi_file):
            continue

        with open(poi_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            tags = item.get("tags", [])

            text = (
                f"{item['name']}. "
                f"{item['description']}. "
                f"Tags: {', '.join(tags)}"
            )

            metadata = sanitize_metadata(
                {
                    **item,
                    "doc_type": "poi",
                }
            )

            collection.add(
                documents=[text],
                embeddings=[_embedding(text)],
                metadatas=[metadata],
                ids=[f"poi_{item['city'].lower()}_{index}"],
            )

            index += 1

    # ---------------------------------------------------
    # Load city guides
    # ---------------------------------------------------

    for city_folder in os.listdir(DATA_PATH):
        city_path = os.path.join(DATA_PATH, city_folder)

        if not os.path.isdir(city_path):
            continue

        if city_folder == "travel_rules":
            continue

        city_guide_file = os.path.join(city_path, "city_guide.md")

        if not os.path.exists(city_guide_file):
            continue

        with open(city_guide_file, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = split_markdown_by_headings(text)

        for chunk_index, chunk in enumerate(chunks):
            chunk_text = chunk["content"]

            metadata = sanitize_metadata(
                {
                    "doc_type": "city_guide",
                    "city": city_folder.title(),
                    "source_file": "city_guide.md",
                    "chunk_index": chunk_index,
                    "chunk_title": chunk["title"],
                }
            )

            collection.add(
                documents=[chunk_text],
                embeddings=[_embedding(chunk_text)],
                metadatas=[metadata],
                ids=[f"city_guide_{city_folder}_{chunk_index}_{index}"],
            )

            index += 1

    # ---------------------------------------------------
    # Load travel patterns / sample itineraries
    # ---------------------------------------------------

    for city_folder in os.listdir(DATA_PATH):
        city_path = os.path.join(DATA_PATH, city_folder)

        if not os.path.isdir(city_path):
            continue

        if city_folder == "travel_rules":
            continue

        sample_file = os.path.join(city_path, "sample_itineraries.md")

        if not os.path.exists(sample_file):
            continue

        with open(sample_file, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = split_markdown_by_headings(text)

        for chunk_index, chunk in enumerate(chunks):
            chunk_text = chunk["content"]

            metadata = sanitize_metadata(
                {
                    "doc_type": "travel_pattern",
                    "city": city_folder.title(),
                    "pattern_file": "sample_itineraries.md",
                    "chunk_index": chunk_index,
                    "chunk_title": chunk["title"],
                }
            )

            collection.add(
                documents=[chunk_text],
                embeddings=[_embedding(chunk_text)],
                metadatas=[metadata],
                ids=[f"pattern_{city_folder}_{chunk_index}_{index}"],
            )

            index += 1

    # ---------------------------------------------------
    # Load travel rules
    # ---------------------------------------------------

    rules_path = os.path.join(DATA_PATH, "travel_rules")

    if os.path.exists(rules_path):
        for filename in os.listdir(rules_path):
            if not filename.endswith(".md"):
                continue

            file_path = os.path.join(rules_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            metadata = sanitize_metadata(
                {
                    "doc_type": "rule",
                    "rule_file": filename,
                    "city": "global",
                }
            )

            collection.add(
                documents=[text],
                embeddings=[_embedding(text)],
                metadatas=[metadata],
                ids=[f"rule_{filename}_{index}"],
            )

            index += 1

    return index


# Backward-compatible alias.
# If some old code still calls load_all_knowledge(), it will still work.
def load_all_knowledge() -> int:
    return rebuild_index()


def query_pois(query_text: str, city: str, n_results: int = 5):
    embedding = _embedding(query_text)

    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={
            "$and": [
                {"doc_type": "poi"},
                {"city": city},
            ]
        },
    )


def query_rules(query_text: str, n_results: int = 3):
    embedding = _embedding(query_text)

    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={"doc_type": "rule"},
    )


def query_travel_patterns(query_text: str, city: str, n_results: int = 2):
    embedding = _embedding(query_text)

    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={
            "$and": [
                {"doc_type": "travel_pattern"},
                {"city": city},
            ]
        },
    )

def query_city_guide(query_text: str, city: str, n_results: int = 3):
    embedding = _embedding(query_text)

    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={
            "$and": [
                {"doc_type": "city_guide"},
                {"city": city},
            ]
        },
    )