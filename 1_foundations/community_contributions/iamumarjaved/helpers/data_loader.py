from pathlib import Path
from typing import Dict
from pypdf import PdfReader


def load_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


def load_text_file(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_all_documents(base_path: str = "me") -> Dict[str, str]:
    base = Path(base_path)
    documents = {}
    
    linkedin_path = base / "linkedin.pdf"
    if linkedin_path.exists():
        try:
            documents["linkedin"] = load_pdf(linkedin_path)
            print(f"[OK] Loaded LinkedIn: {len(documents['linkedin'])} chars")
        except Exception as e:
            print(f"[ERROR] Error loading LinkedIn: {e}")
            documents["linkedin"] = "LinkedIn profile not available"
    
    for txt_file in ["summary.txt", "projects.txt", "tech_stack.txt"]:
        file_path = base / txt_file
        if file_path.exists():
            try:
                doc_name = txt_file.replace(".txt", "")
                documents[doc_name] = load_text_file(file_path)
                print(f"[OK] Loaded {doc_name}: {len(documents[doc_name])} chars")
            except Exception as e:
                print(f"[ERROR] Error loading {txt_file}: {e}")
    
    return documents

