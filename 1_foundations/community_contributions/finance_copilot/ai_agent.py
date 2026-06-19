import openai
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.schema import AgentAction, AgentFinish
from langchain_openai import ChatOpenAI
from langchain.prompts import StringPromptTemplate
from langchain.tools import BaseTool
from typing import Dict, List, Optional, Union, Any
import json
import re
from config import Config
from market_data import MarketDataTool
from analysis_tool import AnalysisTool
from database import FinanceDatabase
from notification_system import NotificationSystem
import pandas as pd
from datetime import datetime
import os

class FinanceCopilotAgent:
    """AI agent for Finance Copilot that orchestrates tools and provides intelligent responses"""
    
    def __init__(self):
        """Initialize the AI agent"""
        self.config = Config()
        self.llm = self._initialize_llm()
        self.db = FinanceDatabase(self.config.DATABASE_PATH)
        self.market_data = MarketDataTool()
        self.analysis_tool = AnalysisTool()
        self.notification_system = NotificationSystem()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize conversation memory
        self.conversation_memory = []
        self.max_memory_items = 10  # Keep last 10 exchanges
        self.context_window = 5     # Consider last 5 exchanges for context
    
    def _initialize_llm(self):
        """Initialize the OpenAI LLM client"""
        try:
            # Check if API key is available
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("⚠️  OPENAI_API_KEY not found in environment variables")
                print("   Please set OPENAI_API_KEY in your .env file")
                return None
            
            # Initialize LangChain ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                openai_api_key=api_key,
                max_tokens=4000,  # Limit tokens to prevent context length issues
                request_timeout=60  # Add timeout
            )
            
            # Test the LLM with a simple query
            try:
                test_response = llm.invoke("Hello")
                print("✅ OpenAI LLM initialized and tested successfully")
                return llm
            except Exception as test_error:
                print(f"❌ LLM test failed: {test_error}")
                print("   This might indicate an API key issue or network problem")
                return None
            
        except ImportError as e:
            print(f"❌ Failed to import OpenAI libraries: {e}")
            print("   Please install: pip install openai langchain-openai")
            return None
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            return None
    
    def add_to_memory(self, user_query: str, ai_response: str, tools_used: List[str] = None):
        """Add a conversation exchange to memory"""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "ai_response": ai_response,
            "tools_used": tools_used or [],
            "summary": self._summarize_exchange(user_query, ai_response)
        }
        
        self.conversation_memory.append(exchange)
        
        # Keep only the last max_memory_items
        if len(self.conversation_memory) > self.max_memory_items:
            self.conversation_memory = self.conversation_memory[-self.max_memory_items:]
    
    def get_conversation_context(self) -> str:
        """Get relevant conversation context for the current query"""
        if not self.conversation_memory:
            return ""
        
        # Get the last context_window exchanges
        recent_exchanges = self.conversation_memory[-self.context_window:]
        
        context_parts = []
        for exchange in recent_exchanges:
            context_parts.append(f"User: {exchange['user_query']}")
            context_parts.append(f"AI: {exchange['summary']}")
            if exchange['tools_used']:
                context_parts.append(f"Tools used: {', '.join(exchange['tools_used'])}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _summarize_exchange(self, user_query: str, ai_response: str) -> str:
        """Create a concise summary of the exchange for memory"""
        # Extract key information from the response
        if "Growth Analysis" in ai_response:
            # Extract growth score if present
            score_match = re.search(r'Growth Score: (-?\d+)/10', ai_response)
            if score_match:
                score = score_match.group(1)
                return f"Provided growth analysis with score {score}/10"
            return "Provided growth analysis"
        
        elif "stock price" in user_query.lower() or "price" in user_query.lower():
            # Extract price information if available
            price_match = re.search(r'\$(\d+\.?\d*)', ai_response)
            if price_match:
                price = price_match.group(1)
                return f"Retrieved stock price: ${price}"
            return "Retrieved stock price information"
        
        elif "fundamentals" in user_query.lower():
            # Extract key fundamental metrics
            pe_match = re.search(r'P/E.*?(\d+\.?\d*)', ai_response, re.IGNORECASE)
            if pe_match:
                pe = pe_match.group(1)
                return f"Retrieved company fundamentals with P/E ratio {pe}"
            return "Retrieved company fundamentals"
        
        elif "portfolio" in user_query.lower():
            return "Retrieved portfolio information"
        
        elif "news" in user_query.lower():
            return "Retrieved company news"
        
        else:
            # Generic summary
            return "Provided financial information and analysis"
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.conversation_memory = []
    
    def get_memory_summary(self) -> str:
        """Get a summary of conversation memory"""
        if not self.conversation_memory:
            return "No conversation history"
        
        summary_parts = []
        summary_parts.append(f"**Conversation Memory ({len(self.conversation_memory)} exchanges)**")
        
        for i, exchange in enumerate(self.conversation_memory[-5:], 1):  # Show last 5
            summary_parts.append(f"{i}. **{exchange['user_query'][:50]}...**")
            summary_parts.append(f"   Response: {exchange['summary']}")
            if exchange['tools_used']:
                summary_parts.append(f"   Tools: {', '.join(exchange['tools_used'])}")
        
        return "\n".join(summary_parts)
    
    def get_tools(self) -> List[BaseTool]:
        """Get the list of available tools"""
        return self.tools
        
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all available tools"""
        tools = [
            Tool(
                name="get_stock_price",
                func=self._get_stock_price,
                description="Get current stock price and basic information for a given symbol"
            ),
            Tool(
                name="get_crypto_price",
                func=self._get_crypto_price,
                description="Get current cryptocurrency price and information for a given symbol"
            ),
            Tool(
                name="get_stock_fundamentals",
                func=self._get_stock_fundamentals,
                description="Get detailed fundamental analysis for a stock including financial ratios"
            ),
            Tool(
                name="get_company_news",
                func=self._get_company_news,
                description="Get latest news and sentiment analysis for a company"
            ),
            Tool(
                name="get_portfolio",
                func=self._get_portfolio,
                description="Get current portfolio holdings and positions"
            ),
            Tool(
                name="add_portfolio_item",
                func=self._add_portfolio_item,
                description="Add a new stock or crypto position to the portfolio"
            ),
            Tool(
                name="update_portfolio",
                func=self._update_portfolio,
                description="Update portfolio with buy/sell transactions"
            ),
            Tool(
                name="calculate_portfolio_metrics",
                func=self._calculate_portfolio_metrics,
                description="Calculate comprehensive portfolio performance metrics"
            ),
            Tool(
                name="run_monte_carlo_simulation",
                func=self._run_monte_carlo_simulation,
                description="Run Monte Carlo simulation for portfolio forecasting"
            ),
            Tool(
                name="run_symbol_monte_carlo_simulation",
                func=self._run_symbol_monte_carlo_simulation,
                description="Run Monte Carlo simulation for a specific stock or crypto symbol"
            ),
            Tool(
                name="create_portfolio_charts",
                func=self._create_portfolio_charts,
                description="Create portfolio visualization charts"
            ),
            Tool(
                name="suggest_rebalancing",
                func=self._suggest_rebalancing,
                description="Suggest portfolio rebalancing actions based on current weights"
            ),
            Tool(
                name="add_price_alert",
                func=self._add_price_alert,
                description="Add price alerts for one or multiple symbols. Supports percentage thresholds (e.g., 5%) or volatility levels (low: 2%, medium: 5%, high: 10%, very high: 15%, extreme: 20%). Can handle single symbol or multiple symbols in one request."
            ),
            Tool(
                name="get_market_summary",
                func=self._get_market_summary,
                description="Get market summary for major indices"
            ),
            Tool(
                name="send_notification",
                func=self._send_notification,
                description="Send a custom push notification"
            ),
            Tool(
                name="get_conversation_history",
                func=self._get_conversation_history,
                description="Get a summary of recent conversation history and context"
            ),
            Tool(
                name="clear_conversation_history",
                func=self._clear_conversation_history,
                description="Clear conversation history and start fresh"
            )
        ]
        return tools
    
    def _get_stock_price(self, symbol: str) -> str:
        """Get stock price tool wrapper"""
        try:
            result = self.market_data.get_stock_price(symbol)
            if "error" in result:
                return f"Error: {result['error']}"
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_crypto_price(self, symbol: str) -> str:
        """Get crypto price tool wrapper"""
        try:
            result = self.market_data.get_crypto_price(symbol)
            if "error" in result:
                return f"Error: {result['error']}"
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_stock_fundamentals(self, symbol: str) -> str:
        """Get stock fundamentals tool wrapper"""
        try:
            result = self.market_data.get_stock_fundamentals(symbol)
            if "error" in result:
                return f"Error: {result['error']}"
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_company_news(self, symbol: str, limit: int = 5) -> str:
        """Get company news tool wrapper"""
        try:
            result = self.market_data.get_company_news(symbol, limit)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_portfolio(self) -> str:
        """Get portfolio tool wrapper"""
        try:
            result = self.db.get_portfolio()
            if result.empty:
                return "Portfolio is empty"
            
            # Convert to a more readable format
            portfolio_list = []
            for _, row in result.iterrows():
                portfolio_list.append({
                    'symbol': row['symbol'],
                    'shares': row['shares'],
                    'avg_price': f"${row['avg_price']:.2f}",
                    'purchase_date': row['purchase_date'] if 'purchase_date' in row else 'N/A'
                })
            
            return json.dumps(portfolio_list, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _add_portfolio_item(self, symbol: str, shares: float, avg_price: float, purchase_date: str = None) -> str:
        """Add portfolio item tool wrapper"""
        try:
            self.db.add_portfolio_item(symbol, shares, avg_price, purchase_date)
            return f"Successfully added {shares} shares of {symbol} at ${avg_price:.2f}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _update_portfolio(self, symbol: str, shares: float, price: float, transaction_type: str) -> str:
        """Update portfolio tool wrapper"""
        try:
            self.db.update_portfolio(symbol, shares, price, transaction_type)
            
            # Fix grammar for transaction types
            if transaction_type.upper() == "BUY":
                action = "bought"
            elif transaction_type.upper() == "SELL":
                action = "sold"
            else:
                action = transaction_type.lower()
            
            return f"Successfully {action} {shares} shares of {symbol} at ${price:.2f}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _calculate_portfolio_metrics(self) -> str:
        """Calculate portfolio metrics tool wrapper"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return "Portfolio is empty"
            
            # Convert to dict format
            portfolio_dict = {}
            for _, row in portfolio.iterrows():
                portfolio_dict[row['symbol']] = {
                    'shares': row['shares'],
                    'avg_price': row['avg_price']
                }
            
            # Get current prices
            symbols = list(portfolio_dict.keys())
            current_prices = self.market_data.get_portfolio_prices(symbols)
            
            # Calculate metrics
            metrics = self.analysis_tool.calculate_portfolio_metrics(portfolio_dict, current_prices)
            
            if "error" in metrics:
                return f"Error: {metrics['error']}"
            
            return json.dumps(metrics, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _run_monte_carlo_simulation(self, forecast_years: int = 5, num_simulations: int = 10000) -> str:
        """Run Monte Carlo simulation tool wrapper"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return "Portfolio is empty"
            
            # Get historical data for portfolio symbols
            returns_data = {}
            for symbol in portfolio['symbol']:
                hist_data = self.market_data.get_historical_data(symbol, period="1y")
                if not hist_data.empty:
                    returns = self.analysis_tool.calculate_returns(hist_data['Close'])
                    returns_data[symbol] = returns
            
            if not returns_data:
                return "No historical data available for simulation"
            
            # Create returns DataFrame
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()
            
            if returns_df.empty:
                return "Insufficient data for simulation"
            
            # Run simulation
            initial_value = 10000  # Default value
            result = self.analysis_tool.run_monte_carlo_simulation(
                returns_df, initial_value, num_simulations, forecast_years
            )
            
            if "error" in result:
                return f"Error: {result['error']}"
            
            # Remove numpy arrays for JSON serialization
            result.pop('simulation_results', None)
            result.pop('final_values', None)
            
            # Clean up any remaining numpy/pandas objects that might cause JSON serialization issues
            cleaned_result = {}
            for key, value in result.items():
                try:
                    # Convert numpy types to Python native types
                    if hasattr(value, 'item'):  # numpy scalar
                        cleaned_result[key] = value.item()
                    elif hasattr(value, 'tolist'):  # numpy array
                        cleaned_result[key] = value.tolist()
                    elif isinstance(value, (pd.Series, pd.DataFrame)):
                        cleaned_result[key] = value.to_dict() if hasattr(value, 'to_dict') else str(value)
                    else:
                        cleaned_result[key] = value
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean key {key}, converting to string: {e}")
                    cleaned_result[key] = str(value)
            
            # Add symbol context to the result
            cleaned_result['symbol'] = symbol
            cleaned_result['analysis_type'] = 'Individual Symbol Monte Carlo Simulation'
            
            print(f"🔍 DEBUG: Final result prepared, converting to JSON")
            json_result = json.dumps(cleaned_result, indent=2)
            print(f"🔍 DEBUG: JSON conversion successful, length: {len(json_result)}")
            
            return json_result
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _run_symbol_monte_carlo_simulation(self, symbol: str, forecast_years: int = 5, num_simulations: int = 10000) -> str:
        """Run Monte Carlo simulation for a specific symbol (stock or crypto)"""
        try:
            # Get historical data for the specific symbol
            hist_data = self.market_data.get_historical_data(symbol, period="1y")
            if hist_data.empty:
                return f"No historical data available for {symbol}"
            
            # Calculate returns
            returns = self.analysis_tool.calculate_returns(hist_data['Close'])
            if returns.empty:
                return f"Insufficient data for {symbol} simulation"
            
            # Create returns DataFrame (single column)
            returns_df = pd.DataFrame({symbol: returns})
            returns_df = returns_df.dropna()
            
            if returns_df.empty:
                return f"Insufficient data for {symbol} simulation"
            
            # Run simulation with $10,000 initial investment
            initial_value = 10000
            result = self.analysis_tool.run_monte_carlo_simulation(
                returns_df, initial_value, num_simulations, forecast_years
            )
            
            if "error" in result:
                return f"Error: {result['error']}"
            
            # Remove numpy arrays for JSON serialization
            result.pop('simulation_results', None)
            result.pop('final_values', None)
            
            # Clean up any remaining numpy/pandas objects that might cause JSON serialization issues
            cleaned_result = {}
            for key, value in result.items():
                try:
                    # Convert numpy types to Python native types
                    if hasattr(value, 'item'):  # numpy scalar
                        cleaned_result[key] = value.item()
                    elif hasattr(value, 'tolist'):  # numpy array
                        cleaned_result[key] = value.tolist()
                    elif isinstance(value, (pd.Series, pd.DataFrame)):
                        cleaned_result[key] = value.to_dict() if hasattr(value, 'to_dict') else str(value)
                    else:
                        cleaned_result[key] = value
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean key {key}, converting to string: {e}")
                    cleaned_result[key] = str(value)
            
            # Add symbol context to the result
            cleaned_result['symbol'] = symbol
            cleaned_result['analysis_type'] = 'Individual Symbol Monte Carlo Simulation'
            
            return json.dumps(cleaned_result, indent=2)
        except Exception as e:
            return f"Error running Monte Carlo simulation for {symbol}: {str(e)}"
    
    def _create_portfolio_charts(self) -> str:
        """Create portfolio charts tool wrapper"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return "Portfolio is empty"
            
            # Convert to dict format
            portfolio_dict = {}
            for _, row in portfolio.iterrows():
                portfolio_dict[row['symbol']] = {
                    'shares': row['shares'],
                    'avg_price': row['avg_price']
                }
            
            # Get current prices
            symbols = list(portfolio_dict.keys())
            current_prices = self.market_data.get_portfolio_prices(symbols)
            
            # Create charts
            charts = self.analysis_tool.create_portfolio_charts(portfolio_dict, current_prices)
            
            if "error" in charts:
                return f"Error: {charts['error']}"
            
            # Return chart data (charts will be displayed in UI)
            return json.dumps({
                "total_value": charts["total_value"],
                "symbols": charts["symbols"],
                "weights": charts["weights"],
                "returns": charts["returns"]
            }, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _suggest_rebalancing(self) -> str:
        """Suggest rebalancing tool wrapper"""
        try:
            portfolio = self.db.get_portfolio()
            if portfolio.empty:
                return "Portfolio is empty"
            
            # Convert to dict format
            portfolio_dict = {}
            for _, row in portfolio.iterrows():
                portfolio_dict[row['symbol']] = {
                    'shares': row['shares'],
                    'avg_price': row['avg_price']
                }
            
            # Get current prices
            symbols = list(portfolio_dict.keys())
            current_prices = self.market_data.get_portfolio_prices(symbols)
            
            # Get rebalancing suggestions
            suggestions = self.analysis_tool.suggest_rebalancing(portfolio_dict, current_prices)
            
            if "error" in suggestions:
                return f"Error: {suggestions['error']}"
            
            return json.dumps(suggestions, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _add_price_alert(self, symbol: str, alert_type: str, threshold: float) -> str:
        """Add price alert tool wrapper"""
        try:
            self.db.add_alert(symbol, alert_type, threshold)
            return f"Successfully added {alert_type} alert for {symbol} at {threshold}% threshold"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_market_summary(self) -> str:
        """Get market summary tool wrapper"""
        try:
            result = self.market_data.get_market_summary()
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _send_notification(self, title: str, message: str) -> str:
        """Send notification tool wrapper"""
        try:
            success = self.notification_system.send_pushover_notification(title, message)
            if success:
                return f"Successfully sent notification: {title}"
            else:
                return "Failed to send notification"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_conversation_history(self) -> str:
        """Get conversation history tool wrapper"""
        try:
            return self.get_memory_summary()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _clear_conversation_history(self) -> str:
        """Clear conversation history tool wrapper"""
        try:
            self.clear_memory()
            return "Conversation history cleared successfully. Starting fresh!"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def process_query(self, user_query: str) -> str:
        """Process user query using AI to intelligently select and execute tools"""
        if not self.llm:
            return "❌ **OpenAI API Key Not Configured**\n\nPlease set `OPENAI_API_KEY` in your environment variables or `.env` file.\n\n**To fix this:**\n1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)\n2. Add it to your `.env` file: `OPENAI_API_KEY=your_key_here`\n3. Restart the application\n\n**Alternative:** You can still use the app for market data, portfolio management, and analysis, but AI-powered responses won't be available."
        
        try:
            # Step 1: Analyze the query and determine which tools to use
            analysis_prompt = f"""
You are an AI financial analyst. Analyze the user's query and determine which tools to use to provide the most comprehensive answer.

AVAILABLE TOOLS:
{self._format_tools_for_prompt()}

CONVERSATION CONTEXT:
{self.get_conversation_context()}

USER QUERY: "{user_query}"

ANALYSIS INSTRUCTIONS:
1. **Consider conversation context** - Use previous exchanges to provide more relevant responses
2. **Think comprehensively** - For company analysis, consider using multiple tools:
   - Company fundamentals (get_stock_fundamentals)
   - Company news (get_company_news)
   - Current stock price (get_stock_price)
   
3. **For portfolio questions**, use portfolio-related tools
4. **For market overview**, use market summary tools
5. **Select ALL relevant tools** that would provide valuable information
6. **Extract parameters** like stock symbols (AAPL, GOOGL, MSFT) from the query
7. **Build on previous analysis** - If user asked about a stock before, reference that context

EXAMPLES:
Query: "Tell me about Google" → {{"tools_to_use": ["get_stock_price", "get_stock_fundamentals", "get_company_news"], "parameters": {{"symbol": "GOOGL", "limit": 5}}}}
Query: "What's the price of AAPL?" → {{"tools_to_use": ["get_stock_price"], "parameters": {{"symbol": "AAPL"}}}}
Query: "Show me MSFT fundamentals and news" → {{"tools_to_use": ["get_stock_fundamentals", "get_company_news"], "parameters": {{"symbol": "MSFT", "limit": 5}}}}
Query: "What's in my portfolio?" → {{"tools_to_use": ["get_portfolio"], "parameters": {{}}}}
Query: "How does that compare to what we discussed earlier?" → {{"tools_to_use": ["get_stock_price", "get_stock_fundamentals"], "parameters": {{"symbol": "AAPL"}}}}

Return only the JSON response:
"""
            
            print(f"🔍 Analyzing query: {user_query}")
            
            try:
                analysis_response = self.llm.invoke([{"role": "user", "content": analysis_prompt}])
                analysis_content = analysis_response.content if hasattr(analysis_response, 'content') else str(analysis_response)
            except Exception as llm_error:
                print(f"❌ LLM analysis failed: {llm_error}")
                return f"❌ **AI Analysis Failed**\n\nI encountered an error while analyzing your query: `{user_query}`\n\n**Error:** {str(llm_error)}\n\n**Possible causes:**\n- OpenAI API key is invalid or expired\n- Network connectivity issues\n- OpenAI service is temporarily unavailable\n\n**To troubleshoot:**\n1. Check your internet connection\n2. Verify your OpenAI API key is valid\n3. Check [OpenAI Status](https://status.openai.com/)\n4. Try again in a few minutes\n\n**Alternative:** You can still access market data, portfolio information, and analysis tools directly from the other tabs."
            
            # Step 2: Parse the analysis and extract tool information
            tool_plan = self._parse_tool_analysis(analysis_content)
            if not tool_plan:
                return self._get_helpful_fallback_response(user_query)
            
            print(f"🎯 Tool plan: {tool_plan}")
            
            # Step 3: Execute the selected tools
            tool_results = self._execute_tools(tool_plan)
            
            # Step 4: Check if this is a growth analysis query and handle specially
            if self._is_growth_analysis_query(user_query):
                return self._handle_growth_analysis_query(user_query, tool_results)
            
            # Step 5: Truncate results to prevent token limit exceeded
            truncated_results = self._truncate_tool_results(tool_results)
            
            # Step 6: Generate comprehensive response using AI
            response_prompt = f"""
You are a helpful financial AI assistant. The user asked: "{user_query}"

CONVERSATION CONTEXT:
{self.get_conversation_context()}

You executed these tools and got these results:
{json.dumps(truncated_results, indent=2)}

INSTRUCTIONS:
1. **Use conversation context** - Reference previous exchanges when relevant
2. Provide a comprehensive, helpful response based on the tool results
3. Format the response nicely with markdown
4. Include specific data and insights from the tools
5. If there were errors, explain them clearly and provide troubleshooting tips
6. If successful, present the information in an organized, easy-to-read format
7. Add helpful context and analysis where appropriate
8. Use emojis and formatting to make the response engaging
9. If data was truncated, mention that and focus on the key insights available
10. **Build on previous analysis** - If this relates to earlier questions, make connections

RESPONSE REQUIREMENTS:
- Be informative and actionable
- Format numbers and data clearly
- Provide insights, not just raw data
- If errors occurred, help the user understand what went wrong
- Suggest next steps or related questions
- Keep the response concise but comprehensive
- **Reference previous context** when it adds value

Respond in a helpful, professional tone:
"""
            
            try:
                final_response = self.llm.invoke([{"role": "user", "content": response_prompt}])
                ai_response = final_response.content if hasattr(final_response, 'content') else str(final_response)
            except Exception as llm_error:
                print(f"❌ LLM response generation failed: {llm_error}")
                return f"❌ **AI Response Generation Failed**\n\nI successfully analyzed your query and executed the necessary tools, but encountered an error while generating the final response.\n\n**Query:** {user_query}\n**Error:** {str(llm_error)}\n\n**Tool Results Available:**\n{json.dumps(truncated_results, indent=2)}\n\n**To troubleshoot:**\n1. Check your internet connection\n2. Verify your OpenAI API key is valid\n3. Try again in a few minutes\n\n**Alternative:** You can view the raw tool results above or access the data directly from the other tabs."
            
            # Step 7: Add to conversation memory
            self.add_to_memory(user_query, ai_response, tool_plan.get('tools_to_use', []))
            
            return ai_response
            
        except Exception as e:
            error_msg = f"❌ **Unexpected Error**\n\nAn unexpected error occurred while processing your query: `{user_query}`\n\n**Error:** {str(e)}\n\n**To troubleshoot:**\n1. Check that all required environment variables are set\n2. Verify your API keys are valid\n3. Check your internet connection\n4. Try again in a few minutes\n\n**Alternative:** You can still access market data, portfolio information, and analysis tools directly from the other tabs."
            print(f"❌ Unexpected error in process_query: {e}")
            return error_msg
    
    def _format_tools_for_prompt(self) -> str:
        """Format available tools for the prompt"""
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(tool_descriptions)
    
    def _parse_tool_analysis(self, analysis_content: str) -> Dict:
        """Parse the LLM's tool analysis response"""
        try:
            import re
            import json
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', analysis_content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Validate required fields
                if "tools_to_use" in analysis and "parameters" in analysis:
                    return {
                        "tools": analysis["tools_to_use"],
                        "parameters": analysis.get("parameters", {}),
                        "reasoning": analysis.get("reasoning", ""),
                        "expected_output": analysis.get("expected_output", "")
                    }
            
            # Fallback: try to extract tool names from text
            print(f"⚠️  JSON parsing failed, using fallback extraction")
            return self._fallback_tool_extraction(analysis_content)
            
        except Exception as e:
            print(f"❌ Tool analysis parsing failed: {e}")
            return self._fallback_tool_extraction(analysis_content)
    
    def _fallback_tool_extraction(self, analysis_content: str) -> Dict:
        """Fallback method to extract tools when JSON parsing fails"""
        query_lower = analysis_content.lower()
        tools_to_use = []
        parameters = {}
        
        # Extract stock symbols - be more intelligent about what constitutes a valid ticker
        import re
        
        # Common words that should NOT be treated as stock symbols
        common_words = {
            'WHAT', 'WHEN', 'WHERE', 'WHY', 'HOW', 'THE', 'AND', 'FOR', 'ARE', 'YOU', 'YOUR',
            'THEY', 'THEIR', 'THERE', 'HERE', 'THIS', 'THAT', 'WITH', 'FROM', 'ABOUT', 'INTO',
            'THROUGH', 'DURING', 'BEFORE', 'AFTER', 'ABOVE', 'BELOW', 'INSIDE', 'OUTSIDE',
            'BETWEEN', 'AMONG', 'AGAINST', 'TOWARD', 'TOWARDS', 'WITHIN', 'WITHOUT'
        }
        
        # Look for potential stock symbols (1-5 letters, but exclude common words)
        potential_symbols = re.findall(r'\b[A-Z]{1,5}\b', analysis_content.upper())
        
        # Filter out common words and validate symbols
        valid_symbols = []
        for symbol in potential_symbols:
            if symbol not in common_words:
                # Additional validation: check if it looks like a real ticker
                # Most real tickers don't have all vowels or all consonants
                vowels = sum(1 for c in symbol if c in 'AEIOU')
                consonants = len(symbol) - vowels
                
                # Skip if it's all vowels or all consonants (likely not a real ticker)
                if vowels > 0 and consonants > 0:
                    valid_symbols.append(symbol)
        
        if valid_symbols:
            # Use the first valid symbol found
            parameters["symbol"] = valid_symbols[0]
        
        # Pattern matching for tools
        if any(word in query_lower for word in ["price", "stock", "quote"]):
            tools_to_use.append("get_stock_price")
        elif any(word in query_lower for word in ["fundamentals", "pe ratio", "financial"]):
            tools_to_use.append("get_stock_fundamentals")
        elif any(word in query_lower for word in ["portfolio", "holdings"]):
            tools_to_use.append("get_portfolio")
        elif any(word in query_lower for word in ["market", "summary", "overview"]):
            tools_to_use.append("get_market_summary")
        elif any(word in query_lower for word in ["bitcoin", "btc", "crypto"]):
            tools_to_use.append("get_crypto_price")
            # For crypto queries, set BTC-USD as default if no specific symbol found
            if "symbol" not in parameters:
                parameters["symbol"] = "BTC-USD"
            
            # If the query mentions outlook, forecast, or future, also add Monte Carlo simulation
            if any(word in query_lower for word in ["outlook", "forecast", "future", "prediction", "simulation"]):
                tools_to_use.append("run_symbol_monte_carlo_simulation")
                # Set default parameters for Monte Carlo
                if "years" not in parameters:
                    parameters["years"] = 5
                if "simulations" not in parameters:
                    parameters["simulations"] = 10000
        
        return {
            "tools": tools_to_use,
            "parameters": parameters,
            "reasoning": "Fallback tool extraction",
            "expected_output": "Tool execution results"
        }
    
    def _execute_tools(self, tool_plan: Dict) -> Dict:
        """Execute the planned tools and return results"""
        results = {}
        
        for tool_name in tool_plan.get("tools", []):
            try:
                print(f"🔧 Executing tool: {tool_name}")
                
                if tool_name == "get_stock_price":
                    symbol = tool_plan["parameters"].get("symbol")
                    if not symbol:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    result = self._get_stock_price(symbol)
                    results[tool_name] = self._ensure_dict_result(result, f"Stock price for {symbol}")
                
                elif tool_name == "get_stock_fundamentals":
                    symbol = tool_plan["parameters"].get("symbol")
                    if not symbol:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    result = self._get_stock_fundamentals(symbol)
                    results[tool_name] = self._ensure_dict_result(result, f"Fundamentals for {symbol}")
                
                elif tool_name == "get_company_news":
                    symbol = tool_plan["parameters"].get("symbol")
                    if not symbol:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    limit = tool_plan["parameters"].get("limit", 5)
                    result = self._get_company_news(symbol, limit)
                    results[tool_name] = self._ensure_dict_result(result, f"Company news for {symbol}")
                
                elif tool_name == "get_portfolio":
                    result = self._get_portfolio()
                    results[tool_name] = self._ensure_dict_result(result, "Portfolio data")
                
                elif tool_name == "add_portfolio_item":
                    symbol = tool_plan["parameters"].get("symbol")
                    if not symbol:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    
                    # Get shares/quantity and price from parameters with multiple name variations
                    shares = (tool_plan["parameters"].get("shares") or 
                             tool_plan["parameters"].get("quantity") or
                             tool_plan["parameters"].get("amount"))
                    
                    avg_price = (tool_plan["parameters"].get("avg_price") or 
                                tool_plan["parameters"].get("price") or
                                tool_plan["parameters"].get("cost"))
                    
                    # Validate required parameters
                    if shares is None or avg_price is None:
                        results[tool_name] = {
                            "error": "Missing required parameters",
                            "suggestion": "Please specify both shares/quantity and price (e.g., 'add 100 shares of AAPL at $150')"
                        }
                        continue
                    
                    purchase_date = tool_plan["parameters"].get("purchase_date", None)
                    result = self._add_portfolio_item(symbol, shares, avg_price, purchase_date)
                    results[tool_name] = self._ensure_dict_result(result, f"Portfolio item added for {symbol}")
                
                elif tool_name == "update_portfolio":
                    symbol = tool_plan["parameters"].get("symbol")
                    if not symbol:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    
                    # Get shares/quantity and price from parameters with multiple name variations
                    shares = (tool_plan["parameters"].get("shares") or 
                             tool_plan["parameters"].get("quantity") or
                             tool_plan["parameters"].get("amount"))
                    
                    avg_price = (tool_plan["parameters"].get("avg_price") or 
                                tool_plan["parameters"].get("price") or
                                tool_plan["parameters"].get("cost"))
                    
                    action = tool_plan["parameters"].get("action", "BUY")
                    
                    # Validate required parameters
                    if shares is None or avg_price is None:
                        results[tool_name] = {
                            "error": "Missing required parameters",
                            "suggestion": "Please specify both shares/quantity and price (e.g., 'buy 50 shares of GOOGL at $2800')"
                        }
                        continue
                    
                    result = self._update_portfolio(symbol, shares, avg_price, action)
                    results[tool_name] = self._ensure_dict_result(result, f"Portfolio updated for {symbol}")
                
                elif tool_name == "calculate_portfolio_metrics":
                    result = self._calculate_portfolio_metrics()
                    results[tool_name] = self._ensure_dict_result(result, "Portfolio metrics")
                
                elif tool_name == "run_monte_carlo_simulation":
                    forecast_years = tool_plan["parameters"].get("years", 5)
                    num_simulations = tool_plan["parameters"].get("simulations", 10000)
                    result = self._run_monte_carlo_simulation(forecast_years, num_simulations)
                    results[tool_name] = self._ensure_dict_result(result, "Monte Carlo simulation")
                
                elif tool_name == "run_symbol_monte_carlo_simulation":
                    symbol = tool_plan["parameters"].get("symbol")
                    if not symbol:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    
                    forecast_years = tool_plan["parameters"].get("years", 5)
                    num_simulations = tool_plan["parameters"].get("simulations", 10000)
                    result = self._run_symbol_monte_carlo_simulation(symbol, forecast_years, num_simulations)
                    results[tool_name] = self._ensure_dict_result(result, f"Monte Carlo simulation for {symbol}")
                
                elif tool_name == "create_portfolio_charts":
                    result = self._create_portfolio_charts()
                    results[tool_name] = self._ensure_dict_result(result, "Portfolio charts")
                
                elif tool_name == "suggest_rebalancing":
                    result = self._suggest_rebalancing()
                    results[tool_name] = self._ensure_dict_result(result, "Rebalancing suggestions")
                
                elif tool_name == "add_price_alert":
                    # Handle both single symbol and multiple symbols
                    symbol = tool_plan["parameters"].get("symbol")
                    symbols = tool_plan["parameters"].get("symbols")
                    
                    # Determine which symbols to process
                    if symbols and isinstance(symbols, list):
                        symbols_to_process = symbols
                    elif symbol:
                        symbols_to_process = [symbol]
                    else:
                        results[tool_name] = {
                            "error": "No valid stock symbol found in the query",
                            "suggestion": "Please specify a stock symbol (e.g., AAPL, GOOGL, MSFT)"
                        }
                        continue
                    
                    # Get alert parameters from user input with multiple name variations
                    alert_type = tool_plan["parameters"].get("alert_type", "PRICE_DROP")
                    
                    # Try to get threshold from various parameter names
                    threshold = (tool_plan["parameters"].get("threshold") or
                               tool_plan["parameters"].get("drop_percentage") or
                               tool_plan["parameters"].get("percentage") or
                               tool_plan["parameters"].get("drop") or
                               tool_plan["parameters"].get("percent"))
                    
                    # Handle volatility-based alerts by converting to percentage thresholds
                    if threshold is None:
                        volatility = (tool_plan["parameters"].get("volatility") or
                                    tool_plan["parameters"].get("volatility_level"))
                        if volatility:
                            # Convert volatility levels to percentage thresholds
                            volatility_thresholds = {
                                "low": 2.0,      # 2% change
                                "medium": 5.0,   # 5% change
                                "high": 10.0,   # 10% change
                                "very high": 15.0,  # 15% change
                                "extreme": 20.0  # 20% change
                            }
                            threshold = volatility_thresholds.get(volatility.lower(), 5.0)
                            alert_type = "VOLATILITY_ALERT"
                        else:
                            # Default threshold if no specific value or volatility provided
                            threshold = 5.0
                            alert_type = "PRICE_DROP"
                    
                    # Ensure threshold is numeric
                    try:
                        threshold = float(threshold)
                    except (ValueError, TypeError):
                        threshold = 5.0  # Default to 5% if conversion fails
                    
                    # Process multiple symbols
                    results_list = []
                    for sym in symbols_to_process:
                        try:
                            result = self._add_price_alert(sym, alert_type, threshold)
                            results_list.append(f"✅ {result}")
                        except Exception as e:
                            results_list.append(f"❌ Failed to add alert for {sym}: {str(e)}")
                    
                    # Combine results
                    combined_result = "\n".join(results_list)
                    results[tool_name] = self._ensure_dict_result(combined_result, f"Price alerts for {len(symbols_to_process)} symbols")
                
                elif tool_name == "get_market_summary":
                    result = self._get_market_summary()
                    results[tool_name] = self._ensure_dict_result(result, "Market summary")
                
                elif tool_name == "get_crypto_price":
                    symbol = tool_plan["parameters"].get("symbol", "BTC-USD")
                    result = self._get_crypto_price(symbol)
                    results[tool_name] = self._ensure_dict_result(result, f"Crypto price for {symbol}")
                
                elif tool_name == "send_notification":
                    title = tool_plan["parameters"].get("title", "Notification")
                    message = tool_plan["parameters"].get("message", "Test message")
                    result = self._send_notification(title, message)
                    results[tool_name] = self._ensure_dict_result(result, "Notification sent")
                
                elif tool_name == "get_conversation_history":
                    result = self._get_conversation_history()
                    results[tool_name] = self._ensure_dict_result(result, "Conversation history")
                
                elif tool_name == "clear_conversation_history":
                    result = self._clear_conversation_history()
                    results[tool_name] = self._ensure_dict_result(result, "Conversation history cleared")
                
                else:
                    results[tool_name] = {"error": f"Tool {tool_name} not implemented"}
                
                print(f"✅ Tool {tool_name} executed successfully")
                
            except Exception as e:
                print(f"❌ Tool {tool_name} failed: {e}")
                results[tool_name] = {"error": f"Tool execution failed: {str(e)}"}
        
        return results
    
    def _ensure_dict_result(self, result, description: str) -> Dict:
        """Ensure the result is a dictionary, parsing JSON strings if needed"""
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            try:
                # Try to parse as JSON
                import json
                parsed = json.loads(result)
                return parsed
            except json.JSONDecodeError:
                # If it's not JSON, wrap it in a dict
                return {"data": result, "description": description}
        else:
            return {"data": str(result), "description": description}
    
    def _truncate_tool_results(self, tool_results: Dict, max_tokens: int = 6000) -> Dict:
        """Truncate tool results to prevent token limit exceeded errors"""
        truncated_results = {}
        total_length = 0
        
        for tool_name, result in tool_results.items():
            # Convert result to string to measure length
            result_str = json.dumps(result, indent=2)
            result_length = len(result_str)
            
            # If adding this result would exceed the limit, truncate it
            if total_length + result_length > max_tokens:
                # Truncate the result
                if isinstance(result, dict):
                    if "data" in result:
                        # For news or other long data, keep only essential info
                        truncated_results[tool_name] = {
                            "summary": f"Data truncated due to length ({result_length} chars)",
                            "key_info": self._extract_key_info(result),
                            "full_data_available": True
                        }
                    else:
                        # For other data types, keep the structure but truncate values
                        truncated_results[tool_name] = self._truncate_dict_values(result)
                else:
                    # For string results, truncate to reasonable length
                    truncated_results[tool_name] = {
                        "summary": str(result)[:500] + "..." if len(str(result)) > 500 else str(result),
                        "truncated": len(str(result)) > 500
                    }
            else:
                # Result fits within limit, keep it as is
                truncated_results[tool_name] = result
                total_length += result_length
        
        return truncated_results
    
    def _extract_key_info(self, data: Dict) -> Dict:
        """Extract key information from long data structures"""
        key_info = {}
        
        # Always preserve essential fields
        essential_fields = ["error", "description", "symbol", "price", "change_percent", "pe_ratio", "revenue_growth", "earnings_growth"]
        for field in essential_fields:
            if field in data:
                key_info[field] = data[field]
        
        if "data" in data:
            # For news data, keep only first few items
            if isinstance(data["data"], list) and len(data["data"]) > 0:
                key_info["count"] = len(data["data"])
                key_info["sample"] = data["data"][:2] if len(data["data"]) > 2 else data["data"]
            else:
                key_info["data"] = data["data"]
        
        # Preserve any other important fields that might be present
        for key, value in data.items():
            if key not in key_info and isinstance(value, (int, float, str)) and len(str(value)) < 100:
                key_info[key] = value
        
        return key_info
    
    def _truncate_dict_values(self, data: Dict, max_value_length: int = 200) -> Dict:
        """Truncate long string values in a dictionary while preserving structure"""
        truncated = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_value_length:
                truncated[key] = value[:max_value_length] + "..."
            elif isinstance(value, dict):
                # Recursively truncate nested dictionaries
                truncated[key] = self._truncate_dict_values(value, max_value_length)
            elif isinstance(value, list):
                # For lists, keep first few items and truncate long ones
                if len(value) > 5:
                    truncated[key] = value[:5] + [f"... and {len(value) - 5} more items"]
                else:
                    truncated[key] = value
            else:
                truncated[key] = value
        return truncated
    
    def _is_growth_analysis_query(self, query: str) -> bool:
        """Check if the query is asking about growth potential for STOCKS (not crypto)"""
        # Skip crypto queries - they should use Monte Carlo simulation instead
        crypto_keywords = ['bitcoin', 'btc', 'crypto', 'cryptocurrency', 'eth', 'ethereum', 'ada', 'sol']
        query_lower = query.lower()
        
        # If this is a crypto query, don't treat it as a growth analysis query
        if any(crypto in query_lower for crypto in crypto_keywords):
            return False
        
        # Only handle stock growth analysis queries
        growth_keywords = [
            'growth', 'future', 'potential', 'outlook', 'prospects',
            'good investment', 'worth buying', 'should i buy',
            'growth potential', 'future growth', 'investment potential'
        ]
        
        return any(keyword in query_lower for keyword in growth_keywords)
    
    def _handle_growth_analysis_query(self, query: str, tool_results: Dict) -> str:
        """Handle growth analysis queries efficiently without LLM processing"""
        try:
            # Extract symbol from query or tool results
            symbol = None
            
            # Look for symbol in tool results
            for tool_name, result in tool_results.items():
                if tool_name == "get_stock_fundamentals" and "error" not in result:
                    # Try to extract symbol from fundamentals
                    if isinstance(result, dict):
                        symbol = result.get("symbol", None)
                        break
            
            # If no symbol found, try to extract from query
            if not symbol:
                import re
                symbol_match = re.search(r'\b([A-Z]{1,5})\b', query.upper())
                if symbol_match:
                    symbol = symbol_match.group(1)
            
            if not symbol:
                return "❌ **Unable to identify stock symbol**\n\nPlease specify a stock symbol (e.g., 'Is AAPL a good growth stock?')"
            
            # Get fundamentals data
            fundamentals = None
            for tool_name, result in tool_results.items():
                if tool_name == "get_stock_fundamentals" and "error" not in result:
                    fundamentals = result
                    break
            
            if not fundamentals or "error" in fundamentals:
                return f"""❌ **Unable to analyze {symbol} growth potential**

**Issue:** Could not retrieve fundamental data for {symbol}

💡 **Try:**
1. Verify the stock symbol is correct
2. Check if the stock is actively traded
3. Try again in a few minutes
4. Ask for specific data: 'What's the P/E ratio for {symbol}?'"""
            
            # Use the specialized growth analysis method
            return self._analyze_growth_potential(symbol, fundamentals)
            
        except Exception as e:
            return f"""❌ **Error analyzing growth potential**

**Error Details:** {str(e)}

💡 **What to do:**
1. Try rephrasing your question
2. Check if you included a stock symbol
3. Make sure the stock data is available
4. Try again in a few minutes"""
    
    def _analyze_growth_potential(self, symbol: str, fundamentals: Dict, news: Dict = None) -> str:
        """Analyze growth potential for a stock based on fundamentals and news"""
        try:
            # Extract key metrics
            pe_ratio = fundamentals.get('pe_ratio', 0)
            forward_pe = fundamentals.get('forward_pe', 0)
            revenue_growth = fundamentals.get('revenue_growth', 0)
            earnings_growth = fundamentals.get('earnings_growth', 0)
            debt_to_equity = fundamentals.get('debt_to_equity', 0)
            return_on_equity = fundamentals.get('return_on_equity', 0)
            
            # Analyze growth potential
            analysis = []
            score = 0
            
            # P/E Analysis
            if pe_ratio > 0:
                if pe_ratio < 15:
                    analysis.append("📈 **P/E Ratio**: Low P/E suggests good value and growth potential")
                    score += 2
                elif pe_ratio < 25:
                    analysis.append("📊 **P/E Ratio**: Moderate P/E indicates reasonable valuation")
                    score += 1
                else:
                    analysis.append("⚠️ **P/E Ratio**: High P/E suggests high growth expectations")
                    score += 0
            
            # Forward P/E Analysis
            if forward_pe > 0 and pe_ratio > 0:
                if forward_pe < pe_ratio:
                    analysis.append("🚀 **Forward P/E**: Lower than current P/E suggests earnings growth expected")
                    score += 2
                else:
                    analysis.append("📉 **Forward P/E**: Higher than current P/E suggests earnings decline expected")
                    score -= 1
            
            # Growth Metrics
            if revenue_growth > 0.1:
                analysis.append(f"📈 **Revenue Growth**: Strong {revenue_growth*100:.1f}% growth indicates expanding business")
                score += 2
            elif revenue_growth > 0.05:
                analysis.append(f"📊 **Revenue Growth**: Moderate {revenue_growth*100:.1f}% growth shows steady expansion")
                score += 1
            else:
                analysis.append(f"📉 **Revenue Growth**: Low {revenue_growth*100:.1f}% growth suggests limited expansion")
                score -= 1
            
            if earnings_growth > 0.15:
                analysis.append(f"💰 **Earnings Growth**: Excellent {earnings_growth*100:.1f}% growth shows strong profitability")
                score += 2
            elif earnings_growth > 0.08:
                analysis.append(f"📊 **Earnings Growth**: Good {earnings_growth*100:.1f}% growth indicates solid earnings")
                score += 1
            else:
                analysis.append(f"📉 **Earnings Growth**: Low {earnings_growth*100:.1f}% growth suggests weak earnings")
                score -= 1
            
            # Financial Health
            if debt_to_equity < 0.5:
                analysis.append("🏦 **Financial Health**: Low debt levels provide financial flexibility")
                score += 1
            elif debt_to_equity > 1.0:
                analysis.append("⚠️ **Financial Health**: High debt levels may limit growth opportunities")
                score -= 1
            
            if return_on_equity > 0.15:
                analysis.append(f"💎 **ROE**: Strong {return_on_equity*100:.1f}% return on equity shows efficient capital use")
                score += 1
            elif return_on_equity < 0.08:
                analysis.append(f"📉 **ROE**: Low {return_on_equity*100:.1f}% return on equity suggests poor capital efficiency")
                score -= 1
            
            # Overall Assessment
            if score >= 6:
                growth_outlook = "🚀 **EXCELLENT** growth potential"
                recommendation = "This stock shows strong fundamentals for future growth"
            elif score >= 3:
                growth_outlook = "📈 **GOOD** growth potential"
                recommendation = "This stock has solid growth prospects with some areas for improvement"
            elif score >= 0:
                growth_outlook = "📊 **MODERATE** growth potential"
                recommendation = "This stock has mixed growth indicators - proceed with caution"
            else:
                growth_outlook = "📉 **LIMITED** growth potential"
                recommendation = "This stock shows concerning growth indicators - consider alternatives"
            
            # Format the response
            response = f"""## {symbol} Growth Analysis 📊

{growth_outlook}

### Key Metrics Analysis:
{chr(10).join(analysis)}

### Growth Score: {score}/10

### Recommendation:
{recommendation}

### Next Steps:
- Monitor quarterly earnings reports
- Watch for revenue growth trends
- Consider market conditions and industry outlook
- Consult with a financial advisor for personalized advice

*Analysis based on fundamental data. Past performance doesn't guarantee future results.*"""
            
            return response
            
        except Exception as e:
            return f"Error analyzing growth potential: {str(e)}"
    
    def _get_helpful_fallback_response(self, user_query: str) -> str:
        """Provide a helpful response when tool analysis fails"""
        return f"""🤖 **I'm here to help with your financial questions!**

💡 **Try asking me about:**
- **Stock prices:** "What's the price of AAPL?"
- **Company fundamentals:** "Show me fundamentals for MSFT"
- **Portfolio:** "What's in my portfolio?"
- **Market overview:** "Give me a market summary"
- **Cryptocurrency:** "What's the Bitcoin price?"

🔍 **Be specific:** Include stock symbols (AAPL, GOOGL, MSFT) for best results.

📚 **Need help?** Ask "What can you do?" to see all my capabilities.

**Your question:** "{user_query}"
"""
    
    def _get_stock_analysis(self, stock_data: Dict) -> str:
        """Generate simple stock analysis based on data"""
        try:
            price = stock_data.get('price', 0)
            change_percent = stock_data.get('change_percent', 0)
            pe_ratio = stock_data.get('pe_ratio', 0)
            
            analysis = []
            
            if change_percent > 0:
                analysis.append(f"Stock is up {change_percent:.2f}% today")
            elif change_percent < 0:
                analysis.append(f"Stock is down {abs(change_percent):.2f}% today")
            else:
                analysis.append("Stock is unchanged today")
            
            if pe_ratio > 0:
                if pe_ratio < 15:
                    analysis.append("P/E ratio suggests good value")
                elif pe_ratio < 25:
                    analysis.append("P/E ratio is reasonable")
                else:
                    analysis.append("P/E ratio is high - growth expected")
            
            return " | ".join(analysis) if analysis else "Data available for analysis"
            
        except Exception as e:
            return "Analysis not available"
    
    def get_available_functions(self) -> List[Dict]:
        """Get list of available functions for the agent"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "type": "function"
            }
            for tool in self.tools
        ]
    
    def get_agent_status(self) -> Dict:
        """Get agent status and configuration"""
        return {
            "openai_configured": bool(self.config.OPENAI_API_KEY),
            "pushover_configured": bool(self.config.PUSHOVER_USER_KEY and self.config.PUSHOVER_APP_TOKEN),
            "available_tools": len(self.tools),
            "database_connected": True,
            "notification_system_running": self.notification_system.running
        }

    def test_llm_connection(self) -> dict:
        """Test the LLM connection and return status information"""
        status = {
            "llm_configured": False,
            "api_key_set": False,
            "connection_test": False,
            "error": None,
            "details": {}
        }
        
        # Check if API key is set
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            status["api_key_set"] = True
            status["details"]["api_key_length"] = len(api_key)
            status["details"]["api_key_preview"] = f"{api_key[:8]}...{api_key[-4:]}"
        else:
            status["error"] = "OPENAI_API_KEY not set in environment variables"
            return status
        
        # Check if LLM is initialized
        if self.llm:
            status["llm_configured"] = True
            
            # Test the connection
            try:
                test_response = self.llm.invoke("Test")
                status["connection_test"] = True
                status["details"]["test_response"] = str(test_response)[:100] + "..." if len(str(test_response)) > 100 else str(test_response)
            except Exception as e:
                status["connection_test"] = False
                status["error"] = f"LLM connection test failed: {str(e)}"
        else:
            status["error"] = "LLM not initialized"
        
        return status
    
    def get_llm_status(self) -> str:
        """Get a human-readable status of the LLM configuration"""
        status = self.test_llm_connection()
        
        if status["llm_configured"] and status["connection_test"]:
            return "✅ **LLM Status: Fully Operational**\n\n- OpenAI API key configured\n- LLM initialized successfully\n- Connection test passed\n- AI features available"
        
        elif status["llm_configured"] and not status["connection_test"]:
            return f"⚠️ **LLM Status: Partially Configured**\n\n- OpenAI API key configured\n- LLM initialized but connection test failed\n- Error: {status['error']}\n\n**To troubleshoot:**\n1. Check your internet connection\n2. Verify your API key is valid\n3. Check OpenAI service status"
        
        elif status["api_key_set"] and not status["llm_configured"]:
            return f"⚠️ **LLM Status: Configuration Issue**\n\n- OpenAI API key is set\n- LLM failed to initialize\n- Error: {status['error']}\n\n**To troubleshoot:**\n1. Check your API key format\n2. Verify you have sufficient OpenAI credits\n3. Try restarting the application"
        
        else:
            return f"❌ **LLM Status: Not Configured**\n\n- OpenAI API key not set\n- LLM not initialized\n- Error: {status['error']}\n\n**To fix this:**\n1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)\n2. Add it to your `.env` file: `OPENAI_API_KEY=your_key_here`\n3. Restart the application"


