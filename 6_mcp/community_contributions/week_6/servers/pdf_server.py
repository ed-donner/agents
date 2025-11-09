from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from fpdf import FPDF
import os
import uuid

app = FastAPI()
OUT_DIR = "reports"
os.makedirs(OUT_DIR, exist_ok=True)

class Section(BaseModel):
    title: str
    content: str

class CreateReportRequest(BaseModel):
    title: str
    subtitle: str | None = None
    sections: list[Section]

@app.post("/create_report")
def create_report(req: CreateReportRequest):
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{req.title[:40].replace(' ', '_')}_{now}_{uuid.uuid4().hex[:6]}.pdf"
    path = os.path.join(OUT_DIR, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 10, req.title)
    if req.subtitle:
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, req.subtitle)
    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    for sec in req.sections:
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 8, sec.title)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, sec.content)
        pdf.ln(2)
    pdf.output(path)
    return {"path": path, "filename": filename}

@app.get("/download_report")
def download_report(path: str):
    if not os.path.exists(path):
        return {"error": "file not found"}
    return FileResponse(path, filename=os.path.basename(path), media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
