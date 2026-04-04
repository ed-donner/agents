#import "@preview/basic-resume:0.2.8": *
#import "@preview/fontawesome:0.6.0": *

#let name = "Martins AWOJIDE"
#let location = "68 Peregrine Drive, Great Warley, Brentwood, Essex, CM13 3GW"
#let email = "awojidemartins@gmail.com"
#let phone = "+250 (798) 694-256"

#show: resume.with(
  author: name,
  location: location,
  email: email,
  phone: phone,
  accent-color: "#26428b",
  font: "New Computer Modern",
  paper: "us-letter",
  author-position: center,
  personal-info-position: center,
)

== Professional Work Experience

#work(
  title: "Decision Intelligence Analyst",
  location: "Lagos, NGA",
  company: "Dufil Prima Foods Plc",
  dates: dates-helper(start-date: "Dec 2021", end-date: "Apr 2022"),
)

_Handled Business Intelligence tasks and Process Improvement Strategy for the Head of Continuous Improvement & Sustainability and the C-suite at Group Corporate HQ._
- Analyzed financial and operational data to identify key areas for process enhancement and support Six Sigma initiatives.
- Led feasibility studies and developed entry strategies for new business opportunities in Nigerian agriculture, consumer, and financial markets.
- Spearheaded internal improvement projects and led a think tank for new business exploration.

#work(
  title: "Operations Manager, Warehousing and Logistics",
  location: "Kaduna, NGA",
  company: "Dufil Prima Foods Plc",
  dates: dates-helper(start-date: "Jan 2021", end-date: "Nov 2021"),
)

_Managed a department of 140+ personnel to achieve seamless warehousing operations and integration with other departments._
- Implemented Kanban concepts to enhance document flow, improving OTDIF by *84%*.
- Achieved *zero* non-conformance in ISO 22000 and ISO 9001:2015 audits, with commendations on reporting and traceability improvements.
- Reduced Warehouse/Logistics downtime from *0.85%* to *0.42%* YTD, enhancing capacity utilization.
- Decreased truck turnaround time by *57%* through ETA tracking and SMED implementation.
- Restructured the department, leading to improved resource utilization and transition from Orion ERP to SAP.

#work(
  title: "Data Scientist, Industrial Optimization",
  location: "Lagos & Kaduna, NGA",
  company: "Dufil Prima Foods Plc",
  dates: dates-helper(start-date: "Dec 2018", end-date: "Dec 2020"),
)

_Black Belt Project Facilitator focused on process improvement in production settings._
- Reduced Noodle Block Fat Content from *17.0%* to *16.5%* for various SKUs using Expanded MSA.
- Developed a low-code software for paperless reporting, cutting consumables cost by *95%*.
- Led a DMAIC project reducing laminate variance, saving *\$53,900* in the first year and *\$88,800* annually thereafter.
- Managed a Lean project improving packaging reliability, reducing leakage, and saving *\$7,500* annually.
- Trained 40+ staff on 5S, Lean Six Sigma, and mentored new facilitators on improvement projects.

== Education

#edu(
  institution: "Carnegie Mellon University",
  location: "Pennsylvania, USA",
  dates: dates-helper(start-date: "Aug 2023", end-date: "May 2025"),
  degree: "Master of Science, Engineering Artificial Intelligence (with Distinction)",
)
- Cumulative GPA: 3.75\/4.0 | Mastercard Foundation Scholarship
- Relevant Coursework: On-Device Machine Learning, Deep Learning, Machine Learning for Engineers, AI System Design, Embedded System Development, Systems Software Engineering, Mobile Big Data Analytics & Management, Cloud Computing

#edu(
  institution: "University of Lagos",
  location: "Lagos, NGA",
  degree: "Bachelor of Science, Chemical Engineering (with First Class Honours)",
)
- Cumulative GPA: 4.74\/5.0 | Top 10% of ChE Class, Society of Petroleum Engineers Star Scholarship, MTN Foundation Scholarship

== Training and Certifications

#certificates(
  name: "Design for Six Sigma (DFSS) Training",
  issuer: "Benchmark X 360",
  date: "Jan 2021",
)

#certificates(
  name: "Lean Six Sigma Black Belt",
  issuer: "Benchmark X 360",
  date: "Feb 2020",
)
- _Batch Topper, LSSBB Mumbai '20 Cohort_ #link("https://www.benchmarksixsigma.com/forum/all-time-lean-six-sigma-black-belt-top-scorers/")[#fa-icon("up-right-from-square", solid: true, fill: blue)]

== Skills

- *Data Analysis*: Excel, Python, Pandas, SQL, Git, PySpark, PyTorch, Docker, AWS, Google AppSheet, Minitab, Tableau
- *Programming Languages*: Python, C/C++, Bash
- *Technologies*: Git, PySpark, Flask, PyTorch, TensorFlow, Docker, AWS, GCP, AppSheet, Edge Impulse
- *Application*: Minitab, Quality Companion, Google AppSheet, Jira, Trello, Linear, MS Planner, MS Excel