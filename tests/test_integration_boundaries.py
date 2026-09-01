from __future__ import annotations

from ai_architect.agents.agent_manager import AgentManager
from ai_architect.agents.architect_agent import ArchitectAgent
from ai_architect.agents.base_agent import BaseAgent
from ai_architect.agents.test_agent import TestAgent as CompatibilityTestAgent
from ai_architect.decision_engine.decision_engine import DecisionEngine


def test_agent_manager_imports_compatibility_agents() -> None:
    assert issubclass(ArchitectAgent, BaseAgent)
    assert issubclass(CompatibilityTestAgent, BaseAgent)
    assert ArchitectAgent.name == "Architect Agent"
    assert CompatibilityTestAgent.name == "Test Agent"
    assert AgentManager.__module__ == "ai_architect.agents.agent_manager"


def test_decision_engine_facade_routes_to_auto_decision() -> None:
    report = DecisionEngine().decide(
        metrics={
            "duplicates": 0,
            "oversized_files": 0,
            "complexity": 0,
            "security_findings": 0,
        },
        findings=[],
        task={"touches_core": False},
        tests_ok=True,
    )

    assert report["approved"] is True
    assert report["decision"] == "ACCEPT"
    assert report["confidence"] >= 0.9
