from graph import build_graph


if __name__ == "__main__":
    graph = build_graph()

    initial_state = {
        "user_input": {
            "name": "Mugao",
            "skills": ["React", "Django"],
            "goal": "AI Engineer"
        },
        "clarified": False,
        "roles": [],
        "skill_gaps": {},
        "learning_plan": "",
        "final_report": "",
        "next_step": ""
    }

    result = graph.invoke(initial_state)

    print(result["final_report"])