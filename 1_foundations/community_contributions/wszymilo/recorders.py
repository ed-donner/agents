import logging
import os
import sqlite3
import threading

from openai import pydantic_function_tool
from pydantic import BaseModel, Field
import requests


class RecordUserDetailsSchema(BaseModel):
    email: str = Field(..., description="The email address of this user")
    name: str = Field(
        description="The user's name, if they provided it", default="Name not provided")
    notes: str = Field(
        description="Any additional information about the conversation that's worth recording to give context", default="not provided")


class RecordUnknownQuestionSchema(BaseModel):
    question: str = Field(...,
                          description="The question that couldn't be answered")


class CheckQuestionAnsweredSchema(BaseModel):
    pass


class BaseRecorder:
    """Base for recorders that expose record_user_details, record_unknown_question and a tools registry for the chatbot."""

    def __init__(self):
        self._tools_registry = self._build_tools_registry()

    def _build_tools_registry(self):
        """Return a dict of tool_name -> {json, class, name, function}. Subclasses must implement."""
        raise NotImplementedError

    @property
    def tools_registry(self):
        return self._tools_registry

    @property
    def tools(self):
        return [t["json"] for t in self._tools_registry.values()]


class DB(BaseRecorder):
    def __init__(self):
        self.db = sqlite3.connect("me/db.sqlite3", check_same_thread=False)
        self.cursor = self.db.cursor()
        self._write_lock = threading.Lock()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_details (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, name TEXT, notes TEXT)")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS unknown_questions (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL, answer TEXT DEFAULT '')")
        self.db.commit()
        super().__init__()

    def record_user_details(self, email, name="Name not provided", notes="not provided"):
        """Records that a user is interested in being in touch and provided notes and an email address"""
        if not email:
            raise ValueError("Email is required")
        email = email.strip()[:50]
        name = name.strip()[:50]
        notes = notes.strip()[:150]
        with self._write_lock:
            self.cursor.execute(
                "INSERT INTO user_details (email, name, notes) VALUES (?, ?, ?)", (email, name, notes))
            self.db.commit()
        return {"recorded": "ok"}

    def record_unknown_question(self, question):
        """Records any question that couldn't be answered as you didn't know the answer"""
        if not question:
            raise ValueError("Question is required")
        question = question.lower().strip()[:150]
        with self._write_lock:
            # Check if the question already exists (case-insensitive)
            self.cursor.execute(
                "SELECT 1 FROM unknown_questions WHERE LOWER(question) = ?", (question,))
            exists = self.cursor.fetchone()
            if not exists:
                self.cursor.execute(
                    "INSERT INTO unknown_questions (question, answer) VALUES (?, ?)", (question, ""))
                self.db.commit()
                return {"recorded": "ok"}
            else:
                return {"not recorded": "question already stored - use get_answered_questions to get all questions that have been answered already"}

    def get_answered_questions(self):
        """Returns all questions with answers."""
        self.cursor.execute(
            "SELECT question, answer FROM unknown_questions WHERE answer != ''")
        questions = self.cursor.fetchall()
        return [{"question": q, "answer": a} for q, a in questions]

    def _build_tools_registry(self):
        return {
            "record_user_details": {
                "json": pydantic_function_tool(
                    RecordUserDetailsSchema,
                    name="record_user_details",
                    description=self.record_user_details.__doc__,
                ),
                "class": RecordUserDetailsSchema,
                "name": "record_user_details",
                "function": self.record_user_details,
            },
            "record_unknown_question": {
                "json": pydantic_function_tool(
                    RecordUnknownQuestionSchema,
                    name="record_unknown_question",
                    description=self.record_unknown_question.__doc__,
                ),
                "class": RecordUnknownQuestionSchema,
                "name": "record_unknown_question",
                "function": self.record_unknown_question,
            },
            "get_answered_questions": {
                "json": pydantic_function_tool(
                    CheckQuestionAnsweredSchema,
                    name="get_answered_questions",
                    description=self.get_answered_questions.__doc__,
                ),
                "class": CheckQuestionAnsweredSchema,
                "name": "get_answered_questions",
                "function": self.get_answered_questions,
            },
        }


