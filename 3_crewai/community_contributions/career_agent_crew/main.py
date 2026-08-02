from crew import build_crew


if __name__ == "__main__":
    user_input = {
        "name": "Mugao",
        "skills": ["React", "Django"],
        "goal": "AI Engineer"
    }

    crew = build_crew(user_input)

    result = crew.kickoff()

    print("\n=== FINAL OUTPUT ===\n")
    print(result)