from crewai import Agent, Crew, Process, Task  # pyright: ignore[reportMissingImports]
from crewai.project import CrewBase, agent, crew, task  # pyright: ignore[reportMissingImports]
from crewai.agents.agent_builder.base_agent import BaseAgent  # pyright: ignore[reportMissingImports]
from crewai_tools import SerperDevTool, ScrapeWebsiteTool  # pyright: ignore[reportMissingImports]
from typing import List, Dict, Optional
import yaml
import re


@CrewBase
class ProtienFoodFinder():
    """ProtienFoodFinder crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    settings_config = 'src/protien_food_finder/config/settings.yaml'

    def __init__(self):
        # Initialize tools
        self.serper_tool = SerperDevTool()
        self.scraper_tool = ScrapeWebsiteTool()

        # Load settings
        self.settings = self._load_settings()

        # Storage for dynamic agents and tasks
        self.dynamic_agents: List[Agent] = []
        self.dynamic_tasks: List[Task] = []
        self.store_list: List[str] = []

    def _load_settings(self) -> Dict:
        """Load settings from settings.yaml"""
        try:
            with open(self.settings_config, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load settings.yaml: {e}")
            # Return defaults if file doesn't exist
            return {
                'products_per_store': {'default': 5},
                'agent_behavior': {'continue_on_failure': True},
                'stores': {}
            }

    @agent
    def store_locator(self) -> Agent:
        return Agent(
            config=self.agents_config['store_locator'],
            tools=[self.serper_tool],# type: ignore[index]
            verbose=True
        )

    @agent
    def nutrition_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['nutrition_researcher'],
            tools=[self.serper_tool, self.scraper_tool],  # Added scraper for detailed product pages
            verbose=True
        )

    @agent
    def nutrition_validator(self) -> Agent:
        return Agent(
            config=self.agents_config['nutrition_validator'],
            verbose=True
        )

    @agent
    def recommendation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['recommendation_specialist'],
            verbose=True
        )

    def parse_stores_from_output(self, find_stores_output: str) -> List[str]:
        """
        Parse store names from the find_stores task output.
        Expected format: "1. Store Name - Distance" or "Store Name - Distance"
        """
        stores = []
        lines = find_stores_output.strip().split('\n')

        # Known store patterns from settings
        known_stores = list(self.settings.get('stores', {}).keys())

        for line in lines:
            # Remove numbering (1., 2., etc.)
            line = re.sub(r'^\d+\.\s*', '', line.strip())

            # Try to extract store name (everything before " - ")
            match = re.match(r'^([^-]+)', line)
            if match:
                potential_store = match.group(1).strip()

                # Check if it matches any known store
                for known_store in known_stores:
                    if known_store.lower() in potential_store.lower():
                        if known_store not in stores:  # Avoid duplicates
                            stores.append(known_store)
                        break

        print(f"📍 Parsed {len(stores)} stores: {stores}")
        return stores

    def create_store_specialist_agent(self, store_name: str, location: str, dietary_preferences: str) -> Optional[Agent]:
        """
        Dynamically create a store specialist agent using the template from agents.yaml
        """
        try:
            # Get template from agents config
            template = self.agents_config.get('store_specialist_template', {})

            # Get store info from settings
            store_info = self.settings['stores'].get(store_name, {})
            store_website = store_info.get('website', f"{store_name.lower().replace(' ', '')}.com")

            # Get products count from settings
            products_count = self.settings['products_per_store'].get('default', 5)

            # Replace variables in template
            agent_config = {
                'role': template['role'].format(store_name=store_name),
                'goal': template['goal'].format(
                    store_name=store_name,
                    store_website=store_website,
                    location=location,
                    dietary_preferences=dietary_preferences,
                    products_count=products_count
                ),
                'backstory': template['backstory'].format(
                    store_name=store_name,
                    store_website=store_website
                ),
                'llm': template.get('llm', 'gpt-4o-mini'),
                'verbose': template.get('verbose', True),
                'allow_delegation': template.get('allow_delegation', False)
            }

            # Create agent
            agent = Agent(
                config=agent_config,
                tools=[self.serper_tool, self.scraper_tool],
                verbose=True
            )

            print(f"✅ Created agent for {store_name}")
            return agent

        except Exception as e:
            print(f"❌ Failed to create agent for {store_name}: {e}")
            if self.settings['agent_behavior'].get('continue_on_failure', True):
                print(f"⏭️  Continuing without {store_name}")
                return None
            else:
                raise

    def create_store_search_task(self, store_name: str, agent: Agent, location: str, dietary_preferences: str, find_stores_task_obj: Task) -> Optional[Task]:
        """
        Dynamically create a store search task using the template from tasks.yaml
        """
        try:
            # Get template from tasks config
            template = self.tasks_config.get('store_search_template', {})

            # Get store info from settings
            store_info = self.settings['stores'].get(store_name, {})
            store_website = store_info.get('website', f"{store_name.lower().replace(' ', '')}.com")

            # Get products count from settings
            products_count = self.settings['products_per_store'].get('default', 5)

            # Replace variables in template
            task_config = {
                'description': template['description'].format(
                    store_name=store_name,
                    store_website=store_website,
                    location=location,
                    dietary_preferences=dietary_preferences,
                    products_count=products_count
                ),
                'expected_output': template['expected_output'].format(
                    store_name=store_name,
                    products_count=products_count
                ),
                'agent': agent,
                'context': [find_stores_task_obj]
            }

            # Create task
            task = Task(
                description=task_config['description'],
                expected_output=task_config['expected_output'],
                agent=task_config['agent'],
                context=task_config['context']
            )

            print(f"✅ Created task for {store_name}")
            return task

        except Exception as e:
            print(f"❌ Failed to create task for {store_name}: {e}")
            if self.settings['agent_behavior'].get('continue_on_failure', True):
                print(f"⏭️  Continuing without {store_name} task")
                return None
            else:
                raise

    @task
    def find_stores_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_stores'], 
        )

    @task
    def research_protein_items_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_protein_items'],
        )

    @task
    def validate_products_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_products'],
        )

    @task
    def create_recommendations_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_recommendations'],
        )

    def build_dynamic_crew(self, location: str, dietary_preferences: str) -> Crew:
        """
        Build a dynamic crew that:
        1. Finds stores first
        2. Parses store names from output
        3. Creates one agent and task per store
        4. Runs all store tasks in parallel (if configured)
        5. Validates and makes recommendations
        """
        print(f"\n🏗️  Building dynamic crew for location: {location}")

        # Step 1: Find stores
        print("\n📍 Step 1: Finding stores...")
        store_locator_agent = self.store_locator()
        find_stores_task_obj = self.find_stores_task()

        # Run just the store finding task
        initial_crew = Crew(
            agents=[store_locator_agent],
            tasks=[find_stores_task_obj],
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
        )

        # Execute to get store list
        find_stores_result = initial_crew.kickoff(inputs={'location': location})
        find_stores_output = str(find_stores_result)

        # Step 2: Parse stores
        print("\n🔍 Step 2: Parsing stores from output...")
        stores = self.parse_stores_from_output(find_stores_output)
        self.store_list = stores

        if not stores:
            print("⚠️  No stores found. Falling back to legacy workflow.")
            return self.crew()  # Fallback to old workflow

        # Step 3: Create dynamic agents and tasks
        print(f"\n🤖 Step 3: Creating {len(stores)} store specialist agents...")
        for store_name in stores:
            agent = self.create_store_specialist_agent(store_name, location, dietary_preferences)
            if agent:
                self.dynamic_agents.append(agent)

                # Create corresponding task
                task = self.create_store_search_task(
                    store_name,
                    agent,
                    location,
                    dietary_preferences,
                    find_stores_task_obj
                )
                if task:
                    self.dynamic_tasks.append(task)

        if not self.dynamic_tasks:
            print("⚠️  No dynamic tasks created. Falling back to legacy workflow.")
            return self.crew()

        # Step 4: Build complete task list
        print(f"\n📋 Step 4: Building complete workflow with {len(self.dynamic_tasks)} store tasks...")

        # Create validation and recommendation tasks
        validator_agent = self.nutrition_validator()
        recommender_agent = self.recommendation_specialist()

        # Validation task needs all store tasks as context
        validate_task = Task(
            description=self.tasks_config['validate_products']['description'],
            expected_output=self.tasks_config['validate_products']['expected_output'],
            agent=validator_agent,
            context=self.dynamic_tasks  # Context from all store searches
        )

        # Recommendation task needs validation task as context
        recommend_task = Task(
            description=self.tasks_config['create_recommendations']['description'],
            expected_output=self.tasks_config['create_recommendations']['expected_output'],
            agent=recommender_agent,
            context=[validate_task] + self.dynamic_tasks,  # Context from validation and all searches
            output_file='output/protein_recommendations.md'
        )

        # Combine all agents and tasks
        all_agents = [store_locator_agent] + self.dynamic_agents + [validator_agent, recommender_agent]
        all_tasks = [find_stores_task_obj] + self.dynamic_tasks + [validate_task, recommend_task]

        print(f"\n✅ Dynamic crew built:")
        print(f"   - {len(all_agents)} agents ({len(self.dynamic_agents)} store specialists)")
        print(f"   - {len(all_tasks)} tasks ({len(self.dynamic_tasks)} store searches)")

        # Step 5: Create and return dynamic crew
        return Crew(
            agents=all_agents,
            tasks=all_tasks,
            process=Process.sequential,  # Sequential ensures proper context flow
            verbose=True,
            memory=True,
            cache=True,
        )

    @crew
    def crew(self) -> Crew:
        """
        Creates the ProtienFoodFinder crew with memory enabled.
        This is the legacy/fallback workflow using static agents.
        For dynamic workflow, use build_dynamic_crew() instead.
        """
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=True,  # Enable memory to cache results and avoid redundant searches
            cache=True,   # Enable caching for tool calls
        )
