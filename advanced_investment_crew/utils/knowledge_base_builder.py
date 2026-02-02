# utils/knowledge_base_builder.py
from typing import List, Dict
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

class AdvancedKnowledgeBase:
    """
    Comprehensive knowledge base with multiple specialized collections
    """
    
    def __init__(self, persist_directory: str = "./data/knowledge_base"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Multiple specialized collections
        self.collections = {
            "historical_patterns": self._init_collection("historical_patterns"),
            "geopolitical_events": self._init_collection("geopolitical_events"),
            "economic_theories": self._init_collection("economic_theories"),
            "market_crashes": self._init_collection("market_crashes"),
            "turkey_history": self._init_collection("turkey_history"),
            "sector_dynamics": self._init_collection("sector_dynamics"),
            "investment_strategies": self._init_collection("investment_strategies"),
            "risk_frameworks": self._init_collection("risk_frameworks"),
            "regulatory_changes": self._init_collection("regulatory_changes"),
            "company_case_studies": self._init_collection("company_case_studies")
        }
    
    def _init_collection(self, name: str):
        return Chroma(
            collection_name=name,
            embedding_function=self.embeddings,
            persist_directory=f"{self.persist_directory}/{name}"
        )
    
    def populate_historical_patterns(self):
        """
        Populate with historical market patterns and their outcomes
        """
        patterns = [
            {
                "pattern": "2008 Financial Crisis",
                "context": """
                - Subprime mortgage crisis
                - Lehman Brothers collapse
                - Global credit freeze
                - Central bank interventions
                - Turkey impact: BIST fell 56%, TRY depreciated 25%
                - Recovery pattern: V-shaped in EM, U-shaped in developed
                - Sectors affected: Finance most, technology resilient
                - Policy response: QE, fiscal stimulus
                - Lessons: Liquidity is king, diversification matters
                """,
                "investment_implications": "...",
                "similar_current_conditions": []
            },
            {
                "pattern": "2018 Turkey Currency Crisis",
                "context": """
                - US tariffs and pastor Brunson crisis
                - CBRT credibility issues
                - TRY lost 30% in weeks
                - Capital controls considered
                - Banking sector stress
                - Recovery: Gradual with policy normalization
                - Sectors: Exporters benefited, importers struggled
                - Lessons: Political risk premium, FX hedging critical
                """,
                "investment_implications": "...",
                "similar_current_conditions": []
            },
            {
                "pattern": "COVID-19 Pandemic Market Shock",
                "context": """
                - Global lockdowns March 2020
                - Fastest bear market in history
                - Unprecedented fiscal and monetary response
                - Turkey: BIST fell 25%, recovered to new highs
                - Winners: Tech, healthcare, e-commerce
                - Losers: Travel, hospitality, retail
                - New normal: Remote work, digital transformation
                - Lessons: Adaptability, secular trends matter
                """,
                "investment_implications": "...",
                "similar_current_conditions": []
            }
        ]
        
        documents = [
            Document(
                page_content=f"{p['pattern']}\n{p['context']}",
                metadata={"pattern": p["pattern"], "type": "historical"}
            )
            for p in patterns
        ]
        
        self.collections["historical_patterns"].add_documents(documents)
    
    def populate_geopolitical_knowledge(self):
        """
        Geopolitical frameworks and historical precedents
        """
        geopolitical_data = [
            {
                "event": "Turkey's Strategic Balancing Act",
                "analysis": """
                HISTORICAL CONTEXT:
                - Ottoman Empire's Eastern Question legacy
                - Cold War non-alignment attempts
                - Post-Cold War NATO integration
                - 2000s EU accession process
                - 2010s pivot to multi-vectorism
                
                CURRENT DYNAMICS:
                - NATO member but S-400 purchaser
                - EU candidate but authoritarian drift
                - US ally but strategic divergences
                - Russia partner in energy and tourism
                - China economic partner (BRI)
                
                INVESTMENT IMPLICATIONS:
                - Policy unpredictability premium
                - Sanction risk always present
                - Opportunities in defense, infrastructure
                - Energy corridor strategic value
                - Geopolitical rent extraction
                
                SIMILAR HISTORICAL CASES:
                - India's non-alignment
                - Yugoslavia's Third Way
                - Egypt under Nasser
                
                RISK INDICATORS:
                - US Congress sanctions bills
                - NATO summit outcomes
                - EU progress reports
                - Russia-Turkey incidents
                """,
                "sectors_affected": ["defense", "energy", "tourism", "construction"],
                "monitoring_indicators": []
            },
            {
                "event": "US-China Tech Cold War",
                "analysis": """
                PHASES:
                1. Trade war (2018-2019): Tariffs
                2. Tech decoupling (2019-2021): Huawei, TikTok
                3. Chip wars (2022-present): Export controls
                4. AI competition (ongoing): Compute restrictions
                
                TURKEY POSITION:
                - Not forced to choose (yet)
                - Benefits from both markets
                - Risks: Secondary sanctions, tech access
                - Opportunities: Manufacturing alternative
                
                INVESTMENT IMPLICATIONS:
                - Semiconductor supply chain critical
                - Dual supply chain strategies
                - Turkey as neutral manufacturing hub
                - Defense tech indigenous development
                
                SIMILAR PATTERNS:
                - US-Soviet tech competition
                - Japan semiconductor agreement 1986
                
                FORWARD INDICATORS:
                - CHIPS Act implementation
                - China semiconductor breakthroughs
                - Taiwan strait tensions
                - Export control expansions
                """,
                "sectors_affected": ["technology", "semiconductors", "manufacturing"],
                "monitoring_indicators": []
            }
        ]
        
        documents = [
            Document(
                page_content=f"{d['event']}\n{d['analysis']}",
                metadata={"event": d["event"], "type": "geopolitical"}
            )
            for d in geopolitical_data
        ]
        
        self.collections["geopolitical_events"].add_documents(documents)
    
    def populate_economic_theories(self):
        """
        Economic frameworks and their application
        """
        theories = [
            {
                "theory": "Turkish Economic Model Critique",
                "content": """
                THEORETICAL FRAMEWORK:
                - Growth-first approach vs orthodox economics
                - Interest rate-inflation relationship debate
                - Current account deficit financing models
                - Credit-driven growth sustainability
                
                HISTORICAL PRECEDENTS:
                - Latin American populism (1970s-1980s)
                - Asian Tigers credit booms
                - Turkish boom-bust cycles (1994, 2001, 2018)
                
                CURRENT APPLICATION:
                - Low interest rates despite high inflation
                - Credit expansion through state banks
                - Construction and mega-projects focus
                - Export competitiveness via weak currency
                
                INVESTMENT IMPLICATIONS:
                - High volatility environment
                - FX hedging essential
                - Real asset preference (real estate, gold)
                - Exporter vs importer dynamics
                - Banking sector credit quality concerns
                
                RISK SCENARIOS:
                - Balance of payments crisis
                - Banking sector stress
                - Inflation spiral
                - Capital controls
                
                OPPORTUNITY SCENARIOS:
                - Policy normalization
                - External financing improvement
                - Structural reforms
                - EU relations improvement
                """,
                "application": "Turkey macro analysis",
                "related_indicators": []
            }
        ]
        
        documents = [
            Document(
                page_content=f"{t['theory']}\n{t['content']}",
                metadata={"theory": t["theory"], "type": "economic_theory"}
            )
            for t in theories
        ]
        
        self.collections["economic_theories"].add_documents(documents)
    
    def query_relevant_context(
        self,
        query: str,
        collections: List[str] = None,
        k: int = 5
    ) -> Dict[str, List[Document]]:
        """
        Query multiple collections for relevant context
        """
        if collections is None:
            collections = list(self.collections.keys())
        
        results = {}
        for collection_name in collections:
            if collection_name in self.collections:
                results[collection_name] = self.collections[collection_name].similarity_search(
                    query, k=k
                )
        
        return results
