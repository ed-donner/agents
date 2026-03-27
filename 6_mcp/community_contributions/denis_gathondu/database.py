import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from schema import Evaluation, Evaluations, JobPost, JobPosts

load_dotenv(override=True)
BASE_URL = Path(__file__).resolve().parent
DB = os.path.abspath(os.path.join(BASE_URL, "sandbox", "applicant.db"))


with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS applicants (name TEXT PRIMARY KEY, summary TEXT)"
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_posts (
            id INTEGER PRIMARY KEY,
            title TEXT,
            company_name TEXT,
            company_url TEXT,
            location TEXT,
            salary_range TEXT,
            job_description TEXT,
            job_requirements TEXT,
            technologies_needed TEXT,
            must_have_skills TEXT,
            link_to_job_posting TEXT,
            job_post_date TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_acceptable BOOLEAN,
            job_post_id INTEGER REFERENCES job_posts(id),
            feedback TEXT
        )
        """
    )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            datetime DATETIME,
            type TEXT,
            message TEXT
        )
    """)
    conn.commit()


def write_applicant(name: str, applicant_dict: dict[str, Any]):
    """
    Write an applicant to the applicants table.

    Args:
        name (str): The name of the applicant to write
        applicant_dict (dict[str, Any]): The applicant dictionary to write
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO applicants (name, summary) VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET summary=excluded.summary
            """,
            (name.lower(), json.dumps(applicant_dict)),
        )
        conn.commit()


def read_applicant(name: str):
    """
    Read an applicant from the applicants table.

    Args:
        name (str): The name of the applicant to read

    Returns:
        Applicant: The applicant object
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM applicants WHERE name = ?", (name.lower(),))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None


def write_job_post(job_post: JobPost):
    """
    Write a job post to the job_posts table.

    Args:
        job_post (JobPost): The job post to write
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO job_posts (id, title, company_name, company_url, location, salary_range, job_description, job_requirements, technologies_needed, must_have_skills, link_to_job_posting, job_post_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET id=excluded.id,title=excluded.title, company_name=excluded.company_name, company_url=excluded.company_url, location=excluded.location, salary_range=excluded.salary_range, job_description=excluded.job_description, job_requirements=excluded.job_requirements, technologies_needed=excluded.technologies_needed, must_have_skills=excluded.must_have_skills, link_to_job_posting=excluded.link_to_job_posting, job_post_date=excluded.job_post_date
        """,
            (
                job_post.id,
                job_post.title,
                job_post.company_name,
                job_post.company_url,
                job_post.location,
                job_post.salary_range,
                job_post.job_description,
                job_post.job_requirements,
                job_post.technologies_needed,
                job_post.must_have_skills,
                job_post.link_to_job_posting,
                job_post.job_post_date,
            ),
        )
        conn.commit()


def read_job_post(id: int) -> JobPost | None:
    """
    Read a job post from the job_posts table.

    Args:
        id (int): The id of the job post to read
    """
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_posts WHERE id = ?", (id,))
        row = cursor.fetchone()
        return JobPost(**row) if row else None


def list_job_posts() -> JobPosts:
    """
    List all job posts from the job_posts table.

    Returns:
        JobPosts: A list of JobPost objects
    """
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_posts")
        rows = cursor.fetchall()
        return JobPosts(job_posts=[JobPost(**row) for row in rows])


def write_evaluation(evaluation: Evaluation):
    """
    Write an evaluation to the evaluations table.

    Args:
        evaluation (Evaluation): The evaluation to write
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evaluations (is_acceptable, feedback, job_post_id)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET is_acceptable=excluded.is_acceptable, feedback=excluded.feedback, job_post_id=excluded.job_post_id
        """,
            (evaluation.is_acceptable, evaluation.feedback, evaluation.job_post_id),
        )
        conn.commit()


def read_job_post_evaluation(job_post_id: int) -> Evaluation | None:
    """
    Read an evaluation from the evaluations table.

    Args:
        job_post_id (int): The id of the job post to read

    Returns:
        Evaluation: The evaluation object
    """
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM evaluations WHERE job_post_id = ?", (job_post_id,)
        )
        row = cursor.fetchone()
        return Evaluation(**row) if row else None


def list_evaluations() -> Evaluations:
    """
    List all evaluations from the evaluations table.

    Returns:
        Evaluations: A list of Evaluation objects
    """
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluations")
        rows = cursor.fetchall()
        return Evaluations(evaluations=[Evaluation(**row) for row in rows])


def list_positive_evaluations() -> Evaluations:
    """
    List all positive evaluations from the evaluations table.

    Returns:
        Evaluations: A list of Evaluation objects
    """
    evaluations = list_evaluations()
    return Evaluations(
        evaluations=[
            evaluation
            for evaluation in evaluations.evaluations
            if evaluation.is_acceptable
        ]
    )


def list_negative_evaluations() -> Evaluations:
    """
    List all negative evaluations from the evaluations table.

    Returns:
        Evaluations: A list of Evaluation objects
    """
    evaluations = list_evaluations()
    return Evaluations(
        evaluations=[
            evaluation
            for evaluation in evaluations.evaluations
            if not evaluation.is_acceptable
        ]
    )


def write_log(name: str, type: str, message: str):
    """
    Write a log entry to the logs table.

    Args:
        name (str): The name associated with the log
        type (str): The type of log entry
        message (str): The log message
    """
    now = datetime.now().isoformat()

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
        """,
            (name.lower(), type, message),
        )
        conn.commit()


def read_log(name: str, last_n=10):
    """
    Read the most recent log entries for a given name.

    Args:
        name (str): The name to retrieve logs for
        last_n (int): Number of most recent entries to retrieve

    Returns:
        list: A list of tuples containing (datetime, type, message)
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT datetime, type, message FROM logs 
            WHERE name = ? 
            ORDER BY datetime DESC
            LIMIT ?
        """,
            (name.lower(), last_n),
        )

        return reversed(cursor.fetchall())
