from pydantic import BaseModel, Field
import json

class Director(BaseModel):
    name: str
    born: int

class Movie(BaseModel):
    title: str = Field(..., description="The title of the movie", max_length=100)
    year: int = Field(..., description="The year the movie was released")
    generes: list[str] = Field(..., description="The genres of the movie")
    director: Director = Field(..., description="The director of the movie")
    duration_minutes: int = Field(..., description="The duration of the movie in minutes")
    rating: float = Field(default=5.0, ge=0, le=10)




json_string = '{"title": "Titanic", "year": 1997, "generes": ["Drama", "Romance", "Thriller"], "director": {"name": "James Cameron", "born": 1954}, "duration_minutes": 195, "rating": 7.8}'
data = json.loads(json_string)
favorite_movie = Movie(**data)

movie_dict = {"title": "Gladiator", "year": 2000, "generes": ["Drama", "Action", "Thriller"],
 "duration_minutes": 155, "rating": 8.5, "director": {"name": "Ridley Scott", "born": 1937}}
another_movie = Movie(**movie_dict)

print(favorite_movie)