import json 
from modules.tools.setup_sheets import initialize_google_sheets
from modules.config import Config
from modules.setup_logging import setup_logging
import pandas as pd

logger = setup_logging()

_, df = initialize_google_sheets(config=Config)

# --- Data Query Tool ---
def run_query_from_agent(query_str: str, use_head: bool = False) -> str:
    try:
        if df.empty:
            return json.dumps({"error": "No data available in the DataFrame"})
        if use_head:
            target_df = df.head(2)
        else:
            target_df = df
        result = eval(query_str, {'df': target_df})
        if isinstance(result, pd.Series):
            result = result.to_dict()
        elif isinstance(result, pd.DataFrame):
            result = result.to_dict(orient='records')
        return json.dumps({"results": result} if result else {"error": "No products found matching your criteria"})
    except Exception as e:
        logger.error(f"Error executing query '{query_str}' on df: {str(e)}")
        return json.dumps({"error": f"Error: {str(e)}"})