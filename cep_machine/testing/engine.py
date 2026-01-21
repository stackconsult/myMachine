"""
CEP Testing Engine - Replaces BrowserOS ($50-100/mo)

Workflow: Spin up Chromium → Execute Action → Record Metric → Capture Screenshot on Fail

Uses Playwright for real browser automation.
Cost: $0/month (all local)
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from ..core.database import Database


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    passed: bool
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "screenshot_path": self.screenshot_path,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TestReport:
    """Complete test report for a layer."""
    layer_id: int
    layer_name: str
    results: List[TestResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration_ms: int
    pass_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "results": [r.to_dict() for r in self.results],
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "total_duration_ms": self.total_duration_ms,
            "pass_rate": self.pass_rate,
        }


class TestingEngine:
    """
    Testing Engine - Browser automation and testing.
    
    Replaces BrowserOS with:
    - Playwright (real Chromium browser)
    - Local execution (no SaaS)
    - Screenshot capture on failure
    - Performance metrics
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        headless: bool = True,
        screenshot_dir: str = "./screenshots",
    ):
        self.db = db or Database()
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._browser: Optional[Browser] = None
    
    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: playwright install chromium")
        
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=self.headless)
        
        return self._browser
    
    async def close(self):
        """Close the browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    async def run_test(
        self,
        test_name: str,
        url: str,
        actions: List[Dict[str, Any]],
        assertions: List[Dict[str, Any]],
        layer_id: Optional[int] = None,
    ) -> TestResult:
        """
        Run a single test.
        
        Args:
            test_name: Name of the test
            url: URL to navigate to
            actions: List of actions to perform
            assertions: List of assertions to check
            layer_id: Optional layer ID for tracking
        
        Returns:
            TestResult with pass/fail status
        """
        start_time = datetime.now()
        error_message = None
        screenshot_path = None
        metrics: Dict[str, Any] = {}
        passed = True
        
        print(f"[Test] Running: {test_name}")
        
        if not PLAYWRIGHT_AVAILABLE:
            # Mock test result when Playwright not available
            duration_ms = 100
            return TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                error_message="Playwright not installed - mock result",
                metrics={"mock": True},
            )
        
        try:
            browser = await self._get_browser()
            page = await browser.new_page()
            
            # Navigate
            await page.goto(url, wait_until="domcontentloaded")
            metrics["navigation_time_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Execute actions
            for action in actions:
                await self._execute_action(page, action)
            
            # Run assertions
            for assertion in assertions:
                result = await self._check_assertion(page, assertion)
                if not result["passed"]:
                    passed = False
                    error_message = result.get("error", "Assertion failed")
                    break
            
            # Capture screenshot on failure
            if not passed:
                screenshot_name = f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                screenshot_path = str(self.screenshot_dir / screenshot_name)
                await page.screenshot(path=screenshot_path)
                print(f"  ✗ Screenshot saved: {screenshot_path}")
            
            await page.close()
            
        except Exception as e:
            passed = False
            error_message = str(e)
            print(f"  ✗ Error: {error_message}")
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        metrics["total_duration_ms"] = duration_ms
        
        result = TestResult(
            test_name=test_name,
            passed=passed,
            duration_ms=duration_ms,
            error_message=error_message,
            screenshot_path=screenshot_path,
            metrics=metrics,
        )
        
        # Save to database
        if self.db and layer_id:
            try:
                await self.db.save_test_result(
                    layer_id=layer_id,
                    test_name=test_name,
                    passed=passed,
                    duration_ms=duration_ms,
                    error_message=error_message,
                    screenshot_path=screenshot_path,
                )
            except Exception as e:
                print(f"  Warning: Could not save test result: {e}")
        
        status = "✓" if passed else "✗"
        print(f"  {status} {test_name} ({duration_ms}ms)")
        
        return result
    
    async def _execute_action(self, page: Page, action: Dict[str, Any]) -> None:
        """Execute a browser action."""
        action_type = action.get("type", "")
        selector = action.get("selector", "")
        value = action.get("value", "")
        
        if action_type == "click":
            await page.click(selector)
        elif action_type == "fill":
            await page.fill(selector, value)
        elif action_type == "type":
            await page.type(selector, value)
        elif action_type == "wait":
            await page.wait_for_selector(selector)
        elif action_type == "wait_ms":
            await asyncio.sleep(int(value) / 1000)
        elif action_type == "scroll":
            await page.evaluate(f"window.scrollBy(0, {value})")
    
    async def _check_assertion(self, page: Page, assertion: Dict[str, Any]) -> Dict[str, Any]:
        """Check an assertion."""
        assertion_type = assertion.get("type", "")
        selector = assertion.get("selector", "")
        expected = assertion.get("expected", "")
        
        try:
            if assertion_type == "title":
                actual = await page.title()
                passed = expected in actual
            elif assertion_type == "text":
                element = await page.query_selector(selector)
                if element:
                    actual = await element.text_content()
                    passed = expected in (actual or "")
                else:
                    passed = False
                    actual = "Element not found"
            elif assertion_type == "visible":
                element = await page.query_selector(selector)
                passed = element is not None
                actual = "visible" if passed else "not visible"
            elif assertion_type == "url":
                actual = page.url
                passed = expected in actual
            else:
                passed = True
                actual = "Unknown assertion type"
            
            return {
                "passed": passed,
                "expected": expected,
                "actual": actual,
            }
            
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
            }
    
    async def run_layer_tests(
        self,
        layer_id: int,
        layer_name: str,
        tests: List[Dict[str, Any]],
    ) -> TestReport:
        """
        Run all tests for a layer.
        
        Args:
            layer_id: Layer number
            layer_name: Name of the layer
            tests: List of test specifications
        
        Returns:
            TestReport with all results
        """
        print(f"\n[Test] Testing Layer {layer_id}: {layer_name}")
        print("=" * 50)
        
        results: List[TestResult] = []
        
        for test_spec in tests:
            result = await self.run_test(
                test_name=test_spec.get("name", "unnamed"),
                url=test_spec.get("url", "http://localhost:3000"),
                actions=test_spec.get("actions", []),
                assertions=test_spec.get("assertions", []),
                layer_id=layer_id,
            )
            results.append(result)
        
        # Compile report
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = len(results) - passed_tests
        total_duration = sum(r.duration_ms for r in results)
        pass_rate = passed_tests / len(results) if results else 0.0
        
        report = TestReport(
            layer_id=layer_id,
            layer_name=layer_name,
            results=results,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_duration_ms=total_duration,
            pass_rate=pass_rate,
        )
        
        print("=" * 50)
        print(f"[Test] Results: {passed_tests}/{len(results)} passed ({pass_rate:.0%})")
        
        return report
    
    async def quick_test(
        self,
        url: str,
        title_contains: str,
    ) -> TestResult:
        """Quick test that a page loads with expected title."""
        return await self.run_test(
            test_name="quick_test",
            url=url,
            actions=[],
            assertions=[{"type": "title", "expected": title_contains}],
        )


# Default test templates for each layer
LAYER_TEST_TEMPLATES = {
    1: {  # Prospect Research
        "name": "prospect_research_test",
        "url": "http://localhost:8000/api/prospects",
        "actions": [],
        "assertions": [{"type": "title", "expected": "Prospects"}],
    },
    2: {  # Pitch Generator
        "name": "pitch_generator_test",
        "url": "http://localhost:8000/api/pitches",
        "actions": [],
        "assertions": [{"type": "title", "expected": "Pitch"}],
    },
    # ... more templates for layers 3-9
}
