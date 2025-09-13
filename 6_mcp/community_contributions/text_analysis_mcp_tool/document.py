from pydantic import BaseModel
import docx2txt
from pypdf import PdfReader
import textstat

class Document (BaseModel):
    """Document class to hold basic file structure and text functions"""
    filetype: str
    filepath: str

    def file_reader(self):
        text = ""
        if self.filetype in ["txt", ".txt"]:
            with open(self.filepath) as file:
                text = file.read()
            return text

        elif self.filetype in ["docx", "doc",".docx", ".doc"]:
            text = docx2txt.process(self.filepath)
            return text

        elif self.filetype in ["pdf", ".pdf"]:
            file = PdfReader(self.filepath)
            totalPages = len(file.pages)
            if totalPages > 50:
                return "This process is not suited to large pdf documents"
            else:
                for page in file.pages:
                    text += page.extract_text()
                return text
        else:
            return "The filetype is not supported"

    def text_counts(self):
        text = self.file_reader()
        if not text: 
            return "File reader issue" 
        try:
            character_count = len(text)
            word_count = len(text.split())
            line_count = len(text.split('\n'))
            # a bit of a hack!
            temp_text = text.replace('! ', '. ').replace('? ', '. ')
            sentence_count = len(temp_text.split('. ')) 
            time_to_read = round(word_count / 225,1) if word_count >0 else "NA" #225 = average reading speed
            return f"Approximate counts are: Characters - {character_count:,} \nWords - {word_count:,} \nNewlines = {line_count:,} \nSentences - {sentence_count:,} \nAvg. time to read: {time_to_read} minutes."
        except: 
            return "Text counts are not available."

    def text_analyses(self):
        text = self.file_reader()
        if not text: 
            return "File reader issue" 
        try:
            ease_score = textstat.flesch_reading_ease(text)
            rounded_ease_score = round(ease_score)
        except:
            return "Ease score not available"
        ease_assessment = "Needs a rewrite!" if rounded_ease_score < 60 else "Easy reading!" if rounded_ease_score <= 75 else "Wow! Such easy reading!"
        return f"The reading ease_score is {rounded_ease_score} and reading ease assessment is: {ease_assessment}"