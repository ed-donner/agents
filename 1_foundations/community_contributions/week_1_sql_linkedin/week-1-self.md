# Q&A Database Schema and Example

## ✅ 1. Create the Table

```sql
CREATE TABLE qa (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
);


INSERT INTO qa (question, answer) VALUES
('What are your hobbies ?', 'playing guitar');


SELECT * FROM qa;



---

### ✅ Save this as `qa.md`.

When viewed in a Markdown viewer, it will display nicely formatted code blocks and a table.

Would you like me to export this into an actual `.md` file for you?
