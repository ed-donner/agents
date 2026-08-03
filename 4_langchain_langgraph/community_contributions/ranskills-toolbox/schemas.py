from pydantic import BaseModel, Field
from typing import Literal, TypeAlias


Intent: TypeAlias = Literal['research', 'coding', 'unknown']


class IntentClassification(BaseModel):
    intent: Intent = Field(description="The classified intent of the user's request")


class SearchQuery(BaseModel):
    query: str
    reason: str


class SearchQueryList(BaseModel):
    topic: str
    rephrased_topic: str | None
    items: list[SearchQuery]


class EvaluatedSearchQuery(BaseModel):
    query: str
    relevance: int = Field(description='A score of 0 to 5')
    actionability: int = Field(description='A score of 0 to 5')
    specificity: int = Field(description='A score of 0 to 5')
    feedback: str | None = Field(description='An optional feedback on the query')

    @classmethod
    def create_from_query(cls, query: SearchQuery):
        return cls(query=query.query, relevance=0, actionability=0, specificity=0, feedback=None)


class EvaluatedSearchQueryList(BaseModel):
    items: list[EvaluatedSearchQuery]

    @classmethod
    def create_from_queries(cls, queries: list[SearchQuery]):
        return cls(items=[cls.create_from_query(query) for query in queries])
