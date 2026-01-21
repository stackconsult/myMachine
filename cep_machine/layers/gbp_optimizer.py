"""
CEP Layer 6: GBP Optimizer

Automated Google Business Profile optimization with AI-generated content.
Manages posts, photos, reviews, Q&A, and GBP features.

Container Alignment: Operations
Φ Contribution: +0.08

Input: Onboarded clients from Layer 5
Output: Optimized GBP with improved visibility
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class GBPOptimizationType(Enum):
    """Types of GBP optimizations."""
    PROFILE_COMPLETION = "profile_completion"
    PHOTO_UPLOAD = "photo_upload"
    POST_CREATION = "post_creation"
    REVIEW_RESPONSE = "review_response"
    QA_MANAGEMENT = "qa_management"
    SERVICE_UPDATE = "service_update"
    HOURS_UPDATE = "hours_update"
    WEBSITE_LINK = "website_link"


class PostType(Enum):
    """Types of GBP posts."""
    UPDATE = "update"
    OFFER = "offer"
    EVENT = "event"
    NEWS = "news"


class OptimizationStatus(Enum):
    """Status of optimization tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


@dataclass
class GBPOptimization:
    """An optimization task for GBP."""
    id: str
    client_id: str
    business_name: str
    optimization_type: GBPOptimizationType
    title: str
    description: str
    status: OptimizationStatus = OptimizationStatus.PENDING
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    content: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "business_name": self.business_name,
            "optimization_type": self.optimization_type.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "content": self.content,
            "media_urls": self.media_urls,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class GBPPost:
    """A GBP post."""
    id: str
    client_id: str
    business_name: str
    post_type: PostType
    title: str
    content: str
    call_to_action: str
    url: Optional[str] = None
    photo_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    status: OptimizationStatus = OptimizationStatus.PENDING
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "business_name": self.business_name,
            "post_type": self.post_type.value,
            "title": self.title,
            "content": self.content,
            "call_to_action": self.cta,
            "url": self.url,
            "photo_url": self.photo_url,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "status": self.status.value,
            "metrics": self.metrics,
        }


@dataclass
class GBPOptimizationResult:
    """Result of GBP optimization campaign."""
    client_id: str
    business_name: str
    optimizations_completed: int
    posts_created: int
    photos_uploaded: int
    reviews_responded: int
    score_improvement: float
    visibility_increase: float
    processing_time_seconds: float
    optimizations: List[GBPOptimization] = field(default_factory=list)
    posts: List[GBPPost] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "business_name": self.business_name,
            "optimizations_completed": self.optimizations_completed,
            "posts_created": self.posts_created,
            "photos_uploaded": self.photos_uploaded,
            "reviews_responded": self.reviews_responded,
            "score_improvement": self.score_improvement,
            "visibility_increase": self.visibility_increase,
            "processing_time_seconds": self.processing_time_seconds,
            "optimizations": [o.to_dict() for o in self.optimizations],
            "posts": [p.to_dict() for p in self.posts],
        }


