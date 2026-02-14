
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool
from openai import OpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import uuid
from pprint import pprint
from documents_retrievers import MedicalDiseaseQAndARetriever, MedicalDeviceManualsRetriever, SEMANTIC_RETRIEVAL, HYBRID_RETRIEVAL_RERANK
import asyncio
import nest_asyncio

load_dotenv(override=True)

source_disease_qna_disp = "Medical Disease Questions and Answers"
source_device_manuals_disp = "Medical Device Manuals"
source_web_search_disp = 'Web Search'
source_disease_qna = "medical_disease_qna"
source_device_manuals = "medical_device_manuals"
source_web_search = 'web_search'
source_disp_dict = {
            source_disease_qna: source_disease_qna_disp, 
            source_device_manuals: source_device_manuals_disp, 
            source_web_search: source_web_search_disp
            }

YES = 'yes'
NO = 'no'
MAX_ITERATION = 3
N_RESULTS = 3 

class GraphState(TypedDict):
    query: str
    source: str
    raw_results: str
    context: str
    filter_out_all_retrieved_documents: bool
    pass_relevance_test: str
    iteration_count: int
    generation: str
    strategy: str

class RouteOutput(BaseModel):
    """Route a user query to the most relevant datasource."""
    datasource: Literal[source_disease_qna, source_device_manuals] = Field(
        ...,
        description=f"Given a user question choose to route it to '{source_disease_qna}' or '{source_device_manuals}'",
    )

