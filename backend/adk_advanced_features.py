#!/usr/bin/env python3
"""Advanced ADK Features Implementation for BMAD.

This module implements advanced ADK capabilities including multi-model support,
dynamic tool integration, and enhanced agent orchestration patterns.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ModelConfiguration:
    """Configuration for different LLM models."""
    name: str
    provider: str
    model_id: str
    context_window: int
    cost_per_token: float
    performance_score: float
    supported_features: List[str]


@dataclass
class MultiModelAgent:
    """Agent capable of using multiple models dynamically."""
    agent_type: str
    primary_model: str
    fallback_models: List[str]
    task_routing_rules: Dict[str, str]
    performance_thresholds: Dict[str, float]


class ADKMultiModelManager:
    """Manages multi-model capabilities for ADK agents."""

    def __init__(self):
        self.available_models = self._initialize_models()
        self.model_performance_history = {}
        self.task_model_mapping = {}

    def _initialize_models(self) -> Dict[str, ModelConfiguration]:
        """Initialize available models with their configurations."""
        return {
            "gemini-2.0-flash": ModelConfiguration(
                name="Gemini 2.0 Flash",
                provider="google",
                model_id="gemini-2.0-flash-exp",
                context_window=1048576,
                cost_per_token=0.000001,
                performance_score=0.95,
                supported_features=["text", "vision", "tools", "json"]
            ),
            "gemini-1.5-pro": ModelConfiguration(
                name="Gemini 1.5 Pro",
                provider="google",
                model_id="gemini-1.5-pro",
                context_window=2097152,
                cost_per_token=0.0000025,
                performance_score=0.98,
                supported_features=["text", "vision", "tools", "json", "long_context"]
            ),
            "gpt-4-turbo": ModelConfiguration(
                name="GPT-4 Turbo",
                provider="openai",
                model_id="gpt-4-turbo-preview",
                context_window=128000,
                cost_per_token=0.00001,
                performance_score=0.96,
                supported_features=["text", "tools", "json", "function_calling"]
            ),
            "claude-3-opus": ModelConfiguration(
                name="Claude 3 Opus",
                provider="anthropic",
                model_id="claude-3-opus-20240229",
                context_window=200000,
                cost_per_token=0.000015,
                performance_score=0.97,
                supported_features=["text", "vision", "tools", "json"]
            )
        }

    def select_optimal_model(self, task_type: str, complexity: str = "medium",
                           cost_sensitivity: str = "balanced") -> str:
        """Select the optimal model for a given task."""
        candidates = []

        for model_id, config in self.available_models.items():
            # Check if model supports required features for task type
            required_features = self._get_required_features(task_type)
            if not all(feature in config.supported_features for feature in required_features):
                continue

            # Calculate suitability score
            suitability_score = self._calculate_model_suitability(
                config, task_type, complexity, cost_sensitivity
            )

            candidates.append((model_id, suitability_score, config))

        if not candidates:
            return "gemini-2.0-flash"  # Default fallback

        # Return model with highest suitability score
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected_model = candidates[0][0]

        logger.info(f"Selected model {selected_model} for task {task_type}")
        return selected_model

    def _get_required_features(self, task_type: str) -> List[str]:
        """Get required features for a task type."""
        feature_map = {
            "analysis": ["text", "json"],
            "code_generation": ["text", "tools"],
            "vision_analysis": ["vision", "text"],
            "complex_reasoning": ["text", "tools", "json"],
            "creative_writing": ["text"],
            "data_processing": ["json", "tools"]
        }
        return feature_map.get(task_type, ["text"])

    def _calculate_model_suitability(self, config: ModelConfiguration, task_type: str,
                                   complexity: str, cost_sensitivity: str) -> float:
        """Calculate how suitable a model is for the given parameters."""
        score = config.performance_score

        # Adjust for complexity
        if complexity == "high" and "long_context" in config.supported_features:
            score += 0.1
        elif complexity == "low" and config.context_window < 100000:
            score += 0.05

        # Adjust for cost sensitivity
        if cost_sensitivity == "cost_optimized":
            score -= config.cost_per_token * 10000  # Penalize expensive models
        elif cost_sensitivity == "performance_optimized":
            score += config.performance_score * 0.1

        return score

    def create_multi_model_agent(self, agent_type: str, task_profile: Dict[str, Any]) -> MultiModelAgent:
        """Create a multi-model agent configuration."""
        primary_model = self.select_optimal_model(
            task_profile.get("primary_task", "analysis"),
            task_profile.get("complexity", "medium"),
            task_profile.get("cost_sensitivity", "balanced")
        )

        fallback_models = self._select_fallback_models(primary_model, task_profile)

        task_routing_rules = self._create_task_routing_rules(agent_type, task_profile)

        return MultiModelAgent(
            agent_type=agent_type,
            primary_model=primary_model,
            fallback_models=fallback_models,
            task_routing_rules=task_routing_rules,
            performance_thresholds={
                "response_time_threshold": task_profile.get("max_response_time", 5.0),
                "accuracy_threshold": task_profile.get("min_accuracy", 0.8),
                "cost_threshold": task_profile.get("max_cost_per_request", 0.01)
            }
        )

    def _select_fallback_models(self, primary_model: str, task_profile: Dict[str, Any]) -> List[str]:
        """Select appropriate fallback models."""
        all_models = list(self.available_models.keys())
        all_models.remove(primary_model)

        # Sort by performance score for reliability
        fallback_candidates = sorted(
            all_models,
            key=lambda m: self.available_models[m].performance_score,
            reverse=True
        )

        return fallback_candidates[:2]  # Top 2 as fallbacks

    def _create_task_routing_rules(self, agent_type: str, task_profile: Dict[str, Any]) -> Dict[str, str]:
        """Create task routing rules for different scenarios."""
        rules = {}

        # Route complex tasks to high-performance models
        if task_profile.get("complexity") == "high":
            rules["complex_analysis"] = self.select_optimal_model("complex_reasoning", "high")
            rules["code_generation"] = self.select_optimal_model("code_generation", "high")

        # Route vision tasks to vision-capable models
        if task_profile.get("requires_vision", False):
            vision_models = [m for m, config in self.available_models.items()
                           if "vision" in config.supported_features]
            if vision_models:
                rules["vision_analysis"] = vision_models[0]

        # Cost-optimized routing for simple tasks
        rules["simple_query"] = self.select_optimal_model("analysis", "low", "cost_optimized")

        return rules

    def monitor_model_performance(self, model_id: str, task_type: str,
                                response_time: float, success: bool, cost: float):
        """Monitor and record model performance."""
        if model_id not in self.model_performance_history:
            self.model_performance_history[model_id] = []

        performance_record = {
            "timestamp": datetime.now(),
            "task_type": task_type,
            "response_time": response_time,
            "success": success,
            "cost": cost,
            "efficiency_score": (1.0 / response_time) * (1.0 if success else 0.5) / cost if cost > 0 else 0
        }

        self.model_performance_history[model_id].append(performance_record)

        # Keep only last 1000 records per model
        if len(self.model_performance_history[model_id]) > 1000:
            self.model_performance_history[model_id] = self.model_performance_history[model_id][-1000:]

    def get_model_performance_report(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate performance report for models."""
        if model_id:
            return self._get_single_model_report(model_id)
        else:
            return self._get_all_models_report()

    def _get_single_model_report(self, model_id: str) -> Dict[str, Any]:
        """Get performance report for a single model."""
        if model_id not in self.model_performance_history:
            return {"error": f"No performance data for model {model_id}"}

        records = self.model_performance_history[model_id]
        if not records:
            return {"error": f"No performance records for model {model_id}"}

        # Calculate metrics
        total_requests = len(records)
        successful_requests = sum(1 for r in records if r["success"])
        avg_response_time = sum(r["response_time"] for r in records) / total_requests
        avg_cost = sum(r["cost"] for r in records) / total_requests
        success_rate = successful_requests / total_requests

        return {
            "model_id": model_id,
            "total_requests": total_requests,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "avg_cost": avg_cost,
            "config": self.available_models.get(model_id).__dict__ if model_id in self.available_models else {}
        }

    def _get_all_models_report(self) -> Dict[str, Any]:
        """Get performance report for all models."""
        report = {}
        for model_id in self.available_models.keys():
            report[model_id] = self._get_single_model_report(model_id)

        # Add comparison metrics
        if report:
            best_performance = max(report.items(),
                                 key=lambda x: x[1].get("success_rate", 0) / x[1].get("avg_response_time", 1))
            best_cost_effective = min(report.items(),
                                    key=lambda x: x[1].get("avg_cost", 0) / x[1].get("success_rate", 1) if x[1].get("success_rate", 0) > 0 else float('inf'))

            report["comparison"] = {
                "best_performance": best_performance[0],
                "best_cost_effective": best_cost_effective[0]
            }

        return report


