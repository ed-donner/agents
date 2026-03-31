import os
from typing import Annotated

from dotenv import find_dotenv, load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


load_dotenv(find_dotenv())


mcp = FastMCP(name="cat_server")

Score = Annotated[int, Field(ge=0, le=5)]
OptScore = Annotated[Score | None, Field(default=None)]
OptStr = Annotated[str | None, Field(default=None)]
OptUrl = Annotated[HttpUrl | str | None, Field(default=None)]


class CatBreed(BaseModel):
    """Breed payload shape from The Cat API `/v1/breeds` (example: American Bobtail)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    class Weight(BaseModel):
        imperial: str
        metric: str

    class Image(BaseModel):
        id: str
        width: int
        height: int
        url: HttpUrl

    name: str = Field(description="The name of the breed")
    id: str = Field(description="The ID of the breed")
    name: str = Field(description="The name of the breed")

    weight: Weight = Field(description="The weight of the breed")

    image: Annotated[Image | None, Field(description="The image of the breed", default=None)]

    experimental: bool = Field(description="Whether the breed is experimental", default=False)
    hairless: bool = Field(description="Whether the breed is hairless", default=False)
    hypoallergenic: bool = Field(description="Whether the breed is hypoallergenic", default=False)
    indoor: bool = Field(description="Whether the breed is indoor", default=False)
    lap: bool = Field(description="Whether the breed is lap", default=False)
    natural: bool = Field(description="Whether the breed is natural", default=False)
    rare: bool = Field(description="Whether the breed is rare", default=False)
    rex: bool = Field(description="Whether the breed is rex", default=False)
    short_legs: bool = Field(description="Whether the breed is short legs", default=False)
    suppressed_tail: bool = Field(description="Whether the breed is suppressed tail", default=False)

    adaptability: OptScore = Field(description="The adaptability score of the breed")
    affection_level: OptScore = Field(description="The affection level score of the breed")
    child_friendly: OptScore = Field(description="The child friendly score of the breed")
    dog_friendly: OptScore = Field(description="The dog friendly score of the breed")
    energy_level: OptScore = Field(description="The energy level score of the breed")
    grooming: OptScore = Field(description="The grooming score of the breed")
    health_issues: OptScore = Field(description="The health issues score of the breed")
    intelligence: OptScore = Field(description="The intelligence score of the breed")
    shedding_level: OptScore = Field(description="The shedding level score of the breed")
    social_needs: OptScore = Field(description="The social needs score of the breed")
    stranger_friendly: OptScore = Field(description="The stranger friendly score of the breed")
    vocalisation: OptScore = Field(description="The vocalisation score of the breed")

    alt_names: OptStr = Field(description="The alternative names of the breed")
    country_code: OptStr = Field(description="The country code of the breed")
    description: OptStr = Field(description="The description of the breed")
    life_span: OptStr = Field(description="The life span of the breed")
    origin: OptStr = Field(description="The origin of the breed")
    reference_image_id: OptStr = Field(description="The reference image ID of the breed")
    temperament: OptStr = Field(description="The temperament of the breed")

    wikipedia_url: OptUrl = Field(description="The Wikipedia URL of the breed")



class SearchResponse(BaseModel):
    image_id: str = Field(description="The ID of the image")
    image_url: HttpUrl = Field(description="The URL of the image")
    breed: CatBreed | None = Field(description="The breed of the cat", default=None)
    

BASE_URL = 'https://api.thecatapi.com/v1'
HEADERS = {
    'x-api-key': os.getenv('CAT_API_KEY'),
    'User-Agent': 'CatServer/1.0'
}

BREEDS_CACHE = {}

@mcp.tool()
async def get_cat_image_url(breed_id: str | None = None) -> SearchResponse | dict[str, str]:
    """Get image URL of a cat from the Cat API. If breed_id is provided, returns the image URL of the cat of the breed.

    Args:
        breed_id: The ID of the breed to get information about. If not provided, a random cat will be returned.
    
    Returns:
        A SearchResponse object containing cat's image id, url and an optional breed information.
    """
    global BREEDS_CACHE
    

    if breed_id:
        breed_id = breed_id.lower()
        breed = BREEDS_CACHE.get(breed_id, None)
        if breed:
            breed_id = breed.id

    url = f'/images/search?breed_id={breed_id}' if breed_id else '/images/search'
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        cat_data = response.json()[0]
        if cat_data['breeds'] and len(cat_data['breeds']) == 1:
            breed_name = cat_data['breeds'][0]['name'].lower()
            breed = BREEDS_CACHE.get(breed_name, None)
            if not breed:
                breed = CatBreed(**(cat_data['breeds'][0]))
                BREEDS_CACHE[breed_name] = breed
            breeds = breed
        else:
            breeds = None
        return SearchResponse(breed=breeds, image_id=cat_data['id'], image_url=cat_data['url'])


@mcp.tool()
async def get_cat_breeds(breed_name: str | None = None) -> dict[str, CatBreed | None]:
    """Get a list of all cat breeds from the Cat API.
    
    Args:
        breed_name: The name of the breed to get information about. If not provided, a list of all cat breeds will be returned.
    
    Returns:
        A list of CatBreed objects matching the breed name in lowercase or all known breeds.
    """
    global BREEDS_CACHE

    if BREEDS_CACHE:
        ret_value = None
        if breed_name:
            name = breed_name.lower()
            value = BREEDS_CACHE.get(name, None)
            if value:
                ret_value = {breed_name: value}
        else:
            ret_value = BREEDS_CACHE

        if ret_value:
            return ret_value

    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS) as client:
        response = await client.get('/breeds')
        response.raise_for_status()
        breeds = response.json()
        
        BREEDS_CACHE = {breed['name'].lower(): CatBreed(**breed) for breed in breeds}
        BREEDS_CACHE.update({breed['id']: CatBreed(**breed) for breed in breeds})
    
        if breed_name:
            if breed_name.lower() in BREEDS_CACHE:
                return {breed_name.lower(): BREEDS_CACHE.get(breed_name.lower())}
            return {breed_name.lower(): None}

        return BREEDS_CACHE

if __name__ == "__main__":
    mcp.run(transport="stdio")