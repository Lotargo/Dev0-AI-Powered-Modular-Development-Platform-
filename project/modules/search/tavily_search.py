"""
Atomic module for performing web searches using the Tavily API.
"""
import os
import httpx
from pydantic import BaseModel, Field
from project.core.framework.atomic import atomic
from dotenv import load_dotenv

# Load specific env file
load_dotenv(".env.tavily")

class TavilySearchInput(BaseModel):
    query: str = Field(..., description="The technical query to search for.")

class TavilySearchOutput(BaseModel):
    results: str = Field(..., description="A summary of the search results.")

@atomic
def execute(input_data: TavilySearchInput) -> TavilySearchOutput:
    """
    Performs a web search using the Tavily API to retrieve technical information.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return TavilySearchOutput(results="Error: TAVILY_API_KEY not found in .env.tavily")

    try:
        # Use httpx.post (sync)
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": input_data.query,
                "search_depth": "advanced",
                "include_answer": True,
                "topic": "general"
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

        # Format results
        answer = data.get("answer", "No direct answer provided.")
        results_list = data.get("results", [])

        formatted_output = f"**Tavily Answer:**\n{answer}\n\n**Relevant Sources:**\n"
        for res in results_list:
            # Limit content length per source to avoid overflowing context
            content = res.get('content', '')[:300]
            formatted_output += f"- **{res.get('title')}** ({res.get('url')}):\n  {content}...\n\n"

        return TavilySearchOutput(results=formatted_output)

    except Exception as e:
        return TavilySearchOutput(results=f"Search failed: {str(e)}")
