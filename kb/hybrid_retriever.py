#!/usr/bin/env python3
"""
================================================================================
SIH 2026: GRAPHRAG HYBRID RETRIEVER & CROSS-ENCODER RERANKER (TASK L12)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Fuses Dense Vector Search, BM25 Keyword Search, and Knowledge Graph Multi-Hop Traversal.
================================================================================
"""

import os
import sys
import re
import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

import networkx as nx
import matplotlib.pyplot as plt

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from kb.graph_builder import kg_builder
from agent.tools.rag import LocalRAGEngine

class HybridGraphRetriever:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent
        self.rag = LocalRAGEngine()
        self.graph = kg_builder.load_graph()
        self.output_dir = self.base_dir / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _extract_entities_from_query(self, query: str) -> List[str]:
        """Identifies equipment tags, components, damage mechanisms, and units in text."""
        q_upper = query.upper()
        found_nodes = []

        for node, data in self.graph.nodes(data=True):
            nid = node.upper()
            lbl = data.get("label", "").upper()
            tag = str(data.get("tag", "")).upper()
            
            # Match equipment tag
            if tag and tag in q_upper:
                found_nodes.append(node)
                continue
            # Match explicit node ID or label words
            if node in query or (len(lbl) > 4 and lbl in q_upper):
                found_nodes.append(node)
                continue
            # Match key keywords
            if "V-101" in q_upper and "V-101" in nid:
                found_nodes.append(node)
            elif "V-205" in q_upper and "V-205" in nid:
                found_nodes.append(node)
            elif "C-101" in q_upper and "C-101" in nid:
                found_nodes.append(node)
            elif ("COURSE 3" in q_upper or "SHELL 3" in q_upper) and "SHELL_C3" in nid:
                found_nodes.append(node)
            elif "NAPHTHENIC" in q_upper and "NAPHTHENIC" in nid:
                found_nodes.append(node)
            elif "CDU-1" in q_upper and "CDU-1" in nid:
                found_nodes.append(node)

        return list(set(found_nodes))

    def _graph_traverse(self, seed_nodes: List[str], max_hops: int = 3) -> List[Dict[str, Any]]:
        """
        Executes multi-hop traversal from recognized seed entities across directed and undirected paths.
        """
        results = []
        visited_nodes: Set[str] = set()
        traversal_paths = []

        # Convert to undirected view for structural neighborhood exploration
        undirected_G = self.graph.to_undirected()

        for seed in seed_nodes:
            if seed not in self.graph:
                continue
            
            # Find paths up to max_hops
            for target in self.graph.nodes():
                if target == seed:
                    continue
                try:
                    if nx.has_path(undirected_G, seed, target):
                        path = nx.shortest_path(undirected_G, seed, target)
                        if 1 < len(path) <= (max_hops + 1):
                            traversal_paths.append(path)
                except Exception:
                    pass

        # Score and summarize visited relational nodes
        for path in traversal_paths:
            target_node = path[-1]
            if target_node in visited_nodes:
                continue
            visited_nodes.add(target_node)
            node_data = self.graph.nodes[target_node]
            
            path_str = " -> ".join([self.graph.nodes[p].get("label", p) for p in path])
            results.append({
                "source_type": "KNOWLEDGE_GRAPH",
                "node_id": target_node,
                "node_type": node_data.get("node_type"),
                "label": node_data.get("label"),
                "content": f"{node_data.get('label')} [{node_data.get('node_type')}] — Traversal: {path_str}",
                "source_file": node_data.get("source_doc", "equipment_kg.json"),
                "source_span": node_data.get("source_span", "Relational graph link"),
                "traversal_path": path,
                "hop_distance": len(path) - 1,
                "graph_score": 1.0 / (len(path))
            })

        results.sort(key=lambda x: x["graph_score"], reverse=True)
        return results

    def _bm25_search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Lexical matching over document chunks."""
        keywords = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        if not keywords or not self.rag.documents:
            return []

        scored = []
        for doc in self.rag.documents:
            text = (doc["section_title"] + " " + doc["content"]).lower()
            score = 0.0
            for kw in keywords:
                tf = text.count(kw)
                if tf > 0:
                    score += 1.0 + math.log(tf)
            if score > 0:
                scored.append({
                    "source_type": "BM25_KEYWORD",
                    "content": doc["content"],
                    "source_file": doc["source_file"],
                    "section_title": doc["section_title"],
                    "lexical_score": score
                })

        scored.sort(key=lambda x: x["lexical_score"], reverse=True)
        return scored[:top_k]

    def _dense_vector_search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Semantic vector retrieval simulation across document corpus."""
        rag_hits = self.rag.search(query, top_k=top_k)
        results = []
        for i, hit in enumerate(rag_hits):
            results.append({
                "source_type": "DENSE_VECTOR",
                "content": hit.get("content", ""),
                "source_file": hit.get("source_file", ""),
                "section_title": hit.get("section_title", ""),
                "vector_score": 1.0 / (i + 1)
            })
        return results

    def _cross_encoder_rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Local cross-encoder reranker scoring exact token overlap, regulatory relevance, and technical intent.
        """
        q_tokens = set(re.findall(r'\w+', query.lower()))
        reranked = []

        for item in candidates:
            text = (item.get("content", "") + " " + item.get("source_file", "") + " " + str(item.get("label", ""))).lower()
            overlap = sum(1 for t in q_tokens if t in text)
            
            # Domain bonus weights for standard clauses, actions, and equipment entities
            standard_bonus = 1.0
            if "standard" in query.lower() or "governs" in query.lower() or "code" in query.lower():
                if item.get("node_type") == "StandardClause" or "api" in text or "oisd" in text:
                    standard_bonus = 2.5
            elif any(s in text for s in ["api-510", "oisd", "7.1.1", "6.2", "weld"]):
                standard_bonus = 1.5

            relational_bonus = 1.6 if item.get("source_type") == "KNOWLEDGE_GRAPH" else 1.0
            
            base_score = item.get("fused_score", item.get("vector_score", 0.5))
            rerank_score = (base_score * 0.3) + ((overlap / (len(q_tokens) + 1e-5)) * 0.4 * standard_bonus * relational_bonus)
            if item.get("node_type") == "StandardClause" and ("standard" in query.lower() or "governs" in query.lower()):
                rerank_score += 0.25
            
            item["rerank_score"] = round(rerank_score, 4)
            reranked.append(item)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]

    def retrieve(
        self,
        query: str,
        retrieval_mode: str = "hybrid",  # 'vector' | 'hybrid' | 'graph'
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes multi-channel retrieval and fusion.
        """
        t0 = time.time()
        seed_entities = self._extract_entities_from_query(query)
        
        vector_res = []
        keyword_res = []
        graph_res = []

        if retrieval_mode in ["vector", "hybrid"]:
            vector_res = self._dense_vector_search(query, top_k=20)

        if retrieval_mode in ["hybrid"]:
            keyword_res = self._bm25_search(query, top_k=20)

        if retrieval_mode in ["graph", "hybrid"]:
            graph_res = self._graph_traverse(seed_entities, max_hops=3)

        # Reciprocal Rank Fusion (RRF)
        fused_pool: Dict[str, Dict[str, Any]] = {}
        k_const = 60.0

        for rank, item in enumerate(vector_res):
            key = item["content"][:120]
            if key not in fused_pool:
                fused_pool[key] = {**item, "fused_score": 0.0, "vector_rank": rank + 1}
            fused_pool[key]["fused_score"] += 1.0 / (k_const + rank + 1)

        for rank, item in enumerate(keyword_res):
            key = item["content"][:120]
            if key not in fused_pool:
                fused_pool[key] = {**item, "fused_score": 0.0, "keyword_rank": rank + 1}
            fused_pool[key]["fused_score"] += 1.0 / (k_const + rank + 1)

        for rank, item in enumerate(graph_res):
            key = item["content"][:120]
            if key not in fused_pool:
                fused_pool[key] = {**item, "fused_score": 0.0, "graph_rank": rank + 1}
            fused_pool[key]["fused_score"] += (1.0 / (k_const + rank + 1)) * 1.5  # Relational precision weighting

        fused_candidates = list(fused_pool.values())
        fused_candidates.sort(key=lambda x: x.get("fused_score", 0.0), reverse=True)

        # Cross-Encoder Rerank top candidates
        top_reranked = self._cross_encoder_rerank(query, fused_candidates[:40], top_k=top_k)
        elapsed_ms = round((time.time() - t0) * 1000, 2)

        return {
            "query": query,
            "retrieval_mode": retrieval_mode,
            "latency_ms": elapsed_ms,
            "seed_entities": seed_entities,
            "results_count": len(top_reranked),
            "top_results": top_reranked
        }

    def render_subgraph(self, nodes_subset: List[str], output_path: str = "outputs/retrieval_subgraph.png") -> str:
        """
        Renders a query explanation subgraph to image with node source provenance.
        """
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        subG = self.graph.subgraph(nodes_subset).copy()
        if subG.number_of_nodes() == 0:
            subG = self.graph.subgraph(list(self.graph.nodes())[:6]).copy()

        plt.figure(figsize=(10, 6), dpi=150)
        pos = nx.spring_layout(subG, seed=42)
        
        labels = {n: f"{subG.nodes[n].get('label', n)}\n[{subG.nodes[n].get('source_doc', 'KG')}]" for n in subG.nodes()}
        
        nx.draw_networkx_nodes(subG, pos, node_color="#0284C7", node_size=3200, alpha=0.9)
        nx.draw_networkx_labels(subG, pos, labels=labels, font_size=7, font_color="white", font_weight="bold")
        nx.draw_networkx_edges(subG, pos, edge_color="#64748B", arrowsize=15, width=1.5)
        
        edge_labels = {(u, v): subG.edges[u, v].get("relation", "") for u, v in subG.edges()}
        nx.draw_networkx_edge_labels(subG, pos, edge_labels=edge_labels, font_size=6)
        
        plt.title("MRPL GraphRAG: Query Explanation Relational Subgraph", fontsize=11, fontweight="bold")
        plt.axis("off")
        plt.savefig(str(out_p), bbox_inches="tight", facecolor="white")
        plt.close()
        return str(out_p)

# Global Hybrid Retriever Instance
hybrid_retriever = HybridGraphRetriever()

if __name__ == "__main__":
    res = hybrid_retriever.retrieve("which other equipment in this unit shares the damage mechanism found on V-101", retrieval_mode="hybrid")
    print(f"Retrieved {len(res['top_results'])} results in {res['latency_ms']} ms")
    for r in res['top_results']:
        print(f" - [{r.get('source_type')}] Score: {r.get('rerank_score')} | {r.get('content')[:90]}...")
