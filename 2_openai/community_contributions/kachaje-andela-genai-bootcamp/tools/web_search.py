import time
from agents import function_tool
from ddgs import DDGS
from utils.globals import span


def _web_search_impl(query: str) -> str:
    """
    Search the web for current information using DuckDuckGo.
    
    Args:
        query: The search query string.
    
    Returns:
        A formatted string containing search results with titles, snippets, and URLs.
    """
    with span("web_search", f"Searching the web for: {query}"):
        print(f"-> Tool called: web_search({query})")
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with DDGS() as ddgs:
                    # Get results - ensure generator is fully consumed
                    # DuckDuckGo returns a generator, so we need to convert it to a list
                    # Using max_results=10 to get more comprehensive results
                    results_generator = ddgs.text(query, max_results=10)
                    
                    # Explicitly consume the entire generator to ensure all results are loaded
                    results = []
                    try:
                        for result in results_generator:
                            results.append(result)
                            # Safety check to avoid infinite loops (though max_results should limit this)
                            if len(results) >= 20:
                                break
                    except Exception as gen_error:
                        print(f"-> Warning: Error consuming generator: {gen_error}")
                        # If we got some results before the error, use them
                        if not results:
                            raise gen_error
                    
                    print(f"-> Debug: Retrieved {len(results)} raw results (attempt {attempt + 1})")
                    
                    if results:
                        print(f"-> Debug: First result keys: {list(results[0].keys())}")
                        
                        formatted_results = []
                        for i, result in enumerate(results, 1):
                            # Access dictionary keys directly (DuckDuckGo uses lowercase keys)
                            # Handle different possible key names
                            title = result.get('title') or result.get('Title') or 'No title'
                            body = result.get('body') or result.get('Body') or result.get('description') or result.get('Description') or 'No description'
                            href = result.get('href') or result.get('Href') or result.get('url') or result.get('URL') or 'No URL'
                            
                            # Truncate very long body text to keep results readable (but keep more than default snippets)
                            if len(body) > 500:
                                body = body[:500] + "..."
                            
                            # Only add if we have at least a title or meaningful body
                            if title != 'No title' or (body != 'No description' and len(body.strip()) > 0):
                                formatted_results.append(
                                    f"{i}. **{title}**\n   {body}\n   Source: {href}"
                                )
                        
                        if formatted_results:
                            result_text = "\n\n".join(formatted_results)
                            print(f"-> Tool result: Found {len(formatted_results)} search results (total length: {len(result_text)} chars)")
                            return result_text
                        else:
                            print("-> Tool result: Results found but no valid data to format")
                            return "Search completed but no usable results were found. The search may have been blocked or rate-limited."
                    else:
                        # No results - might be rate limiting, try again
                        if attempt < max_retries - 1:
                            print(f"-> No results on attempt {attempt + 1}, retrying in {retry_delay} second(s)...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            print("-> Tool result: No results found after all retries")
                            return "No search results found for the given query. This might be due to rate limiting or network issues. Please try again later."
                
            except Exception as e:
                import traceback
                error_msg = f"Search error on attempt {attempt + 1}: {str(e)}"
                print(f"ERROR: {error_msg}")
                
                if attempt < max_retries - 1:
                    print(f"-> Retrying in {retry_delay} second(s)...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    error_trace = traceback.format_exc()
                    print(f"ERROR Traceback: {error_trace}")
                    return f"An error occurred while searching after {max_retries} attempts: {error_msg}. This might be due to network issues or DuckDuckGo rate limiting. Please try again later."
        
        return "Search failed after multiple attempts. Please check your network connection and try again."


# Create the tool for use with agents
web_search = function_tool(_web_search_impl)

