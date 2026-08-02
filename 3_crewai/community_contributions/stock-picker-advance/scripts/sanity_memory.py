import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    from stock_picker.crew import StockPickerCrew

    crew = StockPickerCrew().crew()
    print("Crew memory flag:", crew.memory)
    print("Embedder config:", crew.embedder)
    print("ShortTermMemory type:", type(crew.short_term_memory).__name__)
    print("LongTermMemory type:", type(crew.long_term_memory).__name__)
    print("EntityMemory type:", type(crew.entity_memory).__name__)

    # Initialize and reset STM to ensure storage path is ready without external calls
    stm = crew.short_term_memory
    stm.save("sanity check", {"note": "init"})
    print("Short-term memory save ok (no reset invoked)")


if __name__ == "__main__":
    main()