class ContactRecorder(BaseRecorder):
    """Handles Pushover notifications and recording user interest / unknown questions for the chatbot."""

    PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self):
        self._token = os.getenv("PUSHOVER_TOKEN")
        self._user = os.getenv("PUSHOVER_USER")
        self._logger = logging.getLogger(__name__)
        super().__init__()

    def _build_tools_registry(self):
        return {
            "record_user_details": {
                "json": pydantic_function_tool(
                    RecordUserDetailsSchema,
                    name="record_user_details",
                    description=self.record_user_details.__doc__,
                ),
                "class": RecordUserDetailsSchema,
                "name": "record_user_details",
                "function": self.record_user_details,
            },
            "record_unknown_question": {
                "json": pydantic_function_tool(
                    RecordUnknownQuestionSchema,
                    name="record_unknown_question",
                    description=self.record_unknown_question.__doc__,
                ),
                "class": RecordUnknownQuestionSchema,
                "name": "record_unknown_question",
                "function": self.record_unknown_question,
            },
        }

    def push(self, text):
        requests.post(
            self.PUSHOVER_URL,
            data={
                "token": self._token,
                "user": self._user,
                "message": text,
            },
            timeout=5,
        )

    def record_user_details(self, email, name="Name not provided", notes="not provided"):
        """Records that a user is interested in being in touch and provided an email address"""
        self.push(
            f"Recording interest from '{name}' with email '{email}' and notes '{notes}'")
        self._logger.info(
            "Recording interest from '%s' with email '%s' and notes '%s'", name, email, notes)
        return {"recorded": "ok"}

    def record_unknown_question(self, question):
        """Records any question that couldn't be answered as you didn't know the answer"""
        if question and question != "not provided":
            self.push(f"Recording question: {question} that I couldn't answer")
            self._logger.info(
                "Recording question: '%s' that I couldn't answer", question)
        else:
            self._logger.warning("Question is not provided")
        return {"recorded": "ok"}


class CompositeRecorder(BaseRecorder):
    """Delegates to both ContactRecorder (push) and DB (persist). Use when you want both notification and storage."""

    def __init__(self, contact_recorder=None, db=None):
        self._contact = contact_recorder or ContactRecorder()
        self._db = db or DB()
        super().__init__()

    def record_user_details(self, email, name="Name not provided", notes="not provided"):
        """Records that a user is interested in being in touch and provided an email address"""
        self._contact.record_user_details(email, name=name, notes=notes)
        self._db.record_user_details(email, name=name, notes=notes)
        return {"recorded": "ok"}

    def record_unknown_question(self, question):
        """Records any question that couldn't be answered as you didn't know the answer"""
        self._contact.record_unknown_question(question)
        return self._db.record_unknown_question(question)

    def get_answered_questions(self):
        """Returns all questions with answers."""
        return self._db.get_answered_questions()

    def _build_tools_registry(self):
        return {
            "record_user_details": {
                "json": pydantic_function_tool(
                    RecordUserDetailsSchema,
                    name="record_user_details",
                    description=self.record_user_details.__doc__,
                ),
                "class": RecordUserDetailsSchema,
                "name": "record_user_details",
                "function": self.record_user_details,
            },
            "record_unknown_question": {
                "json": pydantic_function_tool(
                    RecordUnknownQuestionSchema,
                    name="record_unknown_question",
                    description=self.record_unknown_question.__doc__,
                ),
                "class": RecordUnknownQuestionSchema,
                "name": "record_unknown_question",
                "function": self.record_unknown_question,
            },
            "get_answered_questions": {
                "json": pydantic_function_tool(
                    CheckQuestionAnsweredSchema,
                    name="get_answered_questions",
                    description=self.get_answered_questions.__doc__,
                ),
                "class": CheckQuestionAnsweredSchema,
                "name": "get_answered_questions",
                "function": self.get_answered_questions,
            },
        }
