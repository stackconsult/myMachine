"""
CEP Layer 1: Prospect Research

Find local businesses with weak or missing Google Business Profile (GBP) optimization.
This is the entry point of the sales funnel.

Container Alignment: Sales
Φ Contribution: +0.07

Input: City, business category, radius
Output: List of prospects with GBP scores and opportunities
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from duckduckgo_search import DDGS


class ProspectScore(Enum):
    """Prospect quality scores based on GBP optimization level."""
    HOT = "hot"           # No GBP or very weak (score < 30)
    WARM = "warm"         # Partial GBP (score 30-60)
    COLD = "cold"         # Decent GBP (score 60-80)
    NOT_QUALIFIED = "not_qualified"  # Strong GBP (score > 80)


@dataclass
class GBPAnalysis:
    """Analysis of a business's Google Business Profile."""
    has_gbp: bool = False
    claimed: bool = False
    has_photos: bool = False
    photo_count: int = 0
    has_reviews: bool = False
    review_count: int = 0
    avg_rating: float = 0.0
    has_posts: bool = False
    has_products: bool = False
    has_services: bool = False
    has_hours: bool = False
    has_website: bool = False
    last_updated: Optional[str] = None
    
    def calculate_score(self) -> int:
        """Calculate GBP optimization score (0-100)."""
        score = 0
        
        if self.has_gbp:
            score += 10
        if self.claimed:
            score += 10
        if self.has_photos:
            score += 10
            if self.photo_count >= 10:
                score += 5
        if self.has_reviews:
            score += 10
            if self.review_count >= 10:
                score += 5
            if self.avg_rating >= 4.0:
                score += 5
        if self.has_posts:
            score += 10
        if self.has_products or self.has_services:
            score += 10
        if self.has_hours:
            score += 5
        if self.has_website:
            score += 10
        
        return min(100, score)
    
    def get_opportunities(self) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        if not self.has_gbp:
            opportunities.append("Create Google Business Profile")
        elif not self.claimed:
            opportunities.append("Claim GBP listing")
        
        if self.photo_count < 10:
            opportunities.append(f"Add more photos (currently {self.photo_count})")
        
        if self.review_count < 10:
            opportunities.append(f"Generate more reviews (currently {self.review_count})")
        
        if not self.has_posts:
            opportunities.append("Start posting updates")
        
        if not self.has_products and not self.has_services:
            opportunities.append("Add products/services")
        
        if not self.has_hours:
            opportunities.append("Add business hours")
        
        if not self.has_website:
            opportunities.append("Add website link")
        
        return opportunities


@dataclass
class Prospect:
    """A potential customer prospect."""
    id: str
    business_name: str
    category: str
    location: str
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    gbp_analysis: GBPAnalysis = field(default_factory=GBPAnalysis)
    score: ProspectScore = ProspectScore.WARM
    gbp_score: int = 0
    opportunities: List[str] = field(default_factory=list)
    estimated_revenue_loss: float = 0.0
    discovered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "business_name": self.business_name,
            "category": self.category,
            "location": self.location,
            "phone": self.phone,
            "website": self.website,
            "address": self.address,
            "score": self.score.value,
            "gbp_score": self.gbp_score,
            "opportunities": self.opportunities,
            "estimated_revenue_loss": self.estimated_revenue_loss,
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class ProspectSearchResult:
    """Result of a prospect search."""
    query: str
    location: str
    category: str
    prospects: List[Prospect]
    total_found: int
    hot_leads: int
    warm_leads: int
    search_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "location": self.location,
            "category": self.category,
            "prospects": [p.to_dict() for p in self.prospects],
            "total_found": self.total_found,
            "hot_leads": self.hot_leads,
            "warm_leads": self.warm_leads,
            "search_time_seconds": self.search_time_seconds,
        }


