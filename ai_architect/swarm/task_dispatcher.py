"""
=========================================================
Task Dispatcher
=========================================================
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor


class TaskDispatcher:
    def dispatch(
        self,
        project: str,
        agents: list,
    ) -> dict:

        reports = {}

        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {
                executor.submit(
                    agent.review,
                    project,
                ): agent
                for agent in agents
            }

            for future, agent in futures.items():
                try:
                    reports[agent.name] = future.result()

                except Exception as error:
                    reports[agent.name] = {
                        "status": "FAILED",
                        "error": str(error),
                    }

        return reports
