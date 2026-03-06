from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class LearningMemory:
    """Persistent learning memory backed by ChromaDB + sentence-transformers.

    Falls back to keyword matching when embedding backend is unavailable.
    """

    def __init__(
        self,
        persist_directory: str,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.enabled = True
        self._client = None
        self._ef = None

        try:
            os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
            os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")
            os.environ.setdefault(
                "CHROMA_PRODUCT_TELEMETRY_IMPL",
                "chromadb.telemetry.product.null.NullProductTelemetry",
            )
            import chromadb
            from chromadb.config import Settings
            from chromadb.utils import embedding_functions

            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            settings = Settings(anonymized_telemetry=False)
            self._client = chromadb.PersistentClient(path=persist_directory, settings=settings)
            self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
        except Exception:
            self.enabled = False

        self.collections = {
            "bug_memory": self._get_or_create("bug_memory"),
            "architecture_memory": self._get_or_create("architecture_memory"),
            "solution_memory": self._get_or_create("solution_memory"),
            "code_patterns": self._get_or_create("code_patterns"),
            "task_memory": self._get_or_create("task_memory"),
            "skills": self._get_or_create("skills"),
        }

    def _get_or_create(self, name: str):
        if not self.enabled or self._client is None:
            return None
        assert self._client is not None
        if self._ef is not None:
            return self._client.get_or_create_collection(name=name, embedding_function=self._ef)
        return self._client.get_or_create_collection(name=name)

    def _id_for(self, prefix: str, text: str) -> str:
        digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()
        return f"{prefix}:{digest}"

    def _local_fallback_path(self) -> Path:
        return Path(self.persist_directory) / "fallback_memory.json"

    def _fallback_load(self) -> dict[str, list[dict[str, Any]]]:
        path = self._local_fallback_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _fallback_save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        path = self._local_fallback_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_memory(self, memory_type: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        metadata = metadata or {}
        collection = self.collections.get(memory_type)

        if self.enabled and collection is not None:
            record_id = self._id_for(memory_type, text + json.dumps(metadata, sort_keys=True))
            collection.upsert(ids=[record_id], documents=[text], metadatas=[metadata])
            return

        payload = self._fallback_load()
        payload.setdefault(memory_type, []).append({"text": text, "metadata": metadata})
        payload[memory_type] = payload[memory_type][-500:]
        self._fallback_save(payload)

    def query_memory(self, memory_type: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        collection = self.collections.get(memory_type)
        if self.enabled and collection is not None:
            result = collection.query(query_texts=[query], n_results=limit)
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            return [{"text": d, "metadata": m or {}} for d, m in zip(docs, metas)]

        payload = self._fallback_load().get(memory_type, [])
        query_terms = [t for t in query.lower().split() if len(t) > 2]
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in payload:
            text = str(item.get("text", "")).lower()
            score = sum(text.count(term) for term in query_terms)
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def add_skill(self, skill_name: str, description: str, payload: dict[str, Any]) -> None:
        text = f"{skill_name}: {description}\n{json.dumps(payload, ensure_ascii=True)}"
        data = {"skill": skill_name, "kind": "skill"}
        self.add_memory("skills", text=text, metadata=data)

    def index_repository(self, workspace_root: str) -> int:
        root = Path(workspace_root)
        indexed = 0
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {".git", "node_modules", ".venv", "dist", "build", "__pycache__"} for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".json", ".md", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")[:5000]
            if not text.strip():
                continue
            self.add_memory(
                "code_patterns",
                text=f"FILE: {path.relative_to(root)}\n{text}",
                metadata={"path": str(path.relative_to(root)), "kind": "code_file"},
            )
            indexed += 1
        return indexed

    def query_codebase(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        return self.query_memory("code_patterns", query=query, limit=limit)

    def store_task_workflow(self, task: str, steps: list[str], outcome: str, notes: str = "") -> None:
        body = {
            "task": task,
            "steps": steps,
            "outcome": outcome,
            "notes": notes,
        }
        self.add_memory("task_memory", text=json.dumps(body, ensure_ascii=True), metadata={"task": task, "outcome": outcome})

    def retrieve_task_workflows(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        return self.query_memory("task_memory", query=query, limit=limit)
