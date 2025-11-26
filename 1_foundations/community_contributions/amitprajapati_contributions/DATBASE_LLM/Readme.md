# LLM-Powered SQL Assistant for the Company Transactions Database

This project demonstrates how to use a Large Language Model (LLM) as a **natural language interface** to a relational SQL database. The system allows users to ask questions such as:

> "Which country has the highest transaction amount?"

The application will:

1. Convert the natural language question into an SQL query  
2. Execute the SQL query on the database  
3. Feed the result back to the LLM  
4. Produce a clean, human-friendly explanation  

This project shows how LLMs can act as reasoning engines and SQL copilots for structured data analytics.

---

## 🚨 IMPORTANT: Run `company.sql` First

Before using the notebook or any Python script:

### **You MUST load the database by running `company.sql` first.**

Example:

```bash
mysql -u <user> -p -h <host> <database_name> < company.sql
