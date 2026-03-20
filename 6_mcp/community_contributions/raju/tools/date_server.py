from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("date_server")

@mcp.tool()
def today_date() -> str:
    '''returns current date in yyyy-mm-dd format'''
    today = datetime.today().strftime(format="%Y-%m-%d")
    return today

if __name__ == '__main__':
    mcp.run(transport="stdio")