class ProspectorEngine:
    """
    Layer 1: Prospect Research Engine
    
    Finds local businesses with GBP optimization opportunities.
    Uses DuckDuckGo for search (free, no API key needed).
    """
    
    # Business categories to target
    TARGET_CATEGORIES = [
        "dental",
        "dentist",
        "hvac",
        "plumber",
        "plumbing",
        "electrician",
        "roofing",
        "landscaping",
        "auto repair",
        "chiropractor",
        "veterinarian",
        "real estate agent",
        "attorney",
        "accountant",
        "restaurant",
        "salon",
        "spa",
        "gym",
        "fitness",
    ]
    
    def __init__(self, max_results_per_search: int = 20):
        self.max_results = max_results_per_search
        self.ddgs = DDGS()
    
    async def research_local_businesses(
        self,
        location: str,
        category: str,
        radius_km: int = 25,
    ) -> ProspectSearchResult:
        """
        Research local businesses in a specific category and location.
        
        Args:
            location: City/area to search (e.g., "Grande Prairie, AB")
            category: Business category (e.g., "dental", "hvac")
            radius_km: Search radius in kilometers
        
        Returns:
            ProspectSearchResult with qualified prospects
        """
        start_time = datetime.now()
        
        print(f"[Layer 1] Searching: {category} businesses in {location}")
        
        # Build search query
        query = f"{category} near {location}"
        
        # Execute search
        raw_results = await self._search(query)
        
        # Process and qualify prospects
        prospects: List[Prospect] = []
        
        for i, result in enumerate(raw_results):
            prospect = await self._process_result(result, category, location, i)
            if prospect:
                prospects.append(prospect)
        
        # Sort by opportunity (lowest GBP score = highest opportunity)
        prospects.sort(key=lambda p: p.gbp_score)
        
        # Count lead types
        hot_leads = sum(1 for p in prospects if p.score == ProspectScore.HOT)
        warm_leads = sum(1 for p in prospects if p.score == ProspectScore.WARM)
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        result = ProspectSearchResult(
            query=query,
            location=location,
            category=category,
            prospects=prospects,
            total_found=len(prospects),
            hot_leads=hot_leads,
            warm_leads=warm_leads,
            search_time_seconds=search_time,
        )
        
        print(f"[Layer 1] Found {len(prospects)} prospects ({hot_leads} hot, {warm_leads} warm)")
        
        return result
    
    async def _search(self, query: str) -> List[Dict[str, Any]]:
        """Execute DuckDuckGo search."""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=self.max_results))
            )
            return results
        except Exception as e:
            print(f"[Layer 1] Search error: {e}")
            return []
    
    async def _process_result(
        self,
        result: Dict[str, Any],
        category: str,
        location: str,
        index: int,
    ) -> Optional[Prospect]:
        """Process a search result into a Prospect."""
        try:
            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("href", "")
            
            # Skip if not a business
            if not title or "yelp" in url.lower() or "yellowpages" in url.lower():
                # These are directories, not actual businesses
                pass  # Still process for now
            
            # Create prospect ID
            prospect_id = f"prospect_{category}_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Analyze GBP (simulated - in production would use Google Places API)
            gbp_analysis = await self._analyze_gbp(title, url, body)
            
            # Calculate score and classify
            gbp_score = gbp_analysis.calculate_score()
            
            if gbp_score < 30:
                score = ProspectScore.HOT
            elif gbp_score < 60:
                score = ProspectScore.WARM
            elif gbp_score < 80:
                score = ProspectScore.COLD
            else:
                score = ProspectScore.NOT_QUALIFIED
            
            # Get opportunities
            opportunities = gbp_analysis.get_opportunities()
            
            # Estimate revenue loss (simplified calculation)
            # Businesses with low GBP scores lose ~$50k-500k annually
            if gbp_score < 30:
                estimated_loss = 250000  # $250k potential loss
            elif gbp_score < 60:
                estimated_loss = 100000  # $100k potential loss
            else:
                estimated_loss = 25000   # $25k potential loss
            
            prospect = Prospect(
                id=prospect_id,
                business_name=title,
                category=category,
                location=location,
                website=url if url else None,
                gbp_analysis=gbp_analysis,
                score=score,
                gbp_score=gbp_score,
                opportunities=opportunities,
                estimated_revenue_loss=estimated_loss,
                metadata={"source": "duckduckgo", "snippet": body[:200]},
            )
            
            return prospect
            
        except Exception as e:
            print(f"[Layer 1] Error processing result: {e}")
            return None
    
    async def _analyze_gbp(
        self,
        business_name: str,
        website: str,
        snippet: str,
    ) -> GBPAnalysis:
        """
        Analyze a business's GBP presence.
        
        In production, this would use Google Places API.
        For now, we simulate based on available data.
        """
        analysis = GBPAnalysis()
        
        # Simulate GBP analysis based on available signals
        snippet_lower = snippet.lower()
        
        # Check for GBP signals in snippet
        if "google" in snippet_lower or "maps" in snippet_lower:
            analysis.has_gbp = True
            analysis.claimed = True
        
        # Check for review signals
        if "review" in snippet_lower or "rating" in snippet_lower:
            analysis.has_reviews = True
            # Simulate review count (would come from API)
            import random
            analysis.review_count = random.randint(0, 50)
            analysis.avg_rating = round(random.uniform(3.0, 5.0), 1)
        
        # Check for photo signals
        if "photo" in snippet_lower or "image" in snippet_lower:
            analysis.has_photos = True
            import random
            analysis.photo_count = random.randint(1, 20)
        
        # Check for website
        if website and "http" in website:
            analysis.has_website = True
        
        # Simulate other attributes randomly (would come from API)
        import random
        analysis.has_hours = random.choice([True, False])
        analysis.has_posts = random.choice([True, False, False])  # Most don't post
        analysis.has_products = random.choice([True, False, False])
        analysis.has_services = random.choice([True, False])
        
        return analysis
    
    async def research_multiple_markets(
        self,
        markets: List[Dict[str, str]],
        category: str,
        prospects_per_market: int = 20,
    ) -> List[ProspectSearchResult]:
        """
        Research multiple markets in parallel.
        
        Args:
            markets: List of {"city": "...", "province": "..."}
            category: Business category
            prospects_per_market: Max prospects per market
        
        Returns:
            List of ProspectSearchResult for each market
        """
        print(f"[Layer 1] Researching {len(markets)} markets for {category}")
        
        self.max_results = prospects_per_market
        
        results = []
        for market in markets:
            location = f"{market['city']}, {market.get('province', market.get('state', ''))}"
            result = await self.research_local_businesses(location, category)
            results.append(result)
        
        total_prospects = sum(r.total_found for r in results)
        total_hot = sum(r.hot_leads for r in results)
        
        print(f"[Layer 1] Total: {total_prospects} prospects ({total_hot} hot) across {len(markets)} markets")
        
        return results
    
    async def get_daily_prospects(
        self,
        location: str,
        categories: Optional[List[str]] = None,
        target_count: int = 20,
    ) -> List[Prospect]:
        """
        Get daily prospect list for outreach.
        
        Args:
            location: Target location
            categories: Categories to search (default: all)
            target_count: Target number of prospects
        
        Returns:
            List of qualified prospects for the day
        """
        categories = categories or self.TARGET_CATEGORIES[:5]  # Top 5 by default
        
        all_prospects: List[Prospect] = []
        
        for category in categories:
            result = await self.research_local_businesses(location, category)
            all_prospects.extend(result.prospects)
            
            if len(all_prospects) >= target_count:
                break
        
        # Sort by opportunity and return top prospects
        all_prospects.sort(key=lambda p: p.gbp_score)
        
        return all_prospects[:target_count]


