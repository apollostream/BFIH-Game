#!/usr/bin/env python3
"""
Hermeneutic Synthesis Configuration Schema

Defines and validates the YAML configuration format for multi-analysis
hermeneutic synthesis projects.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path


@dataclass
class TopicConfig:
    """Configuration for a single analysis topic."""
    id: str
    proposition: str
    model: str = "o3-mini"
    difficulty: str = "medium"
    depends_on: List[str] = field(default_factory=list)
    context_from_prior: bool = False
    custom_hypotheses: Optional[List[Dict[str, str]]] = None
    custom_paradigms: Optional[List[Dict[str, str]]] = None

    def validate(self) -> List[str]:
        """Validate topic configuration. Returns list of errors."""
        errors = []
        if not self.id:
            errors.append("Topic must have an 'id'")
        if not self.proposition:
            errors.append(f"Topic '{self.id}' must have a 'proposition'")
        if self.model not in ["o3-mini", "o3", "o4-mini", "gpt-5", "gpt-5.2", "gpt-5-mini"]:
            errors.append(f"Topic '{self.id}' has invalid model: {self.model}")
        if self.difficulty not in ["easy", "medium", "hard"]:
            errors.append(f"Topic '{self.id}' has invalid difficulty: {self.difficulty}")
        return errors


@dataclass
class MetaAnalysisConfig:
    """Configuration for the meta-analysis phase."""
    proposition: str
    hypotheses: List[Dict[str, str]]
    model: str = "o3"
    custom_paradigms: Optional[List[Dict[str, str]]] = None

    def validate(self) -> List[str]:
        """Validate meta-analysis configuration. Returns list of errors."""
        errors = []
        if not self.proposition:
            errors.append("Meta-analysis must have a 'proposition'")
        if not self.hypotheses or len(self.hypotheses) < 2:
            errors.append("Meta-analysis must have at least 2 hypotheses")
        for i, h in enumerate(self.hypotheses):
            if isinstance(h, str):
                continue  # Simple string hypothesis is OK
            if isinstance(h, dict):
                if "id" not in h or "description" not in h:
                    errors.append(f"Meta-analysis hypothesis {i} must have 'id' and 'description'")
        return errors


@dataclass
class SynthesisConfig:
    """Configuration for narrative synthesis."""
    style: str = "philosophical_treatise"
    target_length: str = "book_chapter"
    include_hermeneutic_reflection: bool = True
    include_technical_appendices: bool = True
    include_visualizations: bool = True

    def validate(self) -> List[str]:
        """Validate synthesis configuration. Returns list of errors."""
        errors = []
        valid_styles = ["philosophical_treatise", "academic_paper", "essay", "technical_report"]
        if self.style not in valid_styles:
            errors.append(f"Invalid synthesis style: {self.style}. Must be one of {valid_styles}")
        valid_lengths = ["essay", "book_chapter", "book"]
        if self.target_length not in valid_lengths:
            errors.append(f"Invalid target length: {self.target_length}. Must be one of {valid_lengths}")
        return errors


@dataclass
class ProjectConfig:
    """Top-level project configuration."""
    title: str
    author: str = "BFIH Hermeneutic Synthesis System"
    output_dir: str = "./synthesis_output"
    description: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate project configuration. Returns list of errors."""
        errors = []
        if not self.title:
            errors.append("Project must have a 'title'")
        return errors


