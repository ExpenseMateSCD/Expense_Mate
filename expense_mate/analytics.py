from typing import Dict, Optional, Union

from .database import DatabaseManager
from .repositories import TransactionRepository


class AnalyticsService:
    """Business logic for spending summaries, category breakdowns, and financial trends."""

    def __init__(
        self,
        repository: Union[TransactionRepository, DatabaseManager],
    ):
        if isinstance(repository, DatabaseManager):
            self.repository = TransactionRepository(repository)
        else:
            self.repository = repository

    def get_category_breakdown(
        self,
        trans_type: str = "expense",
        month_year: Optional[str] = None,
    ) -> Dict[str, float]:
        if month_year:
            transactions = self.repository.get_by_month(month_year)
        else:
            transactions = self.repository.get_all()

        filtered = [
            t for t in transactions
            if t.trans_type.lower() == trans_type.lower()
        ]

        breakdown: Dict[str, float] = {}
        for t in filtered:
            breakdown[t.category] = breakdown.get(t.category, 0.0) + t.amount

        return breakdown

    def get_monthly_trends(self) -> Dict[str, Dict[str, float]]:
        transactions = self.repository.get_all()
        trends: Dict[str, Dict[str, float]] = {}

        for t in transactions:
            my = t.date[:7]
            if my not in trends:
                trends[my] = {
                    "income": 0.0,
                    "expense": 0.0,
                    "savings": 0.0,
                }

            if t.trans_type == "income":
                trends[my]["income"] += t.amount
            elif t.trans_type == "expense":
                trends[my]["expense"] += t.amount

        for my in trends:
            trends[my]["savings"] = (
                trends[my]["income"] - trends[my]["expense"]
            )

        return dict(sorted(trends.items()))


class ChartFormatter:
    """Presentation formatter for text-based ASCII charts."""

    @staticmethod
    def generate_ascii_bar_chart(
        data: Dict[str, float],
        title: str = "Breakdown",
        max_bar_width: int = 40,
    ) -> str:
        if not data:
            return f"\n--- {title} ---\nNo data available to display."

        total = sum(data.values())
        max_val = max(data.values()) if data.values() else 1.0

        output = [f"\n=== {title} (Total: {total:.2f}) ==="]

        for label, val in sorted(
            data.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            pct = (val / total * 100) if total > 0 else 0
            bar_len = (
                int((val / max_val) * max_bar_width)
                if max_val > 0 else 0
            )
            bar = "█" * bar_len

            output.append(
                f"{label:<16} | "
                f"{bar:<{max_bar_width}} | "
                f"{val:>10.2f} ({pct:>5.1f}%)"
            )

        return "\n".join(output)


class AnalyticsEngine:
    """Backward-compatible facade delegating to AnalyticsService and ChartFormatter."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.service = AnalyticsService(TransactionRepository(db_manager))
        self.formatter = ChartFormatter()

    def get_category_breakdown(
        self,
        trans_type: str = "expense",
        month_year: Optional[str] = None,
    ) -> Dict[str, float]:
        return self.service.get_category_breakdown(trans_type, month_year)

    def get_monthly_trends(self) -> Dict[str, Dict[str, float]]:
        return self.service.get_monthly_trends()

    def generate_ascii_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "Breakdown",
        max_bar_width: int = 40,
    ) -> str:
        return self.formatter.generate_ascii_bar_chart(
            data, title=title, max_bar_width=max_bar_width
        )
