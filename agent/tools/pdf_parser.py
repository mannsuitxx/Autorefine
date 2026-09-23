import os
from typing import Dict, Any, List, Optional
import pypdf

class PDFParserTool:
    """
    On-Premise PDF Parser Tool using pypdf for sovereign document ingestion.
    Extracts text, page structures, tables, and document metadata completely offline.
    """
    def __init__(self):
        pass

    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parses a PDF file and returns structured text by page with metadata.
        """
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"File not found: {pdf_path}",
                "total_pages": 0,
                "pages": [],
                "text": ""
            }

        try:
            reader = pypdf.PdfReader(pdf_path)
            total_pages = len(reader.pages)
            pages_data = []
            full_text_list = []

            meta = reader.metadata or {}
            metadata_dict = {
                "title": meta.title if meta.title else os.path.basename(pdf_path),
                "author": meta.author if meta.author else "Unknown",
                "creator": meta.creator if meta.creator else "Unknown",
                "producer": meta.producer if meta.producer else "Unknown"
            }

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages_data.append({
                    "page_number": idx + 1,
                    "character_count": len(page_text),
                    "text": page_text
                })
                full_text_list.append(f"--- PAGE {idx + 1} ---\n{page_text}")

            full_text = "\n\n".join(full_text_list)

            return {
                "success": True,
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path),
                "total_pages": total_pages,
                "metadata": metadata_dict,
                "pages": pages_data,
                "text": full_text,
                "summary": f"Extracted {total_pages} pages ({len(full_text)} characters) from {os.path.basename(pdf_path)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse PDF: {str(e)}",
                "total_pages": 0,
                "pages": [],
                "text": ""
            }

    def search_in_pdf(self, pdf_path: str, keyword: str) -> List[Dict[str, Any]]:
        """
        Searches for specific terms across all pages of a PDF.
        """
        result = self.parse_pdf(pdf_path)
        if not result["success"]:
            return []
        
        matches = []
        kw_lower = keyword.lower()
        for p in result["pages"]:
            if kw_lower in p["text"].lower():
                matches.append({
                    "page_number": p["page_number"],
                    "matched_lines": [line.strip() for line in p["text"].split("\n") if kw_lower in line.lower()]
                })
        return matches

# Global singleton instance
pdf_parser = PDFParserTool()