class RelevanceOutput(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: Literal[YES, NO] = Field(
        ...,
        description=f"Retrieved documents are relevant to the question, 'yes' or 'no'",
    ) 

class AgenticRAG:
    def __init__(self):
        self.medical_disease_qna_retriever = None
        self.medical_device_manuals_retriever = None
        self.ollama_via_openai = None
        self.router_llm_with_output = None
        self.checker_llm_with_output = None
        self.embedding_model = None
        self.agentic_rag = None
        self.config = config = {"configurable": {"thread_id": str(uuid.uuid4()), "recursion_limit": 50}}
        self.memory = MemorySaver()
        self.search_tool = None

    async def setup(self, strategy = HYBRID_RETRIEVAL_RERANK):
        self.strategy = strategy
        self.medical_disease_qna_retriever = MedicalDiseaseQAndARetriever()
        await self.medical_disease_qna_retriever.setup_hybrid_retriever()
        self.medical_device_manuals_retriever = MedicalDeviceManualsRetriever()
        await self.medical_device_manuals_retriever.setup_hybrid_retriever()

        self.ollama_via_openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        router_llm = ChatOpenAI(model="gpt-5-nano")
        self.router_llm_with_output = router_llm.with_structured_output(RouteOutput)
        checker_llm = ChatOpenAI(model="gpt-5-nano", reasoning_effort="low")
        self.checker_llm_with_output = checker_llm.with_structured_output(RelevanceOutput)

        serper = GoogleSerperAPIWrapper(k= N_RESULTS)
        self.search_tool =Tool(
            name="search",
            func=serper.run,
            description="Use this tool when you want to get the results of an online web search"
        )
        await self.build_graph()


    ###########################################################
    #####  Route to an appropriate Retriever to retrieve documents
    ########################################################### 
    # All node should return a GraphState.  That's how LangGraph become stateful  
    def route(self, state: GraphState) -> GraphState:
        """Agentic router: decides which retriever to use."""
        print("---ROUTER to VECTORDB RETRIEVER---")
        query = state["query"]
        system_message = f"You are a routing agent. Based on the user query, decide where to look for information."
        user_message = f"""
        You are routing an user query, respond ONLY with one of options:
        - {source_disease_qna}: if it's about general medical disease information, symptoms, or treatment.
        - {source_device_manuals}: if it's about medical devices,  manuals, or instructions.
        User query: "{query}"
        """
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]
        result = self.router_llm_with_output.invoke(messages)
        print(f"---ROUTER DECISION: {result.datasource}---")
        state["source"] = result.datasource
        return state

    def route_decision(self, state: GraphState) -> str:
        return state["source"]    

    ##############################################
    #####  Retrieval
    ##############################################
    def retrieve_from_disease_qna(self, state: GraphState) -> GraphState:
        """Retrieve top documents from ChromaDB Collection 1 (Medical Q&A Data) based on query."""
        print("---Retrieving from Medical Disease Q&A Collection---")
        # Retrieve based upon initialized strategy: semantic or hybrid
        state["strategy"] = self.strategy
        print(f"---strategy= {state["strategy"]}---")
        results = self.medical_disease_qna_retriever.retrieve(state["query"], k = N_RESULTS, strategy = self.strategy)
        state["raw_results"] = results
        state["source"] = source_disease_qna
        return state

    def retrieve_from_device_manual(self, state: GraphState) -> GraphState:
        """Retrieve top documents from ChromaDB Collection 2 ((Medical Device Manuals Data)) based on query."""
        print("---Retrieving from Medical Device Manual Collection---")
        # Retrieve based upon initialized strategy: semantic or hybrid
        state["strategy"] = self.strategy
        print(f"---strategy= {state["strategy"]}---")
        results = self.medical_device_manuals_retriever.retrieve(state["query"], k = N_RESULTS, strategy = self.strategy)
        state["raw_results"] = results
        state["source"] = source_device_manuals
        return state


    ###########################################################
    #####  Check if the retrieved documents are relevant
    ########################################################### 
    def check_relevance(self, state: GraphState) -> GraphState:
        """Determine whether the retrieved documents are relevant or not."""
        print("---CONTEXT RELEVANCE CHECKER---")
        query = state['query']
        documents, context = state["raw_results"], state["raw_results"]
        if state['source'] in [source_disease_qna, source_device_manuals]:
            if not documents:
                print("---FILTER OUT ALL RETRIEVED DOCUMENTS, RELEVANCE RESULT: no---")
                state['filter_out_all_retrieved_documents'] = True
                state['pass_relevance_test'] = NO
                return state
            context = '\n'.join(documents)  # Override in the case of VectorDB

        state['context'] = context
        
        system_message = "You are a grader assessing relevance of a retrieved document to a user question."
        user_message = f"""
        Your assessment need to be precise.
        Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question.
        Retrieved document: \n\n '{context}' \n\n User question: '{query}'
        """
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]
        result = self.checker_llm_with_output.invoke(messages)
        print(f"---RELEVANCE RESULT: {result.binary_score}---")
        state['pass_relevance_test'] = result.binary_score

        iteration_count = state.get("iteration_count", 0)
        state["iteration_count"] = iteration_count + 1
        ## Limiting to MAX_ITERATION
        if state["iteration_count"] >= MAX_ITERATION:
            print("---MAX ITERATIONS REACHED, FORCING 'Yes'---")
            state["pass_relevance_test"] = YES

        return state
    
    def relevance_decision(self, state: GraphState) -> str:
        return state['pass_relevance_test']    


    ###########################################################
    #####  Fallback to web search if we cannot retrieve relevant documents from vectorDB
    ###########################################################
    # Choose among 1) Use Serper.run directly, 2) Use Serper as a standalone Langchain Tool 3) Use LLM Bind tool
    # because Serper is the only tool and LLM does not have add-on value here.  Try option 2).  1) should be outside of Langgraph workflow
    def web_search(self, state: GraphState) -> GraphState:
        """Perform web search using Google Serper API."""
        print("---PERFORMING WEB SEARCH---")
        search_results = self.search_tool.invoke(state["query"])
        # print(search_results)
        state["raw_results"] = search_results
        state["source"] = source_web_search

        return state


    def get_llm_response(self, prompt: str) -> str:
        """Function to get response from simple LLM prompt (user message)"""
        messages = [{"role": "user", "content": prompt}]
        # Simple OpenAI chat message
        response = self.ollama_via_openai.chat.completions.create(
            model="llama3.2",
            messages=messages,
            seed=42
        )
        return response.choices[0].message.content


    ###########################################################
    #####  AUGMENTED GENERATION
    ###########################################################
    def augment_generate(self, state: GraphState) -> GraphState:
        """Construct the RAG-style message"""
        print("---AUGMENT GENERATE ON CONTEXT---")
        query = state["query"]
        context = state["context"]
        source_disp = source_disp_dict.get(state["source"], 'Web Search')
        prompt = f"""
        Please provide a to-the-point answer (less than 500 words) to the question based on the provided context.
        Context: "{context}"
        Question: "{query}"
        Please elaborate what can be applied under what circumstance if the context provides such information.
        Please also cite the source as "{source_disp}"
        """
        answer = self.get_llm_response(prompt)
        state["generation"] = answer
        return state


    async def build_graph(self):
        graph_builder = StateGraph(GraphState)
        graph_builder.add_node("router", self.route)
        graph_builder.add_node("disease_qna_retriever", self.retrieve_from_disease_qna)
        graph_builder.add_node("device_manual_retriever", self.retrieve_from_device_manual)
        graph_builder.add_node("relevance_checker", self.check_relevance)
        graph_builder.add_node("web_searcher", self.web_search)
        graph_builder.add_node("generator", self.augment_generate)

        # Add edges
        graph_builder.add_conditional_edges("router", self.route_decision, 
            {source_disease_qna: "disease_qna_retriever", source_device_manuals: "device_manual_retriever"})
        graph_builder.add_edge("disease_qna_retriever", "relevance_checker")
        graph_builder.add_edge("device_manual_retriever", "relevance_checker")
        graph_builder.add_edge("web_searcher", "relevance_checker")
        graph_builder.add_conditional_edges("relevance_checker", self.relevance_decision, {YES: "generator", NO: "web_searcher"})

        graph_builder.add_edge("generator", END)
        graph_builder.add_edge(START, "router")
        self.agentic_rag = graph_builder.compile(checkpointer=self.memory)

   

    async def run_query(self, input_state: GraphState):
        async for step in self.agentic_rag.astream(input_state, config=self.config):
            for key, value in step.items():
                pprint(f"Finished running: {key}:")
        pprint(value["generation"])

    def cleanup(self):
        # a placeholder fo now.
        pprint('User close browser and free up resources')

    async def run(self, query: str):
        input_state = GraphState(query=query, iteration_count=0, filter_out_all_retrieved_documents=False)
        async for step in self.agentic_rag.astream(input_state, config=self.config):
            for key, value in step.items():
                yield f"### Finished running: '{key.upper()}'"
                if key == 'router':
                    yield f"#### ROUTER DECISION: `{value['source']}`"
                elif key in ["disease_qna_retriever","device_manual_retriever"]:
                    yield f"#### STRATEGY: `{value['strategy']}`"   
                elif key == 'relevance_checker':
                    yield f"#### RELEVANCE DECISION: `{value['pass_relevance_test']}`"
                    if value.get("iteration_count", 0) >= MAX_ITERATION:
                        yield "**MAX ITERATIONS REACHED, FORCING 'Yes' to relevance**"
                    if value['source'] in [source_disease_qna, source_device_manuals] and \
                       value.get('filter_out_all_retrieved_documents', False):
                       yield "**Unable to retrieve documents met quality criteria, Fallback to Web Search!**"
                    if value['pass_relevance_test'] == YES:
                        yield "### START AUGMENTED GENERATION using CONTEXT---"
        yield f'##### {value["generation"]}'
          

if __name__ == '__main__':
    nest_asyncio.apply()
    instance = AgenticRAG()
    asyncio.run(instance.setup(HYBRID_RETRIEVAL_RERANK))
    # asyncio.run(instance.run_query({"query": "What are the treatments for Kawasaki disease?"}))
    # asyncio.run(instance.run_query({"query": "What's the incubation period of measles?"}))
    # asyncio.run(instance.run_query({"query": "When will a measles patient have the first appearance symptons after he or she is exposed to a pathogen?"}))
    # asyncio.run(instance.run_query({"query": "How do patients contract hantavirus pulmonary syndrome?"}))
    asyncio.run(instance.run_query({"query": "what is the most aggressive form of brain tumor?"}))
    # asyncio.run(instance.run_query({"query": "What are the usage of Dialysis Machine Device?"}))
    # asyncio.run(instance.run_query({"query": "Which devices are suitable for neonatal patients?"}))