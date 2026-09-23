import os
import re
from pathlib import Path
from typing import List, Dict, Any

class LocalRAGEngine:
    """
    Offline local knowledge base engine indexing refinery SOPs & standards.
    Operates 100% on-premises with zero external API calls.
    Never fabricates citations when the corpus is empty or query has no match.
    """
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base = Path(__file__).resolve().parent.parent.parent
            data_dir = str(base / "data")
        self.data_dir = data_dir
        self.documents: List[Dict[str, Any]] = []
        self.load_corpus()

    def load_corpus(self):
        # Look in data/sample_docs/compliance_sops and data/sample_docs/sops_and_standards
        candidates = [
            os.path.join(self.data_dir, "sample_docs", "compliance_sops"),
            os.path.join(self.data_dir, "sample_docs", "sops_and_standards")
        ]
        for sops_dir in candidates:
            if os.path.exists(sops_dir):
                for fname in sorted(os.listdir(sops_dir)):
                    if fname.endswith((".md", ".txt")):
                        fpath = os.path.join(sops_dir, fname)
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                        
                        sections = [s.strip() for s in text.split("##") if s.strip()]
                        for sec in sections:
                            lines = sec.split("\n")
                            title = lines[0].strip("# ") if lines else fname
                            content = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec
                            self.documents.append({
                                "source_file": fname,
                                "section_title": title,
                                "content": content or sec,
                                "full_text": sec
                            })

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs local keyword-matching search. Returns empty list if no matches found.
        """
        if not self.documents:
            return []

        keywords = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        if not keywords:
            return []

        scored = []
        for doc in self.documents:
            text = (doc["section_title"] + " " + doc["content"]).lower()
            score = sum(text.count(kw) for kw in keywords)
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]

    def query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Structured query interface returning matches and count.
        """
        matches = self.search(query, top_k=top_k)
        return {"query": query, "matches": matches, "count": len(matches)}

    def get_index_stats(self) -> Dict[str, Any]:
        doc_names = set(d["source_file"] for d in self.documents)
        return {
            "search_mode": "Offline Local Search over Technical Standards",
            "indexed_files": sorted(list(doc_names)),
            "total_chunks": len(self.documents),
            "status": "ONLINE (100% Air-Gapped)"
        }

# Global singleton
local_rag = LocalRAGEngine()
