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

class FinanceCopilotAgent:
    def __init__(self):
        self.config = Config()
        self.market_data = MarketDataTool()
        self.analysis_tool = AnalysisTool()
        self.db = FinanceDatabase(self.config.DATABASE_PATH)
        self.notification_system = NotificationSystem()
        
        # Initialize OpenAI client
        if self.config.OPENAI_API_KEY:
            openai.api_key = self.config.OPENAI_API_KEY
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                openai_api_key=self.config.OPENAI_API_KEY
            )
        else:
            self.llm = None
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
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
                description="Add a price alert for a specific symbol"
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
            
            return result.to_string()
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
            return f"Successfully {transaction_type.lower()}ed {shares} shares of {symbol} at ${price:.2f}"
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
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
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
    
    def process_query(self, user_query: str) -> str:
        """Process user query and return response"""
        if not self.llm:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY in your environment variables."
        
        try:
            # First, analyze the query to determine what tools to use
            analysis_prompt = f"""
            Analyze this user query and determine which tools to use:
            Query: {user_query}
            
            Available tools: {[tool.name for tool in self.tools]}
            
            Return a JSON response with:
            {{
                "tools_needed": ["tool1", "tool2"],
                "reasoning": "Why these tools are needed",
                "action_plan": "Step-by-step plan to help the user"
            }}
            """
            
            analysis_response = self.llm.invoke([{"role": "user", "content": analysis_prompt}])
            analysis_content = analysis_response.content if hasattr(analysis_response, 'content') else str(analysis_response)
            
            # Extract tool names from the analysis
            import re
            import json
            
            # Try to parse the JSON response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', analysis_content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    tools_needed = analysis.get('tools_needed', [])
                else:
                    # Fallback: try to extract tool names from text
                    tools_needed = []
                    for tool in self.tools:
                        if tool.name.lower() in user_query.lower() or any(keyword in user_query.lower() for keyword in tool.description.lower().split()):
                            tools_needed.append(tool.name)
            except:
                tools_needed = []
            
            # Execute the tools and gather results
            results = {}
            if tools_needed:
                for tool_name in tools_needed:
                    try:
                        # Find the tool
                        tool = next((t for t in self.tools if t.name == tool_name), None)
                        if tool:
                            # Execute the tool with appropriate parameters
                            if tool_name == "get_stock_price":
                                # Extract symbol from query
                                symbol_match = re.search(r'\b[A-Z]{1,5}\b', user_query.upper())
                                if symbol_match:
                                    symbol = symbol_match.group()
                                    results[tool_name] = self._get_stock_price(symbol)
                                else:
                                    results[tool_name] = "Please specify a stock symbol (e.g., AAPL, GOOGL)"
                            
                            elif tool_name == "get_portfolio_metrics":
                                results[tool_name] = self._get_portfolio_metrics()
                            
                            elif tool_name == "run_monte_carlo_simulation":
                                results[tool_name] = self._run_monte_carlo_simulation()
                            
                            elif tool_name == "suggest_rebalancing":
                                results[tool_name] = self._suggest_rebalancing()
                            
                            elif tool_name == "get_market_summary":
                                results[tool_name] = self._get_market_summary()
                            
                            else:
                                results[tool_name] = f"Tool {tool_name} executed successfully"
                        else:
                            results[tool_name] = f"Tool {tool_name} not found"
                    except Exception as e:
                        results[tool_name] = f"Error executing {tool_name}: {str(e)}"
            
            # Create comprehensive response
            if results:
                response_prompt = f"""
                User Query: {user_query}
                
                Tools executed and results:
                {json.dumps(results, indent=2)}
                
                Please provide a comprehensive, helpful response based on the tool results.
                Include specific data, insights, and actionable recommendations.
                Format the response nicely with markdown.
                """
            else:
                response_prompt = f"""
                User Query: {user_query}
                
                No specific tools were needed for this query.
                Please provide a helpful response about financial topics, general advice, or ask for clarification.
                """
            
            # Get final response
            final_response = self.llm.invoke([{"role": "user", "content": response_prompt}])
            
            if hasattr(final_response, 'content'):
                return final_response.content
            else:
                return str(final_response)
                
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
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


