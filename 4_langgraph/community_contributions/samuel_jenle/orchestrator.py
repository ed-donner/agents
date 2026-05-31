
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import uuid
from models import State, CodeDiff, BugFindings, StyleFindings, FinalReview

class Orchestrator:
    def __init__(self):
        self.bug_detector_llm = None
        self.style_reviewer_llm = None
        self.summarizer_llm = None
        self.code_extractor_llm = None
        self.graph = None
        self.memory = MemorySaver()
        self.orchestrator_id = str(uuid.uuid4())
    
    async def setup(self):
        self.code_extractor_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(CodeDiff)
        self.bug_detector_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(BugFindings)
        self.style_reviewer_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(StyleFindings)
        self.summarizer_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(FinalReview)
        await self.build_graph()

    def code_extractor(self, state: State) -> State:
        # extract code diff and language
        system_message = f"""You are a code extractor. Your job is to analyze the conversation and 
        extract the code diff and programming language being reviewed and then include a brief reply.
        Do not explain the code diff, just extract it and identify the language and include a brief reply to the user.
        Here are the messages you need to analyze:
        ## Messages:
        {state['messages'][-1].content}


        ## Instructions:
        - Extract the code diff from the messages, if present.
        - Identify the programming language of the code diff.
         """
        
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
        
        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.code_extractor_llm.invoke(messages)
        assistant_message = [{
            "role": "assistant",
            "content":  response.reply_content
        }]

        return {
            "messages": assistant_message,
            "code_diff": response.code_diff,
            "language": response.language
        }
    
    def code_extractor_router(self, state: State) -> str:
        if state["code_diff"] is None:
            return "END"
        else:
            return "bug_detector"
    
    def bug_detector(self, state: State):
        # use code_diff and language fields of state to find bugs
        system_message = f"""You are a bug detector for {state['language']} code. Here is the code diff you ned to analyze:
        ## Code Diff:
        {state['code_diff']}

        ## Instructions:
        - Analyze the code diff and identify any potential bugs.
        - For each bug, provide a description, the line number, and the severity (low, medium, high).
         """
        
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
        
        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.bug_detector_llm.invoke(messages)

        content = "The code is bug free"
        if response.bug_findings:
            content = "The code has one or more bugs"

        assistant_message = [
            {
                "role": "assistant",
                "content": content
            }
        ]
        return {
            "messages": assistant_message,
            "bug_findings": response.bug_findings
        }

    def style_reviewer(self, state: State):
        # use state.code_diff and state.language to find style issues
        system_message = f"""You are a style reviewer for {state['language']} code. Here is the code diff you ned to analyze:
        ## Code Diff:
        {state['code_diff']}

        ## Instructions:
        - Analyze the code diff and identify any style issues.
        - For each issue, provide a description, the line number, and the severity (low, medium, high).
         """
        
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
        
        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.style_reviewer_llm.invoke(messages)

        content = "The code follows the style guidelines"
        if response.style_findings:
            content = "The code has one or more style issues"

        assistant_message = [
            {
                "role": "assistant",
                "content": content
            }
        ]

        return {
            "messages": assistant_message,
            "style_findings": response.style_findings
        }

    def summarizer(self, state: State) -> State:
        # summarize the bug findings, style findings, and any other findings into a final review
        system_prompt = f"""You are a senior code reviewer. Your job is to summarize the findings from the bug detector, 
        style reviewer, and any other reviewers into a final review. Here are the findings you need to summarize:
        ## Bug Findings:
        {str(state['bug_findings'])}

        ## Style Findings:
        {str(state['style_findings'])}

        ## Instructions:
        - Summarize the findings into a final review.
        - Provide a clear and concise summary. Always state what language the code is written in.
        - If there are not findings, state that the code looks good and follows best practices.
         """
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_prompt
                found_system_message = True
        
        if not found_system_message:
            messages = [SystemMessage(content=system_prompt)] + messages  
        
        response = self.summarizer_llm.invoke(messages)

        assistant_message = [
            {
                "role": "assistant",
                "content": response.final_review
            }
        ]

        return {
            "messages": assistant_message,
            "final_review": response.final_review
        }
    
    
    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("code_extractor", self.code_extractor)
        graph_builder.add_node("bug_detector", self.bug_detector)
        graph_builder.add_node("style_reviewer", self.style_reviewer)
        graph_builder.add_node("summarizer", self.summarizer)

        # Add edges
        graph_builder.add_edge(START, "code_extractor")
        graph_builder.add_conditional_edges("code_extractor", self.code_extractor_router, {"bug_detector": "bug_detector", "END": END})
        graph_builder.add_edge("bug_detector", "style_reviewer")
        graph_builder.add_edge("style_reviewer", "summarizer")
        graph_builder.add_edge("summarizer", END)

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message):
        config = {"configurable": {"thread_id": self.orchestrator_id}}
        state = {
            "messages": [HumanMessage(content=message)],
            "code_diff": "",
            "language": "",
            "bug_findings": [],
            "style_findings": [],
            "final_review": ""
        }

        result = await self.graph.ainvoke(state, config=config)
    
        return result["messages"][-1].content