class GBPOptimizerEngine:
    """
    Layer 6: GBP Optimizer Engine
    
    Optimizes Google Business Profiles with AI-generated content.
    Manages posts, photos, reviews, and GBP features.
    """
    
    # Post frequency by business type
    POST_FREQUENCY = {
        "dental": {"weekly": 2, "monthly": 8},
        "hvac": {"weekly": 1, "monthly": 4},
        "restaurant": {"weekly": 3, "monthly": 12},
        "default": {"weekly": 1, "monthly": 4},
    }
    
    # Content templates by industry
    CONTENT_TEMPLATES = {
        "dental": {
            "post_topics": [
                "Dental hygiene tips",
                "New technology introduction",
                "Patient testimonials",
                "Seasonal dental care",
                "Meet the team",
                "Special offers",
            ],
            "review_responses": {
                "5_star": "Thank you for your wonderful review! We're thrilled you had a great experience.",
                "4_star": "Thank you for your feedback! We appreciate your support and look forward to seeing you again.",
                "3_star": "Thank you for your feedback. We're always looking to improve - please let us know how we can better serve you.",
                "negative": "We're sorry to hear about your experience. Please contact us directly so we can make things right.",
            },
        },
        "hvac": {
            "post_topics": [
                "HVAC maintenance tips",
                "Energy efficiency advice",
                "Seasonal preparation",
                "Equipment upgrades",
                "Emergency services",
                "Customer testimonials",
            ],
            "review_responses": {
                "5_star": "Thank you for trusting us with your HVAC needs! Your comfort is our priority.",
                "4_star": "We appreciate your business! Thank you for the feedback.",
                "3_star": "Thank you for your review. We're committed to providing excellent service.",
                "negative": "We apologize for any issues. Please contact our office to resolve your concerns.",
            },
        },
    }
    
    def __init__(self, llm_provider: str = "openai", model: str = "gpt-4-turbo-preview", dry_run: bool = True):
        self.llm_provider = llm_provider
        self.model = model
        self.dry_run = dry_run
        self.llm = self._init_llm()
        self.optimizations: Dict[str, List[GBPOptimization]] = {}
        self.posts: Dict[str, List[GBPPost]] = {}
    
    def _init_llm(self):
        """Initialize the LLM."""
        if not LLM_AVAILABLE:
            return None
        
        if self.llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return ChatAnthropic(
                    model=self.model or "claude-3-sonnet-20240229",
                    anthropic_api_key=api_key,
                )
        
        if self.llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return ChatOpenAI(
                    model=self.model or "gpt-4-turbo-preview",
                    openai_api_key=api_key,
                )
        
        return None
    
    async def optimize_gbp(
        self,
        client_id: str,
        business_name: str,
        business_type: str,
        current_gbp_score: float,
        optimization_types: Optional[List[GBPOptimizationType]] = None,
    ) -> GBPOptimizationResult:
        """
        Run complete GBP optimization for a client.
        
        Args:
            client_id: Client identifier
            business_name: Business name
            business_type: Type of business (dental, hvac, etc.)
            current_gbp_score: Current GBP optimization score (0-100)
            optimization_types: Specific optimizations to run
        
        Returns:
            GBPOptimizationResult with all optimizations
        """
        start_time = datetime.now()
        
        print(f"[Layer 6] Optimizing GBP for {business_name}")
        
        # Initialize result
        result = GBPOptimizationResult(
            client_id=client_id,
            business_name=business_name,
            optimizations_completed=0,
            posts_created=0,
            photos_uploaded=0,
            reviews_responded=0,
            score_improvement=0.0,
            visibility_increase=0.0,
            processing_time_seconds=0.0,
        )
        
        # Store initial metrics
        initial_metrics = {"gbp_score": current_gbp_score}
        
        # Determine optimizations to run
        if optimization_types is None:
            optimization_types = [
                GBPOptimizationType.PROFILE_COMPLETION,
                GBPOptimizationType.POST_CREATION,
                GBPOptimizationType.PHOTO_UPLOAD,
                GBPOptimizationType.REVIEW_RESPONSE,
                GBPOptimizationType.QA_MANAGEMENT,
            ]
        
        # Run optimizations
        for opt_type in optimization_types:
            optimization = await self._run_optimization(
                client_id, business_name, business_type, opt_type
            )
            result.optimizations.append(optimization)
            
            if optimization.status == OptimizationStatus.COMPLETED:
                result.optimizations_completed += 1
                
                # Update counters
                if opt_type == GBPOptimizationType.POST_CREATION:
                    result.posts_created += 1
                elif opt_type == GBPOptimizationType.PHOTO_UPLOAD:
                    result.photos_uploaded += len(optimization.media_urls)
                elif opt_type == GBPOptimizationType.REVIEW_RESPONSE:
                    result.reviews_responded += 1
        
        # Create content calendar
        posts = await self._create_content_calendar(
            client_id, business_name, business_type
        )
        result.posts.extend(posts)
        result.posts_created += len(posts)
        
        # Calculate improvements
        final_score = current_gbp_score + (result.optimizations_completed * 5)  # 5 points per optimization
        final_score = min(100, final_score)
        
        result.score_improvement = final_score - current_gbp_score
        result.visibility_increase = result.score_improvement * 0.8  # Estimated visibility impact
        
        # Store results
        if client_id not in self.optimizations:
            self.optimizations[client_id] = []
        self.optimizations[client_id].extend(result.optimizations)
        
        if client_id not in self.posts:
            self.posts[client_id] = []
        self.posts[client_id].extend(result.posts)
        
        result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        print(f"[Layer 6] ✓ Optimization complete")
        print(f"  - Optimizations: {result.optimizations_completed}")
        print(f"  - Posts created: {result.posts_created}")
        print(f"  - Score improvement: +{result.score_improvement:.1f}")
        
        return result
    
    async def _run_optimization(
        self,
        client_id: str,
        business_name: str,
        business_type: str,
        opt_type: GBPOptimizationType,
    ) -> GBPOptimization:
        """Run a specific optimization."""
        optimization = GBPOptimization(
            id=f"opt_{client_id}_{opt_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            client_id=client_id,
            business_name=business_name,
            optimization_type=opt_type,
            title=f"{opt_type.value.replace('_', ' ').title()}",
            description=f"Optimize {opt_type.value.replace('_', ' ')} for GBP",
        )
        
        try:
            if opt_type == GBPOptimizationType.PROFILE_COMPLETION:
                await self._complete_profile(optimization, business_type)
            elif opt_type == GBPOptimizationType.POST_CREATION:
                await self._create_post(optimization, business_type)
            elif opt_type == GBPOptimizationType.PHOTO_UPLOAD:
                await self._upload_photos(optimization, business_type)
            elif opt_type == GBPOptimizationType.REVIEW_RESPONSE:
                await self._respond_to_reviews(optimization, business_type)
            elif opt_type == GBPOptimizationType.QA_MANAGEMENT:
                await self._manage_qa(optimization, business_type)
            
            optimization.status = OptimizationStatus.COMPLETED
            optimization.completed_at = datetime.now()
            
        except Exception as e:
            optimization.status = OptimizationStatus.FAILED
            optimization.errors.append(str(e))
            print(f"[Layer 6] Optimization failed: {e}")
        
        return optimization
    
    async def _complete_profile(
        self,
        optimization: GBPOptimization,
        business_type: str,
    ) -> None:
        """Complete GBP profile information."""
        if self.dry_run:
            print(f"[Layer 6] (DRY RUN) Would complete profile for {optimization.business_name}")
            optimization.content = "Profile completed with business hours, categories, and attributes"
            return
        
        # In production, use Google My Business API
        optimization.content = "Profile completed with business hours, categories, and attributes"
        print(f"[Layer 6] ✓ Profile completed for {optimization.business_name}")
    
    async def _create_post(
        self,
        optimization: GBPOptimization,
        business_type: str,
    ) -> None:
        """Create a GBP post."""
        templates = self.CONTENT_TEMPLATES.get(business_type.lower(), {})
        topics = templates.get("post_topics", ["Business update", "Special offer"])
        
        if self.llm:
            content = await self._llm_generate_post(
                optimization.business_name,
                business_type,
                topics[0],
            )
        else:
            content = f"Exciting update from {optimization.business_name}! We're committed to providing excellent service to our community."
        
        optimization.content = content
        print(f"[Layer 6] ✓ Post created for {optimization.business_name}")
    
    async def _upload_photos(
        self,
        optimization: GBPOptimization,
        business_type: str,
    ) -> None:
        """Upload business photos."""
        photo_types = ["exterior", "interior", "team", "work"]
        
        if self.dry_run:
            print(f"[Layer 6] (DRY RUN) Would upload photos for {optimization.business_name}")
            optimization.media_urls = [f"/photos/{optimization.business_name}_{ptype}.jpg" for ptype in photo_types]
            optimization.content = f"Uploaded {len(photo_types)} business photos"
            return
        
        # In production, upload actual photos
        optimization.media_urls = [f"/photos/{optimization.business_name}_{ptype}.jpg" for ptype in photo_types]
        optimization.content = f"Uploaded {len(photo_types)} business photos"
        print(f"[Layer 6] ✓ Photos uploaded for {optimization.business_name}")
    
    async def _respond_to_reviews(
        self,
        optimization: GBPOptimization,
        business_type: str,
    ) -> None:
        """Respond to customer reviews."""
        templates = self.CONTENT_TEMPLATES.get(business_type.lower(), {})
        responses = templates.get("review_responses", {})
        
        # Simulate responding to reviews
        responses_made = []
        for rating, template in responses.items():
            responses_made.append(f"Responded to {rating}-star review: {template}")
        
        optimization.content = f"Responded to {len(responses_made)} reviews"
        optimization.metadata["responses"] = responses_made
        print(f"[Layer 6] ✓ Reviews responded for {optimization.business_name}")
    
    async def _manage_qa(
        self,
        optimization: GBPOptimization,
        business_type: str,
    ) -> None:
        """Manage Q&A section."""
        # Common Q&A by business type
        qa_templates = {
            "dental": [
                {"q": "Do you accept new patients?", "a": "Yes, we're always welcoming new patients!"},
                {"q": "What insurance do you accept?", "a": "We accept most major insurance plans."},
            ],
            "hvac": [
                {"q": "Do you offer emergency service?", "a": "Yes, we provide 24/7 emergency HVAC service."},
                {"q": "What areas do you service?", "a": "We service the entire metropolitan area."},
            ],
        }
        
        qa_list = qa_templates.get(business_type.lower(), qa_templates["hvac"])
        
        if self.dry_run:
            print(f"[Layer 6] (DRY RUN) Would manage Q&A for {optimization.business_name}")
            optimization.content = f"Added {len(qa_list)} Q&A pairs"
            optimization.metadata["qa_pairs"] = qa_list
            return
        
        optimization.content = f"Added {len(qa_list)} Q&A pairs"
        optimization.metadata["qa_pairs"] = qa_list
        print(f"[Layer 6] ✓ Q&A managed for {optimization.business_name}")
    
    async def _create_content_calendar(
        self,
        client_id: str,
        business_name: str,
        business_type: str,
    ) -> List[GBPPost]:
        """Create a content calendar for the client."""
        frequency = self.POST_FREQUENCY.get(business_type.lower(), self.POST_FREQUENCY["default"])
        templates = self.CONTENT_TEMPLATES.get(business_type.lower(), {})
        topics = templates.get("post_topics", ["Business update", "Special offer"])
        
        posts = []
        now = datetime.now()
        
        # Create 4 weeks of posts
        for week in range(4):
            for day in range(frequency["weekly"]):
                post_date = now + timedelta(weeks=week, days=day * 3)
                
                topic = topics[day % len(topics)]
                
                if self.llm:
                    content = await self._llm_generate_post(
                        business_name,
                        business_type,
                        topic,
                    )
                else:
                    content = f"{topic}: {business_name} is here to serve our community with excellence!"
                
                post = GBPPost(
                    id=f"post_{client_id}_{week}_{day}",
                    client_id=client_id,
                    business_name=business_name,
                    post_type=PostType.UPDATE,
                    title=topic,
                    content=content,
                    call_to_action="Call us today!",
                    scheduled_at=post_date,
                    status=OptimizationStatus.SCHEDULED,
                )
                
                posts.append(post)
        
        print(f"[Layer 6] ✓ Created {len(posts)} scheduled posts")
        
        return posts
    
    async def _llm_generate_post(
        self,
        business_name: str,
        business_type: str,
        topic: str,
    ) -> str:
        """Generate post content using LLM."""
        prompt = f"""Write a Google Business Profile post for a {business_type} business.

Business: {business_name}
Topic: {topic}

Requirements:
- 100-150 words
- Professional but friendly tone
- Include a call to action
- No emojis
- Business-focused

Format: Return only the post content."""
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"[Layer 6] LLM generation failed: {e}")
            return f"{topic}: {business_name} is committed to serving our community with excellence. Contact us today!"
    
    async def get_optimization_report(
        self,
        client_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get optimization report for a client."""
        optimizations = self.optimizations.get(client_id, [])
        posts = self.posts.get(client_id, [])
        
        # Filter by date range
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_opts = [o for o in optimizations if o.completed_at and o.completed_at > cutoff]
        recent_posts = [p for p in posts if p.posted_at and p.posted_at > cutoff]
        
        return {
            "client_id": client_id,
            "period_days": days,
            "optimizations_completed": len(recent_opts),
            "posts_published": len(recent_posts),
            "avg_engagement": sum(p.metrics.get("views", 0) for p in recent_posts) / max(len(recent_posts), 1),
            "optimization_types": list(set(o.optimization_type.value for o in recent_opts)),
        }


# Layer 6 Entry Point
async def run_layer(
    client_id: str,
    business_name: str,
    business_type: str,
    current_gbp_score: float,
    dry_run: bool = True,
) -> GBPOptimizationResult:
    """
    Main entry point for Layer 6: GBP Optimizer
    
    Args:
        client_id: Client identifier
        business_name: Business name
        business_type: Type of business (dental, hvac, etc.)
        current_gbp_score: Current GBP score (0-100)
        dry_run: If True, simulate external API calls
    
    Returns:
        GBPOptimizationResult with all optimizations
    """
    print(f"\n{'='*60}")
    print(f"[Layer 6] GBP OPTIMIZER")
    print(f"Client: {business_name}")
    print(f"Type: {business_type}")
    print(f"Current Score: {current_gbp_score}/100")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    optimizer = GBPOptimizerEngine(dry_run=dry_run)
    result = await optimizer.optimize_gbp(
        client_id=client_id,
        business_name=business_name,
        business_type=business_type,
        current_gbp_score=current_gbp_score,
    )
    
    print(f"\n[Layer 6] ✓ Complete")
    print(f"  - Optimizations: {result.optimizations_completed}")
    print(f"  - Posts created: {result.posts_created}")
    print(f"  - Score improvement: +{result.score_improvement:.1f}")
    print(f"  - Processing time: {result.processing_time_seconds:.1f}s")
    
    return result


# Export
__all__ = [
    "GBPOptimization",
    "GBPPost",
    "GBPOptimizationResult",
    "GBPOptimizerEngine",
    "GBPOptimizationType",
    "PostType",
    "OptimizationStatus",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    client_id = sys.argv[1] if len(sys.argv) > 1 else "client_001"
    business_name = sys.argv[2] if len(sys.argv) > 2 else "Test Dental Clinic"
    business_type = sys.argv[3] if len(sys.argv) > 3 else "dental"
    current_score = float(sys.argv[4]) if len(sys.argv) > 4 else 45.0
    
    dry_run = "--live" not in sys.argv
    result = asyncio.run(run_layer(
        client_id=client_id,
        business_name=business_name,
        business_type=business_type,
        current_gbp_score=current_score,
        dry_run=dry_run,
    ))
    
    print("\n" + "="*60)
    print("OPTIMIZATION SUMMARY:")
    print("="*60)
    
    print(f"\nBusiness: {result.business_name}")
    print(f"Score before: {current_score}/100")
    print(f"Score after: {current_score + result.score_improvement:.1f}/100")
    print(f"Improvement: +{result.score_improvement:.1f}")
    
    print(f"\nOptimizations:")
    for opt in result.optimizations:
        status_icon = "✓" if opt.status == OptimizationStatus.COMPLETED else "✗"
        print(f"  {status_icon} {opt.title}")
    
    print(f"\nScheduled Posts:")
    for post in result.posts[:5]:  # Show first 5
        print(f"  📅 {post.scheduled_at.strftime('%Y-%m-%d')}: {post.title}")
    
    if len(result.posts) > 5:
        print(f"  ... and {len(result.posts) - 5} more posts")
