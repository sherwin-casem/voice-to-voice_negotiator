from enum import StrEnum


class WeaknessPattern(StrEnum):
    LONG_ANSWERS = "long_answers"
    FILLER_WORDS = "filler_words"
    WEAK_STAR_STRUCTURE = "weak_star_structure"
    WEAK_TRADE_OFF_DISCUSSION = "weak_trade_off_discussion"
    POOR_ANSWER_OPENING = "poor_answer_opening"
    WEAK_CONCLUSION = "weak_conclusion"
    LACK_OF_CONCRETE_EXAMPLES = "lack_of_concrete_examples"


PATTERN_LABELS: dict[WeaknessPattern, str] = {
    WeaknessPattern.LONG_ANSWERS: "overly long answers",
    WeaknessPattern.FILLER_WORDS: "frequent filler words",
    WeaknessPattern.WEAK_STAR_STRUCTURE: "weak STAR structure",
    WeaknessPattern.WEAK_TRADE_OFF_DISCUSSION: "weak technical trade-off discussions",
    WeaknessPattern.POOR_ANSWER_OPENING: "weak answer openings",
    WeaknessPattern.WEAK_CONCLUSION: "weak conclusions",
    WeaknessPattern.LACK_OF_CONCRETE_EXAMPLES: "lack of concrete examples",
}


TRACKED_DIMENSIONS: tuple[str, ...] = (
    "overall",
    "communication",
    "technical",
    "relevance",
    "structure",
    "conciseness",
    "confidence",
    "problem_solving",
)

DIMENSION_LABELS: dict[str, str] = {
    "overall": "overall performance",
    "communication": "communication",
    "technical": "technical knowledge",
    "relevance": "relevance",
    "structure": "structure",
    "conciseness": "conciseness",
    "confidence": "confidence",
    "problem_solving": "problem solving",
}

TECHNICAL_INTERVIEW_TYPES = frozenset({"technical", "system_design"})
