from fastapi import FastAPI
from pydantic import BaseModel
from latest_market_research.crew import LatestMarketResearch

app = FastAPI(title="Stock Picker API")

# ------------------------------
# Pydantic model for user input
# ------------------------------
class StockPickerInput(BaseModel):
    topic: str
    risk_profile: str
    investment_horizon: str
    region: str
    market_cap_preference: str
    number_of_picks: int  # cast to int directly


# ------------------------------
# Health check / root endpoint
# ------------------------------
@app.get("/")
def read_root():
    return {"message": "Stock Picker API is running!"}


# ------------------------------
# Main stock picker endpoint
# ------------------------------
@app.post("/stock-picker")
def stock_picker_endpoint(inputs: StockPickerInput):
    """
    Receives user inputs, runs the stock picker, and returns results.
    """
    # Convert Pydantic model to dict
    input_dict = inputs.dict()

    # Run the crew
    crew_instance = LatestMarketResearch()
    result = crew_instance.crew().kickoff(inputs=input_dict)

    # Return JSON
    return {"results": result.raw}