# Layer 1 Entry Point
async def run_layer(
    location: str,
    category: str,
    max_prospects: int = 20,
) -> ProspectSearchResult:
    """
    Main entry point for Layer 1: Prospect Research
    
    Args:
        location: City to search (e.g., "Grande Prairie, AB")
        category: Business category (e.g., "dental")
        max_prospects: Maximum prospects to return
    
    Returns:
        ProspectSearchResult with qualified prospects
    """
    print(f"\n{'='*60}")
    print(f"[Layer 1] PROSPECT RESEARCH")
    print(f"Location: {location}")
    print(f"Category: {category}")
    print(f"{'='*60}\n")
    
    engine = ProspectorEngine(max_results_per_search=max_prospects)
    result = await engine.research_local_businesses(location, category)
    
    print(f"\n[Layer 1] ✓ Complete")
    print(f"  - Total prospects: {result.total_found}")
    print(f"  - Hot leads: {result.hot_leads}")
    print(f"  - Warm leads: {result.warm_leads}")
    print(f"  - Search time: {result.search_time_seconds:.1f}s")
    
    return result


# Export
__all__ = [
    "Prospect",
    "ProspectScore",
    "GBPAnalysis",
    "ProspectSearchResult",
    "ProspectorEngine",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    location = sys.argv[1] if len(sys.argv) > 1 else "Grande Prairie, AB"
    category = sys.argv[2] if len(sys.argv) > 2 else "dental"
    
    result = asyncio.run(run_layer(location, category))
    
    print("\n" + "="*60)
    print("TOP PROSPECTS:")
    print("="*60)
    
    for i, prospect in enumerate(result.prospects[:5], 1):
        print(f"\n{i}. {prospect.business_name}")
        print(f"   Score: {prospect.score.value.upper()} (GBP: {prospect.gbp_score}/100)")
        print(f"   Est. Revenue Loss: ${prospect.estimated_revenue_loss:,.0f}/year")
        print(f"   Opportunities: {', '.join(prospect.opportunities[:3])}")
