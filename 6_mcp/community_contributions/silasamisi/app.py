import asyncio
import gradio as gr
from dotenv import load_dotenv
from coach import Coach

load_dotenv(override=True)

cv = """
Name:Silas A. Wawire
Address: Nairobi, Kenya • 
Phone: +254724086803 • 
Email:swawire@gmail.com

Highly skilled and results-oriented trainer with years of experience in teaching and mentoring learners in areas of technology, specifically telecommunications and IT. Adept at designing and delivering comprehensive curriculum, instructing and mentoring students, supervising projects, and assessing learners.  
Experience
JAN 2022 – PRESENT
Lecturer | Oshwal College | Nairobi, Kenya
•	Designed and delivered comprehensive curriculum for information technology and telecommunications. 
•	Instructed students on the practical application of IT for real-world problem-solving.
•	Mentored students on networks, sensors, programming, project management, data analysis, AI model development, and evaluation techniques.
•	Supervised student projects.
•	Contributed to the development of engaging learning materials and assessments to enhance student comprehension and practical skills in IT.
JUN 2020 – JAN 2022
Artificial Intelligence Researcher | JKUAT | Nairobi, Kenya
•	Applied data mining techniques and conducted statistical analysis on large, structured and unstructured datasets to derive insights and opportunities.
•	Modeled business problems using statistical, algorithmic, machine learning, and visualization techniques, collaborating closely with clients and data teams.
•	Performed comprehensive data pre-processing, including manipulation, transformation, normalization, standardization, and feature engineering for Data Science models.
•	Utilized advanced data analytics and mining techniques to analyze data, ensuring data validity and usability, and effectively communicated results to stakeholders.
APR 2017 – FEB 2020
Cooperative Bank of Kenya | IT Support | Nairobi, Kenya
•	Provided technical support for banking systems and applications, resolving hardware and software issues to ensure continuous operational efficiency.
•	Managed user accounts and access permissions, adhering to strict data security and compliance protocols.
•	Assisted in maintaining data integrity and availability by performing regular data backups and system checks.
•	Collaborated with cross-functional teams to diagnose and resolve complex IT problems, minimizing system downtime.
•	Documented IT procedures and troubleshooting guides, improving internal knowledge sharing and support efficiency.
FEB 2013 – MAR 2017
Cooperative Bank of Kenya | Graduate Clerk | Nairobi, Kenya
•	Telling (Executive/Forex/Rtgs/Swift/Western Union and MoneyGram teller)
•	Customer service and inquiries
•	Accounts opening
•	ATM custodian
•	Bank accounts and cash reconciliations
•	Know Your Customer (KYC) and Anti-Money Laundering (AML) compliant
Projects
A distributed framework for distributed denial-of-service attack detection in internet of things environments using deep learning 
•	Developed a DDoS detection framework based on the CNN-BILSTM model, designed for distributed network deployment with robust pre-processing capabilities. Published in Inderscience: https://www.inderscience.com/info/inarticle.php?artid=138107
Education
DEC 2016
MSc Computer Systems | JKUAT| Nairobi, Kenya
DEC 2010
BSc Telecommunications and Information Technology | Kenyatta University| Nairobi, Kenya
Certifications
•	AWS Cloud Practitioner: Ongoing
•	AWS Certified Solutions Architect: Ongoing
•	ICDL: May 2025
•	CCNA: Jun 2018
Skills
•	Programming Languages: Python, R, PHP, SQL, MongoDB
•	Machine Learning Frameworks: Scikit-learn, TensorFlow, PyTorch
•	MLOps & Deployment: AWS, Docker, Kubernetes, CI/CD
•	Natural Language Processing (NLP): Question Answering, Summarization, Data Preprocessing, Web Scraping
•	Data Analysis & Modeling: Predictive Analytics, Statistical Modeling, Data Mining, Data Visualization, Hyperparameter Optimization, Cross-validation
•	Core Concepts: Data Structures, Algorithms, Model Optimization Techniques, Deep Learning, Computer Vision
•	IT Support & Data Stewardship: Technical Support, System Troubleshooting, Data Security, Data Integrity, Access Management, Documentation
•	Soft Skills: Collaboration, Problem-Solving, Technical Documentation, Research, Rapid Prototyping, Curriculum Development, Mentorship
Referees
•	Available upon request
"""


async def run_coach(job_url: str) -> str:
    if not job_url.strip():
        return "Please enter a job posting URL."
    coach = Coach(cv=cv)
    result = await coach.run(job_url=job_url.strip())
    return result


def run_coach_sync(job_url: str) -> str:
    return asyncio.run(run_coach(job_url))


with gr.Blocks(title="Job Application Coach") as app:
    gr.Markdown("# Job Application Coach")
    gr.Markdown("Paste a job posting URL below. The coach will fetch the job, tailor your CV, write a cover letter, and save the application.")

    with gr.Row():
        job_url_input = gr.Textbox(
            label="Job Posting URL",
            placeholder="https://boards.greenhouse.io/company/jobs/123456",
            scale=4
        )
        submit_btn = gr.Button("Run Coach", variant="primary", scale=1)

    output = gr.Markdown(label="Result")

    submit_btn.click(
        fn=run_coach_sync,
        inputs=[job_url_input],
        outputs=[output]
    )

if __name__ == "__main__":
    app.launch()
