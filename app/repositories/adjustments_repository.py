"""Data access for the Time Adjustments (Ajustes) module."""
from __future__ import annotations

from datetime import date

from sqlalchemy import case, func, select

from app.database.models.adjustments import TimeAdjustment
from app.database.models.machining import Machine, Operator
from app.repositories.base import BaseRepository


class TimeAdjustmentRepository(BaseRepository[TimeAdjustment]):
    model = TimeAdjustment

    def active_between(self, start: date, end: date) -> list[TimeAdjustment]:
        stmt = (
            select(TimeAdjustment)
            .where(
                func.date(TimeAdjustment.record_date) >= start,
                func.date(TimeAdjustment.record_date) <= end,
                TimeAdjustment.active.is_(True),
            )
            .order_by(TimeAdjustment.record_date.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def summary_by_operator(self, start: date, end: date) -> list[tuple[str, int, int, float]]:
        """(operator_name, improvements, worsenings, net_seconds_saved)."""
        stmt = (
            select(
                Operator.name,
                func.sum(
                    case(
                        (TimeAdjustment.previous_time_seconds > TimeAdjustment.current_time_seconds, 1),
                        else_=0,
                    )
                ).label("improvements"),
                func.sum(
                    case(
                        (TimeAdjustment.previous_time_seconds <= TimeAdjustment.current_time_seconds, 1),
                        else_=0,
                    )
                ).label("worsenings"),
                func.sum(
                    TimeAdjustment.previous_time_seconds - TimeAdjustment.current_time_seconds
                ).label("net_saved"),
            )
            .join(Operator, Operator.id == TimeAdjustment.operator_id)
            .where(
                func.date(TimeAdjustment.record_date) >= start,
                func.date(TimeAdjustment.record_date) <= end,
                TimeAdjustment.active.is_(True),
            )
            .group_by(Operator.id)
            .order_by(func.sum(TimeAdjustment.previous_time_seconds - TimeAdjustment.current_time_seconds).desc())
        )
        return [
            (name, int(imp or 0), int(wor or 0), round(float(net or 0), 2))
            for name, imp, wor, net in self.session.execute(stmt).all()
        ]

    def summary_by_machine(self, start: date, end: date) -> list[tuple[str, int, int, float]]:
        """(machine_name, improvements, worsenings, net_seconds_saved)."""
        stmt = (
            select(
                Machine.name,
                func.sum(
                    case(
                        (TimeAdjustment.previous_time_seconds > TimeAdjustment.current_time_seconds, 1),
                        else_=0,
                    )
                ).label("improvements"),
                func.sum(
                    case(
                        (TimeAdjustment.previous_time_seconds <= TimeAdjustment.current_time_seconds, 1),
                        else_=0,
                    )
                ).label("worsenings"),
                func.sum(
                    TimeAdjustment.previous_time_seconds - TimeAdjustment.current_time_seconds
                ).label("net_saved"),
            )
            .join(Machine, Machine.id == TimeAdjustment.machine_id)
            .where(
                func.date(TimeAdjustment.record_date) >= start,
                func.date(TimeAdjustment.record_date) <= end,
                TimeAdjustment.active.is_(True),
            )
            .group_by(Machine.id)
            .order_by(func.sum(TimeAdjustment.previous_time_seconds - TimeAdjustment.current_time_seconds).desc())
        )
        return [
            (name, int(imp or 0), int(wor or 0), round(float(net or 0), 2))
            for name, imp, wor, net in self.session.execute(stmt).all()
        ]

    def monthly_totals(self, start: date, end: date) -> list[tuple[str, int, int]]:
        """(month_str, improvements, worsenings) per month."""
        stmt = (
            select(
                func.strftime("%Y-%m", TimeAdjustment.record_date).label("month"),
                func.sum(
                    case(
                        (TimeAdjustment.previous_time_seconds > TimeAdjustment.current_time_seconds, 1),
                        else_=0,
                    )
                ).label("improvements"),
                func.sum(
                    case(
                        (TimeAdjustment.previous_time_seconds <= TimeAdjustment.current_time_seconds, 1),
                        else_=0,
                    )
                ).label("worsenings"),
            )
            .where(
                func.date(TimeAdjustment.record_date) >= start,
                func.date(TimeAdjustment.record_date) <= end,
                TimeAdjustment.active.is_(True),
            )
            .group_by("month")
            .order_by("month")
        )
        return [
            (m, int(imp or 0), int(wor or 0))
            for m, imp, wor in self.session.execute(stmt).all()
        ]
