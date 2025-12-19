"""
Researcher Agent: Finds technical documentation and solutions via Web Search.
"""
import asyncio
import json
from pydantic import BaseModel, Field
from typing import Optional

from project.core.llm_gateway.gateway import execute as gateway_execute
from project.modules.search.tavily_search import execute as tavily_search, TavilySearchInput
from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_CODEBASE, COLLECTION_DOCUMENTATION

class ResearcherInput(BaseModel):
    topic: str
    context: Optional[str] = Field(None, description="Previous context or error message.")
    model_group: Optional[str] = Field("classic_reasoning", description="Model group to use.")

class ResearcherOutput(BaseModel):
    research_summary: str

async def execute_async(input_data: ResearcherInput) -> ResearcherOutput:
    """
    Performs web research and returns a synthesized cheat sheet.
    """
    print(f"--- Researcher: Searching for '{input_data.topic}'... ---")

    # Direct search using the provided topic/query
    # If context contains an error, we append it to the query for better results
    query = input_data.topic
    if input_data.context and "Error" in input_data.context:
         # Extract last part of error or just append
         query += f" {input_data.context[:200]}"

    search_result = tavily_search(TavilySearchInput(query=query))

    # --- Auto-Context RAG ---
    qm = get_qdrant_manager()
    # Search for code examples to see if we already have something similar
    code_chunks = qm.search_items(COLLECTION_CODEBASE, query, limit=3)
    # Search docs for project philosophy
    doc_chunks = qm.search_items(COLLECTION_DOCUMENTATION, query, limit=3)

    rag_content = ""
    if code_chunks:
        rag_content += "\n**Local Codebase Context (Existing Implementations):**\n"
        for chunk in code_chunks:
            rag_content += f"---\nFile: {chunk.get('filepath')}\nContent:\n{chunk.get('content')}\n---\n"

    if doc_chunks:
        rag_content += "\n**Local Documentation Context:**\n"
        for chunk in doc_chunks:
            rag_content += f"---\nFile: {chunk.get('filepath')}\nContent:\n{chunk.get('content')}\n---\n"
    # ------------------------

    prompt = f"""
You are a Senior Technical Researcher.
Your goal is to create a **Developer Cheat Sheet** based on the provided search results and local context.

**User Query:** "{query}"
**Context/Error:** "{input_data.context or 'None'}"

**Search Results (Web):**
{search_result.results}

{rag_content}

**Instructions:**
1.  Analyze the search results carefully.
2.  Provide **concrete, copy-pasteable Python code examples** that solve the problem.
3.  If this is about fixing an error, provide the solution.
4.  **Output Format:** A concise Markdown summary with code blocks. Do not be chatty. Just facts and code.
"""
    # Use the specified model group (defaulting to Llama 70B via classic_reasoning)
    model_group = input_data.model_group if input_data.model_group else "classic_reasoning"
    response = await gateway_execute(model_group=model_group, prompt=prompt)

    return ResearcherOutput(research_summary=response)

def execute(input_data: ResearcherInput) -> ResearcherOutput:
    return asyncio.run(execute_async(input_data))
