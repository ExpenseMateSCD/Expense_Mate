from typing import Dict

from .database import DatabaseManager


class AnalyticsEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_category_breakdown(
        self,
        trans_type: str = "expense",
        month_year: str = None
    ) -> Dict[str, float]:

        transactions = self.db.get_all_transactions()

        filtered = [
            t for t in transactions
            if t.trans_type.lower() == trans_type.lower()
            and (not month_year or t.date.startswith(month_year))
        ]

        breakdown: Dict[str, float] = {}

        for t in filtered:
            breakdown[t.category] = breakdown.get(t.category, 0.0) + t.amount

        return breakdown

    def get_monthly_trends(self) -> Dict[str, Dict[str, float]]:
        transactions = self.db.get_all_transactions()

        trends: Dict[str, Dict[str, float]] = {}

        for t in transactions:
            my = t.date[:7]

            if my not in trends:
                trends[my] = {
                    "income": 0.0,
                    "expense": 0.0,
                    "savings": 0.0
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

    def generate_ascii_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "Breakdown",
        max_bar_width: int = 40
    ) -> str:

        if not data:
            return f"\n--- {title} ---\nNo data available to display."

        total = sum(data.values())
        max_val = max(data.values()) if data.values() else 1.0

        output = [
            f"\n=== {title} (Total: {total:.2f}) ==="
        ]

        for label, val in sorted(
            data.items(),
            key=lambda x: x[1],
            reverse=True
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