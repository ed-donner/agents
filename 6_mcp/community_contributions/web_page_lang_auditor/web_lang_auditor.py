
import os
import pandas as pd
import requests
import time
import random
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from dotenv import load_dotenv
from langcodes import Language, tag_distance, LanguageTagError, standardize_tag
from datetime import datetime

BASE_INPUT_DIR = "input"
BASE_OUTPUT_DIR = "output"

load_dotenv(override=True)

class WebPageLangAuditor:
    def __init__(self, input_path, output_path):
        self.column_names = ["response_status", "current_url", "html_lang_raw", "lang_extracted", "sp_pop", "lang_detected", "match_found", "iana_valid", "status", "recommendation"]
        self.input_file_path = input_path
        self.output_folder_path = output_path
        self.csv_data = None
        self.raw_results = []
        self.timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")

    def get_technical_advice_red(self, match, iana_valid, html_lang_raw):
        """
        Determines Status and provides a Recommendation.
        """
        recommendation = None
        status = "Manual Check"
        try:
            if not html_lang_raw:
                status, recommendation = "Critical", "HTML lang attribute is missing."
            elif not match:
                status, recommendation = "Critical", "The detected text language does not match the HTML tag."
            
            elif html_lang_raw != html_lang_raw.strip():
                normalized = standardize_tag(html_lang_raw)
                status, recommendation = "Fix", f"Syntax error (whitespace). Change '{html_lang_raw}' to '{normalized}'"
            # 3️⃣ IANA / BCP 47 invalid
            elif not iana_valid:
                normalized = standardize_tag(html_lang_raw)
                status, recommendation = "Fix", f"Invalid BCP 47 syntax. Change '{html_lang_raw}' to '{normalized}'"
            elif iana_valid:
                normalized = standardize_tag(html_lang_raw)
                if html_lang_raw != normalized:
                    status, recommendation = "Keep", f"Valid, but standard suggests '{normalized}'"
                else:
                    
                    status, recommendation = "Keep", "Perfect"
        except Exception as e:
            status = "Error"
            recommendation = f"Exception occurred: {type(e).__name__}"
        else:
            print(f"Audit successful for: {html_lang_raw}")
        finally:
            return status, recommendation


    def get_url_lang_data_langcodes(self, url: str):
        current_url = url
        html_lang_raw = lang_extracted = lang_detected = sp_pop = response_status = lang_obj = None
        match_found, iana_valid = False, False
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            current_url = response.url
            response_status = f"{response.status_code}{'_redirected' if len(response.history) > 0 else ''}"
            if response.text:
                soup = BeautifulSoup(response.text, "html.parser")
                html_tag = soup.find("html")
                if html_tag and html_tag.has_attr("lang"):
                    html_lang_raw = html_tag.get("lang", "") 
                    try:
                        lang_obj = Language.get(html_lang_raw, normalize=False)
                        iana_valid = lang_obj.is_valid()
                        lang_extracted = lang_obj.language 
                    except (LanguageTagError, Exception):
                        iana_valid, lang_extracted = False, "invalid"

                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                text = soup.get_text(separator=" ", strip=True)
                if len(text) < 50:
                    lang_detected, match_found = "insufficient_text", False
                else:
                    try:
                        lang_detected = detect(text).lower()
                        print(lang_detected, "lang detected")
                        try:
                            dist = tag_distance(html_lang_raw, lang_detected)
                            print(f"dist: {dist}, html_lang_raw: {html_lang_raw}, lang_detected: {lang_detected}")
                            if dist<10:
                                match_found = True
                            else:
                                match_found = False
                        except Exception:
                            match_found = (lang_extracted == lang_detected)
                    except LangDetectException:
                        lang_detected, match_found = "detection_error", False
                status, recommendation = self.get_technical_advice_red(match_found, iana_valid, html_lang_raw)
                try:
                    sp_pop = Language.get(html_lang_raw, normalize=True).speaking_population()
                except Exception:
                    sp_pop = None
                return (response_status, current_url, html_lang_raw, lang_extracted, sp_pop, lang_detected, 
                        match_found, iana_valid, status, recommendation)
        except Exception as e:
            return (str(type(e).__name__), url, "Error html_lang_raw", "Error lang_extracted","Error sp_pop",  "Error lang_detected", False, False, "Error Status", "Error recommendation")

    def read_input_csv_file(self):
        if not os.path.exists(self.input_file_path):
            raise FileNotFoundError(
                f"Input file not found: {self.input_file_path}"
        )
        print(f"Starting Professional Throttled Audit on: {self.input_file_path}")
        csv_df = pd.read_csv(self.input_file_path)
        if 'url' not in csv_df.columns:
            return "Error: CSV must have a 'url' column."
        self.csv_data = csv_df

    def run_web_lang_auditor(self):
        csv_df = self.csv_data
        total = len(csv_df)
        for index, row in csv_df.iterrows():
            url = row['url']
            print(f"Progress: [{index + 1}/{total}] Processing: {url}")
            res = self.get_url_lang_data_langcodes(url)
            self.raw_results.append(res)
            if index < total - 1: 
                delay = random.uniform(1.0, 2.5)
                time.sleep(delay)
    
    def generate_csv_file_pd_data(self):
        results_df = pd.DataFrame(self.raw_results, columns=self.column_names)
        self.final_df = pd.concat([self.csv_data.reset_index(drop=True), results_df], axis=1)

    def write_output_file(self):
        output_path = os.path.join(self.output_folder_path, f'{self.timestamp}_result.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.final_df.to_csv(output_path, index=False)
        print(f"Audit Complete. Results: {output_path}")
    
    def run_full_audit(self):
        self.read_input_csv_file()
        self.run_web_lang_auditor()
        self.generate_csv_file_pd_data()
        self.write_output_file()

if __name__ == "__main__":
    html_lang_auditor = WebPageLangAuditor(
        "input/20260119_all_sope.csv",
        "output"
    )
    html_lang_auditor.run_full_audit()




