"""
Data loading functions for personal information
"""
from pypdf import PdfReader
import os

def load_linkedin_pdf(filename="linkedin.pdf", paths=["me/", "../../me/", "../me/"]):
    """Load and extract text from LinkedIn PDF"""
    for path in paths:
        try:
            full_path = os.path.join(path, filename)
            reader = PdfReader(full_path)
            linkedin = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    linkedin += text
            print(f"✅ Successfully loaded LinkedIn PDF from {path}")
            return linkedin
        except FileNotFoundError:
            continue
    
    print("❌ LinkedIn PDF not found")
    return "LinkedIn profile not found. Please ensure you have a linkedin.pdf file in the me/ directory."

def load_text_file(filename, paths=["me/", "../../me/", "../me/"]):
    """Load text from a file, trying multiple paths"""
    for path in paths:
        try:
            full_path = os.path.join(path, filename)
            with open(f"{path}{filename}", "r", encoding="utf-8") as f:
                content = f.read()
            print(f"✅ Successfully loaded {filename} from {path}")
            return content
        except FileNotFoundError:
            continue
    
    print(f"❌ {filename} not found")
    return f"{filename} not found. Please create this file in the me/ directory."

def load_personal_data():
    """Load all personal data files"""
    linkedin = load_linkedin_pdf()
    summary = load_text_file("summary.txt")
    faq = load_text_file("faq.txt")
    
    return {
        "linkedin": linkedin,
        "summary": summary,
        "faq": faq
    }