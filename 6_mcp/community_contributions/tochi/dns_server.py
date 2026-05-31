# mcp_dns_server_cached.py
from mcp.server.fastmcp import FastMCP
from dns_lookup import DNS
from functools import lru_cache

mcp = FastMCP("dns_server")

# Cache DNS lookups for 5 minutes (300 seconds)
@lru_cache(maxsize=100)
def get_cached_dns(domain: str) -> DNS:
    """Get or create a cached DNS instance"""
    return DNS(domain=domain)


@mcp.tool()
def get_registrar(domain: str) -> dict:
    """Get the registrar of the given domain.
    
    Args:
        domain: The domain name you want to get the registrar for (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing registrar information
    """
    dns = get_cached_dns(domain)
    response = dns.get_registrar()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def get_creation_date(domain: str) -> dict:
    """Get the creation date of the given domain.

    Args:
        domain: The domain name you want to get the creation date for (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing creation date information
    """
    dns = get_cached_dns(domain)
    response = dns.get_creation_date()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def get_expiry_date(domain: str) -> dict:
    """Get the expiration date of the given domain.

    Args:
        domain: The domain name you want to get the expiration date for (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing expiration date information
    """
    dns = get_cached_dns(domain)
    response = dns.get_expiry_date()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def get_name_servers(domain: str) -> dict:
    """Get the name servers of the given domain.
    
    Args:
        domain: The domain name you want to get the name servers for (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing name servers information
    """
    dns = get_cached_dns(domain)
    response = dns.get_name_servers()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def get_all_dns_info(domain: str) -> dict:
    """Get all DNS information for the given domain (registrar, creation date, expiry date, and name servers).

    Args:
        domain: The domain name you want to get all information for (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing all DNS information
    """
    dns = get_cached_dns(domain)
    return dns.get_all_info()


@mcp.tool()
def save_dns_search(domain: str) -> dict:
    """Save DNS search results to the database for tracking.
    
    This will store the domain name, expiry date, and registrar information
    in a local database for future monitoring.

    Args:
        domain: The domain name you want to save for tracking (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing save status and confirmation message
    """
    dns = get_cached_dns(domain)
    response = dns.save_dns_search()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def watch_dns() -> dict:
    """Watch and retrieve all domains expiring within 3 months from today.
    
    This returns a list of tracked domains that are expiring in the next 90 days,
    sorted by expiry date (earliest first). Useful for proactive domain renewal monitoring.
    
    Returns:
        Dictionary containing list of domains expiring soon with details:
        - domain name
        - expiry date
        - days until expiry
        - registrar
        - tracking history
    """
    response = DNS.watch_dns()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def get_all_tracked_domains() -> dict:
    """Get all tracked domains from the database.
    
    Returns a complete list of all domains being monitored, regardless of
    their expiration date. Useful for viewing your entire domain portfolio.
    
    Returns:
        Dictionary containing:
        - total_domains: Total number of tracked domains
        - records: List of all tracked domains with their information
    """
    response = DNS.get_all_tracked_domains()
    if response["status"]:
        return response
    else:
        raise Exception(response["error"])


@mcp.tool()
def lookup_and_save_domain(domain: str) -> dict:
    """Lookup DNS information for a domain and automatically save it for tracking.
    
    This is a convenience tool that combines get_all_dns_info() and save_dns_search()
    in a single call. Perfect for adding new domains to your monitoring list.

    Args:
        domain: The domain name you want to lookup and save (e.g., 'routelink.com')
    
    Returns:
        Dictionary containing both DNS information and save confirmation
    """
    dns = get_cached_dns(domain)
    
    # Get all DNS info
    dns_info = dns.get_all_info()
    
    # Save to database
    save_result = dns.save_dns_search()
    
    if save_result["status"]:
        return {
            "status": True,
            "dns_info": dns_info,
            "save_result": save_result
        }
    else:
        raise Exception(save_result["error"])


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()