# Global multi-model manager instance
multi_model_manager = ADKMultiModelManager()


def select_optimal_model(task_type: str, complexity: str = "medium",
                        cost_sensitivity: str = "balanced") -> str:
    """Convenience function to select optimal model."""
    return multi_model_manager.select_optimal_model(task_type, complexity, cost_sensitivity)


def create_multi_model_agent(agent_type: str, task_profile: Dict[str, Any]) -> MultiModelAgent:
    """Convenience function to create multi-model agent."""
    return multi_model_manager.create_multi_model_agent(agent_type, task_profile)


def get_model_performance_report(model_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get model performance report."""
    return multi_model_manager.get_model_performance_report(model_id)


if __name__ == "__main__":
    print("🚀 ADK Multi-Model Manager Demo")
    print("=" * 50)

    # Test model selection
    analysis_model = select_optimal_model("analysis", "high", "performance_optimized")
    print(f"Selected model for complex analysis: {analysis_model}")

    vision_model = select_optimal_model("vision_analysis", "medium", "balanced")
    print(f"Selected model for vision analysis: {vision_model}")

    # Test multi-model agent creation
    task_profile = {
        "primary_task": "analysis",
        "complexity": "high",
        "cost_sensitivity": "balanced",
        "requires_vision": True,
        "max_response_time": 3.0,
        "min_accuracy": 0.9
    }

    multi_agent = create_multi_model_agent("analyst", task_profile)
    print(f"Created multi-model agent: {multi_agent.agent_type}")
    print(f"Primary model: {multi_agent.primary_model}")
    print(f"Fallback models: {multi_agent.fallback_models}")
    print(f"Task routing rules: {len(multi_agent.task_routing_rules)} rules")

    # Get performance report
    report = get_model_performance_report()
    print(f"Performance report generated for {len(report)-1} models")  # -1 for comparison

    print("\n✅ Multi-model management completed")
