"""
BFIH Client SDK
Python client library for interacting with BFIH Backend

Usage:
    from bfih_client import BFIHClient
    
    client = BFIHClient(base_url="http://localhost:8000")
    result = await client.submit_analysis(scenario, proposition)
"""

import aiohttp
import asyncio
import time
from typing import Dict, Optional, List
import json


class BFIHClient:
    """Async Python client for BFIH Backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 120):
        """
        Initialize BFIH client
        
        Args:
            base_url: Backend API URL
            timeout: Analysis timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    async def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health") as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    async def submit_analysis(
        self, 
        scenario_id: str,
        proposition: str,
        scenario_config: Dict,
        user_id: Optional[str] = None,
        poll: bool = True,
        poll_interval: int = 2
    ) -> Dict:
        """
        Submit BFIH analysis and optionally wait for result
        
        Args:
            scenario_id: Unique scenario identifier
            proposition: Hypothesis to analyze
            scenario_config: Scenario configuration (paradigms, hypotheses, priors)
            user_id: Optional user identifier
            poll: Whether to wait for result
            poll_interval: Seconds between status polls
            
        Returns:
            Analysis result dict with report and posteriors
        """
        # Submit request
        async with aiohttp.ClientSession() as session:
            payload = {
                "scenario_id": scenario_id,
                "proposition": proposition,
                "scenario_config": scenario_config,
                "user_id": user_id
            }
            
            async with session.post(
                f"{self.base_url}/api/bfih-analysis",
                json=payload
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to submit analysis: {resp.status}")
                
                response = await resp.json()
                analysis_id = response["analysis_id"]
        
        print(f"Analysis submitted: {analysis_id}")
        
        if not poll:
            return response
        
        # Poll for result
        return await self._wait_for_result(analysis_id, poll_interval)
    
    async def _wait_for_result(
        self,
        analysis_id: str,
        poll_interval: int = 2,
        max_attempts: Optional[int] = None
    ) -> Dict:
        """
        Poll for analysis result until completion
        
        Args:
            analysis_id: ID of analysis to monitor
            poll_interval: Seconds between polls
            max_attempts: Maximum number of poll attempts
            
        Returns:
            Completed analysis result
        """
        start_time = time.time()
        attempts = 0
        
        while True:
            elapsed = time.time() - start_time
            
            if self.timeout and elapsed > self.timeout:
                raise TimeoutError(f"Analysis timed out after {self.timeout}s")
            
            if max_attempts and attempts >= max_attempts:
                raise Exception(f"Max attempts ({max_attempts}) reached")
            
            # Check status
            status = await self.get_analysis_status(analysis_id)
            
            if status["status"] == "completed":
                return await self.get_analysis_result(analysis_id)
            elif status["status"].startswith("failed"):
                raise Exception(f"Analysis failed: {status['status']}")
            
            print(f"[{elapsed:.1f}s] Status: {status['status']}...")
            
            await asyncio.sleep(poll_interval)
            attempts += 1
    
    async def get_analysis_result(self, analysis_id: str) -> Dict:
        """Get completed analysis result"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/bfih-analysis/{analysis_id}"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get analysis: {resp.status}")
                return await resp.json()
    
    async def get_analysis_status(self, analysis_id: str) -> Dict:
        """Get analysis status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/analysis-status/{analysis_id}"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get status: {resp.status}")
                return await resp.json()
    
    async def store_scenario(self, scenario: Dict) -> Dict:
        """Store scenario configuration"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/scenario",
                json=scenario
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to store scenario: {resp.status}")
                return await resp.json()
    
    async def get_scenario(self, scenario_id: str) -> Dict:
        """Get scenario configuration"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/scenario/{scenario_id}"
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get scenario: {resp.status}")
                return await resp.json()
    
    async def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all stored scenarios"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/scenarios/list",
                params={"limit": limit, "offset": offset}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to list scenarios: {resp.status}")
                result = await resp.json()
                return result["scenarios"]


# ============================================================================
# SYNCHRONOUS WRAPPER (for simpler usage)
# ============================================================================

class BFIHClientSync:
    """Synchronous wrapper around async client"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 120):
        self.client = BFIHClient(base_url, timeout)
    
    def health_check(self) -> bool:
        """Check health"""
        return asyncio.run(self.client.health_check())
    
    def submit_analysis(
        self,
        scenario_id: str,
        proposition: str,
        scenario_config: Dict,
        user_id: Optional[str] = None,
        poll: bool = True
    ) -> Dict:
        """Submit analysis"""
        return asyncio.run(self.client.submit_analysis(
            scenario_id, proposition, scenario_config, user_id, poll
        ))
    
    def get_analysis_result(self, analysis_id: str) -> Dict:
        """Get result"""
        return asyncio.run(self.client.get_analysis_result(analysis_id))
    
    def get_analysis_status(self, analysis_id: str) -> Dict:
        """Get status"""
        return asyncio.run(self.client.get_analysis_status(analysis_id))
    
    def store_scenario(self, scenario: Dict) -> Dict:
        """Store scenario"""
        return asyncio.run(self.client.store_scenario(scenario))
    
    def get_scenario(self, scenario_id: str) -> Dict:
        """Get scenario"""
        return asyncio.run(self.client.get_scenario(scenario_id))
    
    def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List scenarios"""
        return asyncio.run(self.client.list_scenarios(limit, offset))


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    
    # Example: Synchronous usage
    def example_sync():
        """Synchronous example"""
        client = BFIHClientSync("http://localhost:8000")
        
        # Check health
        if not client.health_check():
            print("Backend is not available")
            return
        
        scenario_config = {
            "paradigms": [
                {"id": "K1", "name": "Paradigm 1", "description": "..."},
                {"id": "K2", "name": "Paradigm 2", "description": "..."}
            ],
            "hypotheses": [
                {"id": "H1", "name": "Hypothesis 1", "domains": [], "associated_paradigms": ["K1"]},
                {"id": "H2", "name": "Hypothesis 2", "domains": [], "associated_paradigms": ["K2"]}
            ],
            "priors_by_paradigm": {
                "K1": {"H1": 0.7, "H2": 0.3},
                "K2": {"H1": 0.3, "H2": 0.7}
            }
        }
        
        # Submit analysis
        result = client.submit_analysis(
            scenario_id="s_example_001",
            proposition="Which hypothesis is correct?",
            scenario_config=scenario_config,
            poll=True  # Wait for result
        )
        
        print("\n" + "="*60)
        print("ANALYSIS RESULT")
        print("="*60)
        print(f"Analysis ID: {result['analysis_id']}")
        print(f"Status: {result.get('status', 'completed')}")
        print("\nReport (first 500 chars):")
        print(result['report'][:500] + "...")
        print("\nPosteriors:")
        print(json.dumps(result['posteriors'], indent=2))
    
    # Example: Async usage
    async def example_async():
        """Async example"""
        client = BFIHClient("http://localhost:8000")
        
        scenario_config = {...}  # Same as above
        
        result = await client.submit_analysis(
            scenario_id="s_example_002",
            proposition="Which hypothesis is correct?",
            scenario_config=scenario_config,
            poll=True
        )
        
        print("Analysis result:", result['analysis_id'])
    
    # Run sync example
    print("Running synchronous example...")
    # example_sync()  # Uncomment to run
