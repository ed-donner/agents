# Smart Retail Communication MCP

## An MCP that allow clients to get an sms immediately a product that was available in stock is restocked.

In retail environments, communication between systems and teams often breaks down — especially when it comes to inventory and customer follow-ups.

For example:

When a product is out of stock:
- Store attendants manually write down customer phone numbers
- There is no structured system to track demand
- Customers are rarely notified when items are restocked

This leads to:
- Lost sales
- Poor customer experience
- Lack of data for restocking decisions

---

##Communication Challenge

The core issue is **communication**.

Different parts of the system do not talk to each other effectively:

- Customers → express interest, but data is not structured  
- Staff → collect information, but do not act on it  
- Inventory systems → update stock, but do not notify anyone  
- Management → lacks visibility into demand trends  

---

## Solution: Model-Driven Communication Protocol (MCP)

I have designed an MCP server that standardizes communication between agents in the retail system.

Instead of manual processes, we introduce:

- Structured tools (APIs)
- Defined communication flows
- Shared data access between agents

---

## Agents in the System

- **Customer Agent** → Requests products, subscribes to restock alerts  
- **Inventory Agent** → Tracks stock levels  
- **Notification Agent** → Sends alerts to customers  
- **Analytics Agent** → Monitors demand trends  

---

## 🔗 Communication via MCP

Each agent communicates through MCP tools:

| Tool | Purpose |
|------|--------|
| `check_inventory` | Query product availability |
| `request_restock_alert` | Register customer interest |
| `restock_product` | Update inventory |
| `notify_customers` | Send notifications |
| `analyze_demand` | Provide insights |

---

##Impact

- Automated customer follow-ups  
- Improved sales conversion  
- Data-driven restocking decisions  
- Reduced manual workload 

No external API keys required for this demo.
##Running the file
python retail_mcp.py