from crewai.tools import tool
import requests, os
from pypdf import PdfReader

@tool("Resume Downloader")
def download_resume(resume_link: str):
    """This tool use to download pdf resume file by providing resume link"""

    response = requests.get(resume_link)

    os.makedirs('input', exist_ok=True)

    if response.status_code == 200:
        with open("input/resume.pdf", "wb") as file:
            file.write(response.content)
            print("PDF downloaded successfully")

    else:
        print(f"Failed to download PDF. Status code {response.status_code}")


@tool("Resume Extractor")
def extract_resume() -> str:
    """Always use this tool to extract downloaded resume to convert pdf to text and return string"""

    reader = PdfReader("input/resume.pdf")
    resume_details = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            resume_details += text

    return resume_details
