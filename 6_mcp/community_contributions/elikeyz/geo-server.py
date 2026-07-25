from mcp.server.fastmcp import FastMCP
import geocoder

mcp = FastMCP("geo-server")

@mcp.tool()
async def get_location(ip: str) -> str:
    """Get the location of a specific IP address"""
    geo = geocoder.ip(ip)
    if geo.latlng:
      latitude, longitude = geo.latlng
      return f"Latitude: {latitude}, Longitude: {longitude}"
    else:
      return f"Failed to get location for IP: {ip}"

@mcp.tool()
async def get_my_location() -> str:
  """Get the location of the current user"""
  geo = geocoder.ip('me')
  if geo.latlng:
    latitude, longitude = geo.latlng
    return f"Latitude: {latitude}, Longitude: {longitude}"
  else:
    return "Failed to get location for current user"

if __name__ == "__main__":
  mcp.run(transport="stdio")
