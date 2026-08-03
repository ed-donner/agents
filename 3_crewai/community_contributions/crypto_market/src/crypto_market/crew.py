from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage


class TrendingCrypto(BaseModel):
    """A trending crypto"""
    name: str = Field(description="The name of the trending crypto")
    symbol: str = Field(description="The crypto ticker symbol for the trending crypto")
    reason: str = Field(description="Reason why the crypto is trending")

class TrendingCryptoList(BaseModel):
    """The list of trending cryptos """
    cryptos: List[TrendingCrypto] = Field(description="List of cryptos trending")

class CryptoFundamentals(BaseModel):
    """Fundamental analysis of a cryptocurrency"""
    name: str = Field(description="Cryptocurrency name")
    symbol: str = Field(description="Crypto ticker symbol")
    market_position: str = Field(description="Current market position and competitive analysis")
    technology_analysis: str = Field(description="Technical assessment of the blockchain/protocol")
    tokenomics: str = Field(description="Token distribution, supply mechanics, and utility")
    tvl_data: str = Field(description="Total Value Locked and DeFi metrics if applicable")
    team_background: str = Field(description="Team and development background")

class CryptoFundamentalsList(BaseModel):
    """List of fundamental analyses for all trending cryptos"""
    research: List[CryptoFundamentals] = Field(description="Comprehensive research on all trending cryptos")

class CryptoRiskAssessment(BaseModel):
    """Risk assessment for a cryptocurrency"""
    name: str = Field(description="Cryptocurrency name")
    symbol: str = Field(description="Crypto ticker symbol")
    regulatory_risk: str = Field(description="Regulatory compliance and legal risks")
    technical_risk: str = Field(description="Smart contract and technical vulnerabilities")
    market_risk: str = Field(description="Volatility and liquidity risks")
    overall_risk_score: str = Field(description="Overall risk rating (Low/Medium/High)")

class CryptoRiskAssessmentList(BaseModel):
    """List of risk assessments for all cryptos"""
    risk_assessments: List[CryptoRiskAssessment] = Field(description="Risk analysis for all researched cryptos")

class CryptoInvestmentDecision(BaseModel):
    """Final investment decision with rationale"""
    selected_crypto: str = Field(description="Name of the chosen cryptocurrency")
    selected_symbol: str = Field(description="Ticker symbol of chosen crypto")
    investment_thesis: str = Field(description="Detailed rationale for selection")
    rejected_cryptos: List[str] = Field(description="Names of cryptos not selected and reasons why")



@CrewBase
class CryptoMarket():
    """CryptoMarket crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def crypto_news_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['crypto_news_analyst'],
            tools=[SerperDevTool()],
        )

    @agent
    def defi_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['defi_researcher'],
            tools=[SerperDevTool()],
        )
        
    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_analyst'],
            tools=[SerperDevTool()],
        )
        
    @agent
    def portfolio_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['portfolio_manager'],
            verbose=True
        )

    @task
    def find_trending_cryptos(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_cryptos'],
            output_pydantic=TrendingCryptoList,
        )

    @task
    def research_crypto_fundamentals(self) -> Task:
        return Task(
            config=self.tasks_config['research_crypto_fundamentals'],
            output_pydantic=CryptoFundamentalsList,
        )
        
    @task
    def assess_crypto_risks(self) -> Task:
        return Task(
            config=self.tasks_config['assess_crypto_risks'],
            output_pydantic=CryptoRiskAssessmentList,
        )
        
    @task
    def select_crypto_investment(self) -> Task:
        return Task(
            config=self.tasks_config['select_crypto_investment'],
            output_pydantic=CryptoInvestmentDecision,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CryptoMarket crew"""
        
        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True,
        )
       
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            memory=True,
            manager_agent=manager,
            long_term_memory = LongTermMemory(
                storage=LTMSQLiteStorage(
                    db_path="./memory/long_term_memory_storage.db"
                )
            ),
            # Short-term memory for current context using RAG
            short_term_memory = ShortTermMemory(
                storage = RAGStorage(
                        embedder_config={
                            "provider": "openai",
                            "config": {
                                "model": 'text-embedding-3-small'
                            }
                        },
                        type="short_term",
                        path="./memory/"
                    )
            ),
            # Entity memory for tracking key information about entities
            entity_memory = EntityMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {
                            "model": 'text-embedding-3-small'
                        }
                    },
                    type="short_term",
                    path="./memory/"
                )
            ),
        )
