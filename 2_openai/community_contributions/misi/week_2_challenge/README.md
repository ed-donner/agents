# Why Use `poor_man_web_search.py` Instead of `agent.WebSearchTool`

## Overview
This directory contains a simple web search utility: `poor_man_web_search.py`. This script is designed as a lightweight, cost-effective alternative to using the more advanced `agent.WebSearchTool` for basic web search tasks.

## Cost Comparison
- **`poor_man_web_search.py`**: This script performs web searches by directly querying public search engines or scraping web content without relying on paid APIs or third-party services. It only incurs minimal costs, such as network bandwidth and local compute resources, which are typically negligible for most users.
- **`agent.WebSearchTool`**: This tool often leverages commercial APIs (such as Bing Search, Google Custom Search, or similar services) that charge per request or per token. These costs can accumulate quickly, especially for frequent or large-scale searches.

## Why Is `poor_man_web_search.py` Cheaper?
1. **No API Fees**: It avoids the per-query or per-token charges associated with commercial web search APIs.
2. **No Subscription Required**: There is no need for a paid subscription or API key, making it accessible to anyone.
3. **Local Execution**: All processing happens locally, so you are not paying for cloud compute or managed service usage.
4. **Simplicity**: For many use cases, especially simple or low-volume searches, the script provides sufficient results without the overhead of advanced features.

## When to Use Each Tool
- **Use `poor_man_web_search.py`** when you want to minimize costs, do not require advanced search features, or are working on a project with budget constraints.
- **Use `agent.WebSearchTool`** if you need more reliable, comprehensive, or large-scale search capabilities, or require features only available through commercial APIs.

## Disclaimer
`poor_man_web_search.py` may be subject to rate limits or blocking by search engines if overused. Always respect the terms of service of any website you access.