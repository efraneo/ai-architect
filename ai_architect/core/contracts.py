"""
=========================================================
Core Contracts

Shared Interfaces
=========================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_architect.core.result import Result


class Component(ABC):
    """
    Base interface for every QUANT component.
    """

    @property
    @abstractmethod
    def name(
        self,
    ) -> str: ...

    @abstractmethod
    def health(
        self,
    ) -> dict: ...


class Analyzer(Component):
    @abstractmethod
    def analyze(
        self,
        context,
    ) -> Result: ...


class Planner(Component):
    @abstractmethod
    def build(
        self,
        context,
    ) -> Result: ...


class Executor(Component):
    @abstractmethod
    def execute(
        self,
        context,
    ) -> Result: ...


class Validator(Component):
    @abstractmethod
    def validate(
        self,
        context,
    ) -> Result: ...


class Generator(Component):
    @abstractmethod
    def generate(
        self,
        context,
    ) -> Result: ...


class Reviewer(Component):
    @abstractmethod
    def review(
        self,
        context,
    ) -> Result: ...
