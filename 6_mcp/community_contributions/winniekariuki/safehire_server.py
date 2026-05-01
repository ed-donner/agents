from mcp.server.fastmcp import FastMCP
mcp = FastMCP("SafeHire Risk Server")

@mcp.tool()
def calculate_risk(name: str, months_experience: int, complaints: int):
    """Calculate the risk score for a given name, months of experience, and complaints."""
    risk = "Low"
    
    if complaints >= 2:
        risk = "High"
    elif complaints == 1:
        risk = "Medium"
        
    if months_experience < 6 and risk == "Low":
        risk = "Medium"

    return {
        "name": name,
        "risk": risk,
        "reason": f"{complaints} complaints, {months_experience} months experience"
    }

if __name__ == "__main__":
    mcp.run(transport='stdio')