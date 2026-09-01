"""
=========================================================
Consensus Engine
=========================================================
"""

from __future__ import annotations


class ConsensusEngine:
    def evaluate(
        self,
        reports: dict,
    ) -> dict:

        warnings = 0

        failures = 0

        success = 0

        for report in reports.values():
            if not isinstance(
                report,
                dict,
            ):
                continue

            status = report.get(
                "status",
                "OK",
            )

            if status == "FAILED":
                failures += 1

            elif status == "WARNING":
                warnings += 1

            else:
                success += 1

        approved = failures == 0

        return {
            "approved": approved,
            "success": success,
            "warnings": warnings,
            "failures": failures,
            "total_agents": len(reports),
        }
