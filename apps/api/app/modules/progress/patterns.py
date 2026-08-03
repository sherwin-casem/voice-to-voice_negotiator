from app.modules.progress.constants import PATTERN_LABELS, WeaknessPattern
from app.modules.progress.schemas import RecurringWeakness, SessionProgressRecord


def detect_recurring_weaknesses(
    records: list[SessionProgressRecord],
    *,
    min_occurrences: int = 2,
    persistence_ratio: float = 0.4,
) -> list[RecurringWeakness]:
    if not records:
        return []

    session_count = len(records)
    counts: dict[WeaknessPattern, int] = {}
    for record in records:
        seen_in_session: set[WeaknessPattern] = set(record.pattern_signals)
        for pattern in seen_in_session:
            counts[pattern] = counts.get(pattern, 0) + 1

    recurring: list[RecurringWeakness] = []
    for pattern, occurrences in counts.items():
        frequency = occurrences / session_count
        is_persistent = occurrences >= min_occurrences and frequency >= persistence_ratio
        if occurrences >= min_occurrences:
            recurring.append(
                RecurringWeakness(
                    pattern=pattern,
                    label=PATTERN_LABELS[pattern],
                    occurrences=occurrences,
                    session_count=session_count,
                    frequency=round(frequency, 3),
                    is_persistent=is_persistent,
                )
            )

    recurring.sort(key=lambda item: (-item.occurrences, -item.frequency, item.label))
    return recurring
