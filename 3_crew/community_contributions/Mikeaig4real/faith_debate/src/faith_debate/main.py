import warnings
from pydantic import BaseModel
from crewai import Task, Crew, Process
from faith_debate.crew import FaithDebate

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

class SelectedDebaters(BaseModel):
    debater_1: str
    debater_2: str
    reasoning: str


motion = 'The universe points to the existence of a Creator.'

# Dynamic run function, this is due to the non-sequential nature of the debate
# and the fact that the moderator selects the debaters dynamically

def run():
    """
    Run the custom orchestrated debate crew.
    """

    debate_crew = FaithDebate()

    agents = {
        'christian': debate_crew.christian_debater(),
        'muslim': debate_crew.muslim_debater(),
        'atheist': debate_crew.atheist_debater(),
        'agnostic': debate_crew.agnostic_debater()
    }

    moderator = debate_crew.moderator()

    print("=== Starting the Faith Debate ===")

    print(f"Motion: {motion}\n")


    print("--- Phase 1: Opening Statements ---")

    opening_tasks = []

    for agent in agents.values():
        t = Task(
            description=debate_crew.tasks_config['opening_statement']['description'].format(motion=motion),
            expected_output=debate_crew.tasks_config['opening_statement']['expected_output'],
            agent=agent
        )

        opening_tasks.append(t)   

    opening_crew = Crew(agents=list(agents.values()), tasks=opening_tasks, process=Process.sequential, verbose=True)
    
    opening_crew.kickoff()
    
    statements = "\n\n".join([f"[{task.agent.role}]: {task.output.raw}" for task in opening_tasks])

    
    print("\n--- Phase 2: Moderator Selection ---")

    selection_task = Task(
        description=debate_crew.tasks_config['moderator_selection']['description'].format(motion=motion) + f"\n\nOPENING STATEMENTS:\n{statements}",
        expected_output=debate_crew.tasks_config['moderator_selection']['expected_output'],
        agent=moderator,
        output_pydantic=SelectedDebaters
    )

    selection_crew = Crew(agents=[moderator], tasks=[selection_task], verbose=True)

    selection_crew.kickoff()

    selected_pydantic = selection_task.output.pydantic

    if not selected_pydantic:
        print("Failed to format output as JSON. Defaulting to christian and atheist.")
        d1, d2 = 'christian', 'atheist'
    else:
        d1 = selected_pydantic.debater_1.lower().replace('_debater', '')
        d2 = selected_pydantic.debater_2.lower().replace('_debater', '')
        print(f"\nModerator selected: {d1.upper()} and {d2.upper()}")
        print(f"Reason: {selected_pydantic.reasoning}\n")
        
    ag1_key = d1 if d1 in agents else 'christian'

    ag2_key = d2 if d2 in agents else 'atheist'

    ag1 = agents[ag1_key]

    ag2 = agents[ag2_key]


    print("\n--- Phase 3: The Debate (3 Rounds) ---")
    debate_history = statements
    
    for round_num in range(1, 4):
        print(f"\n--- Round {round_num} ---")

        # Propose
        task_p = Task(
            description=debate_crew.tasks_config['debate_propose']['description'].format(motion=motion, debate_history=debate_history),
            expected_output=debate_crew.tasks_config['debate_propose']['expected_output'],
            agent=ag1
        )

        crew_p = Crew(agents=[ag1], tasks=[task_p], verbose=True)

        crew_p.kickoff()

        res_p = task_p.output.raw

        debate_history += f"\n\n[Round {round_num} - {ag1.role} Proposes]: {res_p}"
        
        # Oppose
        task_o = Task(
            description=debate_crew.tasks_config['debate_oppose']['description'].format(motion=motion, debate_history=debate_history),
            expected_output=debate_crew.tasks_config['debate_oppose']['expected_output'],
            agent=ag2
        )

        crew_o = Crew(agents=[ag2], tasks=[task_o], verbose=True)

        crew_o.kickoff()

        res_o = task_o.output.raw

        debate_history += f"\n\n[Round {round_num} - {ag2.role} Opposes]: {res_o}"
        
    
    print("\n--- Phase 4: Final Judgment ---")

    judgment_task = Task(
        description=debate_crew.tasks_config['final_judgment']['description'].format(motion=motion, debate_history=debate_history),
        expected_output=debate_crew.tasks_config['final_judgment']['expected_output'],
        agent=moderator
    )
    
    judgment_crew = Crew(agents=[moderator], tasks=[judgment_task], verbose=True)

    judgment_crew.kickoff()
    

    print("\n\n================ FINAL VERDICT ================")
    print(judgment_task.output.raw)
    print("===============================================")

    
    with open("debate_transcript.md", "w", encoding="utf-8") as f:
        f.write(f"# Faith Debate Transcript: {motion}\n\n")
        f.write("## Debate History\n")
        f.write(debate_history)
        f.write("\n\n## Final Verdict\n")
        f.write(judgment_task.output.raw)
    
    print("\nFull debate transcript was saved to 'debate_transcript.md'")

