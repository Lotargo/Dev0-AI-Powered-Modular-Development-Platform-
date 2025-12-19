from duckduckgo_search import DDGS
from pydantic import BaseModel, Field
from typing import List

class WebSearchInput(BaseModel):
    query: str = Field(..., description="The search query.")

class WebSearchResult(BaseModel):
    title: str
    url: str
    body: str

class WebSearchOutput(BaseModel):
    results: List[WebSearchResult]

def execute(input_data: WebSearchInput) -> WebSearchOutput:
    """
    Performs a web search using DuckDuckGo.
    """
    with DDGS() as ddgs:
        results = [
            WebSearchResult(
                title=r["title"],
                url=r["href"],
                body=r["body"]
            )
            for r in ddgs.text(input_data.query, max_results=5)
        ]
    return WebSearchOutput(results=results)