@dataclass
class HermeneuticProjectConfig:
    """
    Complete configuration for a hermeneutic synthesis project.

    This is the main configuration object that encompasses all aspects
    of a multi-analysis synthesis project.
    """
    project: ProjectConfig
    topics: List[TopicConfig]
    meta_analysis: MetaAnalysisConfig
    synthesis: SynthesisConfig

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'HermeneuticProjectConfig':
        """Load configuration from a YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HermeneuticProjectConfig':
        """Create configuration from a dictionary."""
        # Parse project config
        project_data = data.get('project', {})
        project = ProjectConfig(
            title=project_data.get('title', 'Untitled Project'),
            author=project_data.get('author', 'BFIH Hermeneutic Synthesis System'),
            output_dir=project_data.get('output_dir', './synthesis_output'),
            description=project_data.get('description')
        )

        # Parse topics
        topics = []
        for t in data.get('topics', []):
            topic = TopicConfig(
                id=t.get('id', ''),
                proposition=t.get('proposition', ''),
                model=t.get('model', 'o3-mini'),
                difficulty=t.get('difficulty', 'medium'),
                depends_on=t.get('depends_on', []),
                context_from_prior=t.get('context_from_prior', False),
                custom_hypotheses=t.get('custom_hypotheses'),
                custom_paradigms=t.get('custom_paradigms')
            )
            topics.append(topic)

        # Parse meta-analysis config
        meta_data = data.get('meta_analysis', {})
        meta_hypotheses = meta_data.get('hypotheses', [])
        # Normalize hypotheses to dict format
        normalized_hypotheses = []
        for i, h in enumerate(meta_hypotheses):
            if isinstance(h, str):
                # Parse "ID: Description" format or just use as description
                if ':' in h:
                    parts = h.split(':', 1)
                    normalized_hypotheses.append({
                        'id': f'MH{i}',
                        'name': parts[0].strip(),
                        'description': parts[1].strip()
                    })
                else:
                    normalized_hypotheses.append({
                        'id': f'MH{i}',
                        'name': f'Hypothesis {i}',
                        'description': h
                    })
            else:
                normalized_hypotheses.append(h)

        meta_analysis = MetaAnalysisConfig(
            proposition=meta_data.get('proposition', ''),
            hypotheses=normalized_hypotheses,
            model=meta_data.get('model', 'o3'),
            custom_paradigms=meta_data.get('custom_paradigms')
        )

        # Parse synthesis config
        synth_data = data.get('synthesis', {})
        synthesis = SynthesisConfig(
            style=synth_data.get('style', 'philosophical_treatise'),
            target_length=synth_data.get('target_length', 'book_chapter'),
            include_hermeneutic_reflection=synth_data.get('include_hermeneutic_reflection', True),
            include_technical_appendices=synth_data.get('include_technical_appendices', True),
            include_visualizations=synth_data.get('include_visualizations', True)
        )

        return cls(
            project=project,
            topics=topics,
            meta_analysis=meta_analysis,
            synthesis=synthesis
        )

    def validate(self) -> List[str]:
        """
        Validate the entire configuration.
        Returns a list of error messages (empty if valid).
        """
        errors = []

        # Validate project
        errors.extend(self.project.validate())

        # Validate topics
        if not self.topics:
            errors.append("Project must have at least one topic")

        topic_ids = set()
        for topic in self.topics:
            errors.extend(topic.validate())
            if topic.id in topic_ids:
                errors.append(f"Duplicate topic id: {topic.id}")
            topic_ids.add(topic.id)

        # Validate dependencies reference valid topics
        for topic in self.topics:
            for dep in topic.depends_on:
                if dep not in topic_ids:
                    errors.append(f"Topic '{topic.id}' depends on unknown topic: {dep}")

        # Check for circular dependencies
        cycle = self._detect_cycle()
        if cycle:
            errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")

        # Validate meta-analysis
        errors.extend(self.meta_analysis.validate())

        # Validate synthesis
        errors.extend(self.synthesis.validate())

        return errors

    def _detect_cycle(self) -> Optional[List[str]]:
        """Detect circular dependencies using DFS. Returns cycle path if found."""
        # Build adjacency list
        graph = {t.id: t.depends_on for t in self.topics}

        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        for topic_id in graph:
            if topic_id not in visited:
                cycle = dfs(topic_id)
                if cycle:
                    return cycle

        return None

    def get_execution_order(self) -> List[str]:
        """
        Return topic IDs in dependency-respecting order (topological sort).
        """
        # Build adjacency list (reversed - we want dependencies first)
        in_degree = {t.id: 0 for t in self.topics}
        graph = {t.id: [] for t in self.topics}

        for topic in self.topics:
            for dep in topic.depends_on:
                graph[dep].append(topic.id)
                in_degree[topic.id] += 1

        # Kahn's algorithm
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def get_topic_by_id(self, topic_id: str) -> Optional[TopicConfig]:
        """Get a topic configuration by its ID."""
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for serialization)."""
        return {
            'project': {
                'title': self.project.title,
                'author': self.project.author,
                'output_dir': self.project.output_dir,
                'description': self.project.description
            },
            'topics': [
                {
                    'id': t.id,
                    'proposition': t.proposition,
                    'model': t.model,
                    'difficulty': t.difficulty,
                    'depends_on': t.depends_on,
                    'context_from_prior': t.context_from_prior,
                    'custom_hypotheses': t.custom_hypotheses,
                    'custom_paradigms': t.custom_paradigms
                }
                for t in self.topics
            ],
            'meta_analysis': {
                'proposition': self.meta_analysis.proposition,
                'hypotheses': self.meta_analysis.hypotheses,
                'model': self.meta_analysis.model,
                'custom_paradigms': self.meta_analysis.custom_paradigms
            },
            'synthesis': {
                'style': self.synthesis.style,
                'target_length': self.synthesis.target_length,
                'include_hermeneutic_reflection': self.synthesis.include_hermeneutic_reflection,
                'include_technical_appendices': self.synthesis.include_technical_appendices,
                'include_visualizations': self.synthesis.include_visualizations
            }
        }

    def save_yaml(self, path: str) -> None:
        """Save configuration to a YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)


def load_project_config(path: str) -> HermeneuticProjectConfig:
    """
    Load and validate a project configuration from a YAML file.

    Raises ValueError if configuration is invalid.
    """
    config = HermeneuticProjectConfig.from_yaml(path)
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    return config


if __name__ == "__main__":
    # Test with example configuration
    import sys

    if len(sys.argv) > 1:
        config = load_project_config(sys.argv[1])
        print(f"Loaded project: {config.project.title}")
        print(f"Topics: {[t.id for t in config.topics]}")
        print(f"Execution order: {config.get_execution_order()}")
    else:
        print("Usage: python hermeneutic_config_schema.py <config.yaml>")
