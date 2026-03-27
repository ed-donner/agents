from database import (
    list_evaluations,
    list_job_posts,
    list_notifications,
    list_pending_evaluations,
    list_unevaluated_job_posts,
    read_applicant,
    read_job_post,
    read_job_post_evaluation,
    read_notification,
    write_applicant,
    write_evaluation,
    write_job_post,
    write_log,
    write_notification,
)
from pydantic import BaseModel, Field
from schema import Evaluation, Evaluations, JobPost, JobPosts, Notification, Notifications


class Applicant(BaseModel):
    name: str = Field(description="The name of the applicant")
    summary: str = Field(description="The summary of the applicant")

    @classmethod
    def get(cls, name: str):
        fields = read_applicant(name.lower())
        if not fields:
            fields = {
                "name": name.lower(),
                "summary": "",
            }
            write_applicant(name, fields)
        return cls(**fields)

    def __str__(self):
        return f"{self.summary}"

    def __repr__(self):
        return f"{self.summary}"

    def save(self):
        write_applicant(self.name.lower(), self.model_dump())

    def set_summary(self, summary: str):
        """
        Set the summary of the applicant and save it to the database.

        Args:
            summary (str): The summary of the applicant
        """
        self.summary = summary
        self.save()

    def save_job_post(self, job_post: JobPost):
        """
        Save the job post to the database.
        """
        post = write_job_post(job_post)
        write_log("applicant", "save_job_post", "Saved job post to the database.")
        return post

    def list_job_posts(self) -> JobPosts:
        """
        List the job posts from the database.
        """
        return list_job_posts()

    def read_job_post(self, job_post_id: int) -> JobPost | None:
        """
        Read the job post from the database.
        """
        return read_job_post(job_post_id)

    def save_evaluation(self, evaluation: Evaluation):
        """
        Save an evaluation of a job post to the database.
        """
        write_evaluation(evaluation)
        write_log("applicant", "save_evaluation", f"Saved evaluation for job post {evaluation.job_post_id}.")

    def get_evaluation(self, job_post_id: int) -> Evaluation | None:
        """
        Read an evaluation for a job post from the database.
        """
        return read_job_post_evaluation(job_post_id)

    def list_evaluations(self) -> Evaluations:
        """
        List all evaluations from the database.
        """
        return list_evaluations()

    def save_notification(self, notification: Notification) -> None:
        """
        Save a notification record to the database.
        """
        write_notification(notification)
        write_log("applicant", "save_notification", f"Saved notification for evaluation {notification.evaluation_id}.")

    def get_notification(self, evaluation_id: int) -> Notification | None:
        """
        Read a notification record by evaluation_id.
        """
        return read_notification(evaluation_id)

    def list_notifications(self) -> Notifications:
        """
        List all notification records from the database.
        """
        return list_notifications()

    def list_pending_evaluations(self) -> Evaluations:
        """
        List acceptable evaluations that have not yet had a notification sent.
        """
        return list_pending_evaluations()

    def list_unevaluated_job_posts(self) -> JobPosts:
        """
        List job posts that have not yet been evaluated.
        """
        return list_unevaluated_job_posts()
