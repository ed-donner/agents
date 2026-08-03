from autogen_core import MessageContext, RoutedAgent, message_handler
import random
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
from autogen_core import TRACE_LOGGER_NAME
import importlib
import logging
from autogen_core import AgentId
from dotenv import load_dotenv
import json
import os
import subprocess
import shutil
from datetime import datetime

load_dotenv(override=True)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Creator(RoutedAgent):

    system_message = """
    You are an Agent that is able to create new AI Agents.
    You receive a template in the form of Python code that creates an Agent using Autogen Core and Autogen Agentchat.
    You should use this template to create a new Agent with a unique system message that is different from the template,
    and reflects their unique characteristics, interests and goals.
    You can choose to keep their overall goal the same, or change it.
    You can choose to take this Agent in a completely different direction. The only requirement is that the class must be named Agent,
    and it must inherit from RoutedAgent and have an __init__ method that takes a name parameter.
    Also avoid environmental interests - try to mix up the business verticals so that every agent is different.
    Respond only with the python code, no other text, and no markdown code blocks.
    """

    EVOLUTION_SYSTEM_MESSAGE = """
    You are an AI code evolution engine. Your task is to make small, meaningful improvements to existing Python agent code.
    Focus on ONE of these mutation types:
    - Adjust probability thresholds (e.g., CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER)
    - Modify system message tone or personality
    - Change model parameters (temperature, model name)
    - Add new behavioral logic or conditions
    - Improve error handling or logging
    
    Do NOT change:
    - Class names or inheritance structure
    - Method signatures
    - Core architecture patterns
    
    Respond only with the complete modified Python code, no explanations, no markdown blocks.
    """

    PERSONA_TEMPLATES = [
        "You are a {sector} innovator focused on {focus}. You value {value1} and {value2}. Your communication style is {style}.",
        "You are a {role} with expertise in {domain}. You are known for being {trait1} and {trait2}. You prefer ideas that are {preference}.",
        "You are a {industry} entrepreneur who believes in {philosophy}. Your strengths are {strength1} and {strength2}. You avoid {weakness}.",
    ]
    
    SECTORS = ["Healthcare", "Education", "Finance", "Climate Tech", "Space Exploration", "Biotech", "Entertainment", "Transportation"]
    FOCUS = ["AI-driven solutions", "sustainable technology", "human augmentation", "decentralized systems", "automation", "personalization"]
    VALUES = ["innovation", "efficiency", "empathy", "scalability", "accessibility", "transparency"]
    STYLES = ["direct and analytical", "enthusiastic and visionary", "cautious and methodical", "creative and unconventional"]
    ROLES = ["serial entrepreneur", "research scientist", "product designer", "venture capitalist", "policy maker"]
    DOMAINS = ["machine learning", "robotics", "genomics", "renewable energy", "fintech", "edtech"]
    TRAITS = ["optimistic", "skeptical", "pragmatic", "idealistic", "data-driven", "intuitive"]
    PREFERENCES = ["high-risk high-reward", "incremental improvements", "disruptive breakthroughs", "practical applications"]
    INDUSTRIES = ["SaaS", "hardware", "consulting", "platform", "marketplace", "deep tech"]
    PHILOSOPHIES = ["first principles thinking", "design thinking", "lean startup", "moonshot thinking"]
    STRENGTHS = ["technical depth", "market intuition", "operational excellence", "creative problem-solving"]
    WEAKNESSES = ["micromanagement", "feature creep", "slow execution", "over-engineering"]

    def __init__(self, name, version=1) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)
        self._evolution_delegate = AssistantAgent(
            f"{name}_evolution", 
            model_client=OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.8),
            system_message=self.EVOLUTION_SYSTEM_MESSAGE
        )
        self.version = version
        self.worker = None

    def set_worker(self, worker):
        self.worker = worker

    def generate_persona(self, seed=None):
        template = random.choice(self.PERSONA_TEMPLATES)
        persona = template.format(
            sector=random.choice(self.SECTORS),
            focus=random.choice(self.FOCUS),
            value1=random.choice(self.VALUES),
            value2=random.choice(self.VALUES),
            style=random.choice(self.STYLES),
            role=random.choice(self.ROLES),
            domain=random.choice(self.DOMAINS),
            trait1=random.choice(self.TRAITS),
            trait2=random.choice(self.TRAITS),
            preference=random.choice(self.PREFERENCES),
            industry=random.choice(self.INDUSTRIES),
            philosophy=random.choice(self.PHILOSOPHIES),
            strength1=random.choice(self.STRENGTHS),
            strength2=random.choice(self.STRENGTHS),
            weakness=random.choice(self.WEAKNESSES)
        )
        
        full_system_message = f"""
        {persona}
        
        Your task is to come up with a new business idea using Agentic AI, or refine an existing idea.
        Respond with your business ideas in an engaging and clear way that reflects your persona.
        """
        
        return full_system_message, random.randint(1000, 9999)

    def get_user_prompt(self, persona_system_message=None):
        if persona_system_message:
            prompt = "Please generate a new Agent based on this template. The key change is to replace the DEFAULT_SYSTEM_MESSAGE with the provided persona system message.\
            Stick to the class structure. Respond only with the python code, no other text, and no markdown code blocks.\n\n\
            Be creative about taking the agent in a new direction, but don't change method signatures.\n\n\
            Here is the template:\n\n"
        else:
            prompt = "Please generate a new Agent based strictly on this template. Stick to the class structure. \
                Respond only with the python code, no other text, and no markdown code blocks.\n\n\
                Be creative about taking the agent in a new direction, but don't change method signatures.\n\n\
                Here is the template:\n\n"
        
        with open("agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        
        if persona_system_message:
            prompt += f"\n\nUse this system message in the generated agent:\n{persona_system_message}\n\n"
        
        return prompt + template

    def _load_evolution_log(self):
        try:
            with open("evolution_log.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"versions": [], "current_version": 0}

    def _save_evolution_log(self, log):
        with open("evolution_log.json", "w") as f:
            json.dump(log, f, indent=2)

    def _validate_syntax(self, filename):
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", filename],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)

    def _validate_import(self, module_name):
        try:
            importlib.import_module(module_name)
            return True, None
        except Exception as e:
            return False, str(e)

    def _validate_functional(self, module_name, agent_name):
        try:
            module = importlib.import_module(module_name)
            agent = module.Agent(agent_name)
            return True, None
        except Exception as e:
            return False, str(e)

    async def evolve(self, ctx: MessageContext):
        logger.info(f"** Creator v{self.version} initiating evolution cycle")
        
        current_file = f"creator_v{self.version}.py"
        if not os.path.exists(current_file):
            current_file = "creator.py"
        
        try:
            with open(current_file, "r", encoding="utf-8") as f:
                current_dna = f.read()
        except Exception as e:
            logger.error(f"** Failed to read current DNA: {e}")
            return False

        mutation_prompt = f"""Improve this agent code with ONE meaningful change.
        Current version: {self.version}
        
        Code to mutate:
        {current_dna}
        """
        
        text_message = TextMessage(content=mutation_prompt, source="user")
        try:
            response = await self._evolution_delegate.on_messages([text_message], ctx.cancellation_token)
            new_dna = response.chat_message.content
            new_dna = new_dna.replace("```python", "").replace("```", "").strip()
        except Exception as e:
            logger.error(f"** Mutation failed: {e}")
            return False

        new_version = self.version + 1
        new_file = f"creator_v{new_version}.py"
        
        with open(new_file, "w", encoding="utf-8") as f:
            f.write(new_dna)
        logger.info(f"** Created {new_file} with mutation")

        valid, error = self._validate_syntax(new_file)
        if not valid:
            logger.error(f"** Syntax validation failed: {error}")
            os.remove(new_file)
            return False
        logger.info(f"** Syntax validation passed")

        module_name = f"creator_v{new_version}"
        valid, error = self._validate_import(module_name)
        if not valid:
            logger.error(f"** Import validation failed: {error}")
            os.remove(new_file)
            return False
        logger.info(f"** Import validation passed")

        valid, error = self._validate_functional(module_name, f"Creator_v{new_version}")
        if not valid:
            logger.error(f"** Functional validation failed: {error}")
            os.remove(new_file)
            return False
        logger.info(f"** Functional validation passed")

        if self.worker is None:
            logger.error("** No worker available for registration")
            os.remove(new_file)
            return False
        
        try:
            new_module = importlib.import_module(module_name)
            await new_module.Creator.register(
                self.worker, 
                f"Creator_v{new_version}", 
                lambda: new_module.Creator(f"Creator_v{new_version}", new_version)
            )
            logger.info(f"** Creator v{new_version} registered successfully")
            
            log = self._load_evolution_log()
            log["versions"].append({
                "version": new_version,
                "parent_version": self.version,
                "timestamp": datetime.now().isoformat(),
                "file": new_file
            })
            log["current_version"] = new_version
            self._save_evolution_log(log)
            
            self.version = new_version
            logger.info(f"** Evolution complete: now running as Creator v{new_version}")
            return True
            
        except Exception as e:
            logger.error(f"** Registration failed: {e}")
            os.remove(new_file)
            return False

    async def rollback(self, target_version=None):
        log = self._load_evolution_log()
        
        if target_version is None:
            if len(log["versions"]) < 2:
                logger.error("** Cannot rollback: no previous version")
                return False
            target_version = log["versions"][-2]["version"]
        
        logger.info(f"** Rolling back to version {target_version}")
        
        target_file = f"creator_v{target_version}.py"
        if not os.path.exists(target_file):
            logger.error(f"** Target version file not found: {target_file}")
            return False
        
        try:
            target_module = importlib.import_module(f"creator_v{target_version}")
            await target_module.Creator.register(
                self.worker,
                f"Creator_v{target_version}_rollback",
                lambda: target_module.Creator(f"Creator_v{target_version}_rollback", target_version)
            )
            log["current_version"] = target_version
            self._save_evolution_log(log)
            self.version = target_version
            logger.info(f"** Rollback to v{target_version} successful")
            return True
        except Exception as e:
            logger.error(f"** Rollback failed: {e}")
            logger.info("** Attempting emergency fallback to base creator")
            return self._fallback_to_base()

    def _fallback_to_base(self):
        if not os.path.exists("creator_base.py"):
            logger.error("** No base creator available for emergency fallback")
            return False
        
        try:
            import creator_base
            shutil.copy("creator_base.py", "creator.py")
            logger.info("** Fallback to base creator complete")
            return True
        except Exception as e:
            logger.error(f"** Emergency fallback failed: {e}")
            return False
        
    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        """Unified message handler that routes based on content"""
        content = str(message.content)
        
        # Check if this is an evolution trigger
        if "EVOLVE" in content.upper():
            logger.info("** Received evolution trigger")
            success = await self.evolve(ctx)
            if success:
                return messages.Message(content=f"Evolution successful. Now running as Creator v{self.version}")
            else:
                return messages.Message(content="Evolution failed. Rolling back...")
        
        # Check if this is an agent creation request (filename pattern)
        if content.endswith(".py"):
            filename = content
            agent_name = filename.split(".")[0]
            
            # Generate persona and seed for this agent
            persona_system_message, seed = self.generate_persona()
            
            text_message = TextMessage(content=self.get_user_prompt(persona_system_message), source="user")
            response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
            agent_code = response.chat_message.content
            
            # Clean up markdown code blocks
            agent_code = agent_code.replace("```python", "").replace("```", "").strip()
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(agent_code)
            
            print(f"** Creator has created python code for agent {agent_name} with seed {seed}")
            
            module = importlib.import_module(agent_name)
            await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name, seed=seed))
            logger.info(f"** Agent {agent_name} is live with seed {seed}")
            
            result = await self.send_message(messages.Message(content="Generate your unique business idea"), AgentId(agent_name, "default"))
            return messages.Message(content=result.content)
        
        # Unknown message type
        return messages.Message(content=f"Unknown command: {content}")
