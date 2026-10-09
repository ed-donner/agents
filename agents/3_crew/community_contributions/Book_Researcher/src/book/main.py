import os
from book.crew import BookResearchCrew

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the book market research crew.
    """
    inputs = {
        # Example input for genre-based research
        'genre': 'Fantasy'
    }

    # Kickoff the crew with inputs
    result = BookResearchCrew().crew().kickoff(inputs=inputs)

    # Print aggregated raw output
    print("\n\n=== FINAL REPORT ===\n\n")
    print(result.raw)

    print("\nReports have been saved to the 'output/' directory:")
    print(" - trending_books.md")
    print(" - top_novelists.md")
    print(" - genre_research.md")

if __name__ == '__main__':
    run()
