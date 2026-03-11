from langchain_google_genai import ChatGoogleGenerativeAI
print("Imported successfully")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
print(llm)