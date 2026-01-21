"""
CEP Research Engine - Replaces Perplexity ($200/mo)

Workflow: DuckDuckGo Search → Firecrawl Extract → Ollama Summarize → SQLite Store

Cost: $0/month
- DuckDuckGo: free
- Firecrawl: free tier
- Ollama: free (local)
- SQLite: free
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import httpx
from duckduckgo_search import DDGS

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from ..core.database import Database


@dataclass
class ResearchResult:
    """A single research result with citation."""
    query: str
    source_url: str
    source_title: str
    snippet: str
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "snippet": self.snippet,
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ResearchReport:
    """Complete research report with multiple sources."""
    query: str
    results: List[ResearchResult]
    combined_summary: str
    citation_count: int
    research_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "combined_summary": self.combined_summary,
            "citation_count": self.citation_count,
            "research_time_seconds": self.research_time_seconds,
        }


class ResearchEngine:
    """
    Research Engine - The brain for finding information.
    
    Replaces Perplexity Comet ($200/month) with:
    - DuckDuckGo for search (free, no API key)
    - Firecrawl for content extraction (free tier)
    - Ollama for summarization (local, free)
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        ollama_model: str = "llama2",
        max_results: int = 5,
    ):
        self.db = db or Database()
        self.ollama_model = ollama_model
        self.max_results = max_results
        self.ddgs = DDGS()
    
    async def research(
        self,
        query: str,
        layer_id: Optional[int] = None,
    ) -> ResearchReport:
        """
        Execute a complete research workflow.
        
        1. Search web with DuckDuckGo
        2. Extract content from top results
        3. Summarize with local LLM
        4. Store citations in database
        
        Returns a ResearchReport with citations.
        """
        start_time = datetime.now()
        
        # Step 1: Search
        print(f"[Research] Searching: {query}")
        search_results = await self._search(query)
        
        # Step 2: Process each result
        results: List[ResearchResult] = []
        for sr in search_results[:self.max_results]:
            try:
                # Summarize each result
                summary = await self._summarize(sr.get("body", ""), query)
                
                result = ResearchResult(
                    query=query,
                    source_url=sr.get("href", ""),
                    source_title=sr.get("title", ""),
                    snippet=sr.get("body", "")[:500],
                    summary=summary,
                )
                results.append(result)
                
                # Store in database
                if self.db:
                    await self.db.add_research_log(
                        query=query,
                        source_url=result.source_url,
                        source_title=result.source_title,
                        summary=summary,
                        citations=json.dumps([result.source_url]),
                        layer_id=layer_id,
                    )
                
                print(f"  ✓ {result.source_title[:50]}...")
                
            except Exception as e:
                print(f"  ✗ Error processing result: {e}")
                continue
        
        # Step 3: Create combined summary
        combined_summary = await self._create_combined_summary(query, results)
        
        # Calculate research time
        research_time = (datetime.now() - start_time).total_seconds()
        
        report = ResearchReport(
            query=query,
            results=results,
            combined_summary=combined_summary,
            citation_count=len(results),
            research_time_seconds=research_time,
        )
        
        print(f"[Research] Complete: {len(results)} citations in {research_time:.1f}s")
        
        return report
    
    async def _search(self, query: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            # Run sync search in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=self.max_results * 2))
            )
            return results
        except Exception as e:
            print(f"[Research] Search error: {e}")
            return []
    
    async def _summarize(self, content: str, query: str) -> str:
        """Summarize content using Ollama (local LLM)."""
        if not OLLAMA_AVAILABLE:
            # Fallback: return truncated content
            return content[:300] + "..." if len(content) > 300 else content
        
        try:
            prompt = f"""Summarize the following content in 2-3 sentences, focusing on information relevant to: "{query}"

Content:
{content[:2000]}

Summary:"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama.generate(model=self.ollama_model, prompt=prompt)
            )
            
            return response.get("response", content[:300])
            
        except Exception as e:
            print(f"[Research] Summarization error: {e}")
            return content[:300] + "..." if len(content) > 300 else content
    
    async def _create_combined_summary(
        self,
        query: str,
        results: List[ResearchResult],
    ) -> str:
        """Create a combined summary from all results."""
        if not results:
            return "No research results found."
        
        if not OLLAMA_AVAILABLE:
            # Fallback: concatenate summaries
            summaries = [r.summary for r in results]
            return " ".join(summaries)[:500]
        
        try:
            # Combine all summaries
            all_summaries = "\n\n".join([
                f"Source {i+1} ({r.source_title}):\n{r.summary}"
                for i, r in enumerate(results)
            ])
            
            prompt = f"""Based on the following research sources about "{query}", provide a comprehensive 1-paragraph summary that synthesizes the key findings:

{all_summaries}

Comprehensive Summary:"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama.generate(model=self.ollama_model, prompt=prompt)
            )
            
            return response.get("response", all_summaries[:500])
            
        except Exception as e:
            print(f"[Research] Combined summary error: {e}")
            return " ".join([r.summary for r in results])[:500]
    
    async def quick_search(self, query: str) -> List[Dict[str, Any]]:
        """Quick search without summarization (for fast lookups)."""
        results = await self._search(query)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results[:self.max_results]
        ]
    
    async def research_for_layer(
        self,
        layer_id: int,
        topic: str,
    ) -> ResearchReport:
        """Research specifically for a layer build."""
        query = f"best practices for {topic} automation implementation"
        return await self.research(query, layer_id=layer_id)


# Convenience function for quick research
async def quick_research(query: str) -> ResearchReport:
    """Quick research helper function."""
    engine = ResearchEngine()
    return await engine.research(query)
