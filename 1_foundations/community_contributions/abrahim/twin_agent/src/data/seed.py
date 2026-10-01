from db import KnowledgeStore
import pandas
import os

store = KnowledgeStore()
store.init_schema()

current_file_dir = os.path.dirname(os.path.abspath(__file__))
knowledge_path = os.path.join(current_file_dir, "..", ".." "/info", "knowledge.csv")

data_frame = pandas.read_csv(knowledge_path)
chunks = []
listc = {
    row.get("question"): row.get("answer").split("||") for _, row in data_frame.iterrows()
}

for key, chunks in listc.items():
    store.ingest(chunks, meta={"question": key})
    print("Ingested", len(chunks), "chunks")
