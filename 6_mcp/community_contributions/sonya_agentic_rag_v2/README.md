# Agentic RAG equipped w/ Chunking, Hybrid Retriever and MRR (Re-Ranker)

### Simulate An Intelligent RAG system in Health Care Industry

I got this idea from my niece.  She works as an oncologist in Kaiser Permanente.  Most Health Care industry have documents of internal treatment guideline for cost effective or other reasons.  They might scatter around and have not been systemized as an Intelligent RAG system.

The Intelligent Agentic RAG system serves as a Q & A assistant: Router agent will route to one of VectorDB retrievers: `Medical Q & A` or `Medical Device Manuals`  based upon the nature of the question.  The VectorDBs cannot cover the full scope of medical knowledge.  Therefore, a Relevance Checker will verify if the answer is relevant. Go ahead to send to the generator to generate the answer based upon the provided context if pass relevance test; otherwise fallback to web search using Serper API as a tool. Always go through the Relevance Checker.  However, do set a maximum itertaion limit.  I got synthesized data from [Kaggle Comprehensive Medical Q&A Dataset](https://www.kaggle.com/datasets/thedevastator/comprehensive-medical-q-a-dataset) and [Kaggle Medical Device Manuals Dataset](https://www.kaggle.com/datasets/pratyushpuri/global-medical-device-manuals-dataset-2025)

In general, both VectorDB retriever classes implements Semantic Retriever and Hybrid Retriever (Semantic plus Keyword search) plus Re-ranking.  In Gradio app, users can choose the retriever.

The former is using ChromaDB collection query n_results. I created the collection using Cosine distance instead of the default L2 distance for a better evaluation and filter out documents of Cosine distance exceeding customizable max cosine distance criteria.

The latter selects a large pool (3 x k) of semantic matches and keyword matches then use `Cross Encoder` to rank and narroow down to k choices.  Semantic matches use the dot-product of full embeddings and query embedding. Keyword matches use bm25 with tokenized documents and query. Combine the normaized sematic scores and the normalized keyword scores with the customizable weight (alpha) to generate the larger pool of matches before re-ranking.

There is an [Adaptive RAG](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_adaptive_rag.ipynb) that has sophisticated Hallucination guardrail (check between the generation and the context) and Answer guardrails (check between the generation and the answer).  I stick to my simple plan because the system is in medical/ scientic domain and not in product/ marketing materials.  To be honest, documents retrieved are sometimes irrelevant not because the question is not clear but because the dataset is not comprehensive enough. In the prompt of `augment_generate` step, I do require LLM to cite the source.  Hopeful, that will prevent the hallucination which I learned from the RAG lesson of Air Canada.

### Summary

* When I first trace the process and dump results from Hybrid Retriever, I was quite disappointed. It does not live up to the height. I was mainly disappointed by keyword matches.  If I searches for 'How long is the incubation period of measles?',  it will find the incubation period of all kind of disease.  If I search with te alternative: 'When will a measles patient have the first appearance symptons after he or she is exposed to a pathogen?', keyword search did not find the good results.  To be honest, it's the re-ranker whose prediction score keep the final results grounded. I require ranking scores > 0.

  However, in other case like 'what is the most aggressive form of brain tumor?', Semantic Retriever cannot compete with Hybrid Retriever unless I raise up 'max cosine distance criteria'.  Hybrid Retriever using a larger pool of candidates does help too.  Overall, I found Hybrid Retriever plus Re-ranking does have better performance.  Therefore, I use Hybrid Retriever plus Re-rank as the default retriever in Gradio app.py.
* That brings my first question: how do I evalute a RAG system? How do I apply precision@k, recall@k and other metrics?  Will enhance as I learn RAG more.
* ChromaDB is using `sentence-transformers/all-MiniLM-L6-v2` which has 384 dimensions.  It's s decent choice.  That save the work to customize embeddings using OpenAI embeddings.  However, OpenAI `text-embedding-3-small` embeddings has 1536 dimensions and `text-embedding-3-large` embeddings has 3072 dimensions.  Thay should have a better result of semantic search.  Will try out with my next RAG project.
* One of the tough part of a RAG system is that documents can come in many different forms: PDF, Markdown, HTML and text. Langchain has a lot of loaders that can load & parse PDF, Markdown into Documents then apply `RecursiveCharacterTextSplitter` to chunk. That's the easiest ones.

  `asyncio` and `aiohttp` combined with `BeautifulSoup` will work well on large volumn of HTMLs.  Unfortunately, most web sites are JavaScript enabled and  most commercial web sites are also equipped with CloudFlare which will detect crawling even with the best pratice like rotation of User-Agents.

  My original idea is to combine artices from Medical Journals like Lancet Oncology for cancers related knowledge and `Medical Q&A` dataset for general medical information but the former channels were blocked.  I have to use all CSV sources and read them into DataFrame by Polars.  Chunking on `Answer` column and adding documents in batches is the difficult part. Despite my best effort and writing compacted codes, the runnig time is O(N**3).
* Putting together Agentic RAG really helps me solidiy my Langraph understanding.  I learned a lot.

  I always wonder why we need to use Pydantic BaseModel on structured output of individual LangGraph nodes as well TypedDict for the aggregated Graph State.  Why cannot we just lump everything into Graph State using Pydatic BaseModel? Pydantic BaseModel validate data in Run Time.  Graph State most likely having incrementally updated data will fail at validation unless we put most fields optional.  That would defeat the purpose of using Pydantic BaseModel for runtime validation.

  A structured output with Pydantic BasedModel is essential for a Literal output. Giving LLM clear instruction does not gurantee the required output.  I can still get 'Yes' or 'yes.' for 'yes' without the structured output which makes the result deterministic.

  LangGraph relies on states returned by nodes to be stateful.  Any operation changing Graph state need to happen to nodes.  If I implement increment the iteration count for the check of maxium iteration count in `relevance_decision` which is the condition for a conditional edge and return `state['pass_relevance_test']` instead of `state`, the iteration count won't stay.  Such a subtle mistake caused me debugging time.

  Most of time, we use llm with structured out or llm with tools. However, LangGraph does allow to use LangChain Tool directly if you only have a standalone tool and do not use LLM function at all.  It's better to use Serper as a LangChain tool instead of `serper.run` call because the former will be part of history of StateSnapshot that we can set checkpoint at it to replay.  Also, we can use LangGraph standard invoke function to keep things consistent.

### To try your self:

Python 3.14 or the above is not compatible with pydatic-core here.  I am using Python 3.12.12 and use it to create a virtual environment and install requirements.txt.

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt`

Then create a data folder and download [Kaggle Comprehensive Medical Q&A Dataset](https://www.kaggle.com/datasets/thedevastator/comprehensive-medical-q-a-dataset) and [Kaggle Medical Device Manuals Dataset](https://www.kaggle.com/datasets/pratyushpuri/global-medical-device-manuals-dataset-2025) and save them as `data/medical_q_n_a.csv` and `data/medical_device_manuals.csv` .
uncomment `medical_qna_retriever.load_index_documents()` to index Medical Q & A dataset into ChromaDB and`medical_device_retriever.load_index_documents()` to index Medical Device Manuals dataset into ChromaDB
You can leave the rest of codes for initial validation to ensure Retrievers work properly.

You can the execute with
`python app.py`

### Github Codes:

https://github.com/threecuptea/agentic_rag_v2

### The PR:

https://github.com/ed-donner/agents/pull/588

### References:

[Build Agentic RAG using LangGraph](https://ai.plainenglish.io/build-agentic-rag-using-langgraph-b568aa26d710)

[RAG System in 5 levels of Difficulty](https://medium.com/data-science-collective/rag-systems-in-5-levels-of-difficulty-with-full-code-443180a7dc59)

[LangGraph Adaptive RAG](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_adaptive_rag.ipynb)
