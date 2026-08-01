import enum


class InterviewType(str, enum.Enum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    SYSTEM_DESIGN = "system_design"
    HR = "hr"
    LEADERSHIP = "leadership"


class InterviewSessionStatus(str, enum.Enum):
    CREATED = "created"
    CONFIGURED = "configured"
    ACTIVE = "active"
    COMPLETING = "completing"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EVALUATION_FAILED = "evaluation_failed"


class EvaluationScope(str, enum.Enum):
    SESSION = "session"
    ANSWER = "answer"


class EvaluationRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentName(str, enum.Enum):
    INTERVIEWER = "interviewer"
    INTERVIEW_ANALYST = "interview_analyst"
    COMMUNICATION_EVALUATION = "communication_evaluation"
    TECHNICAL_EVALUATION = "technical_evaluation"
    BEHAVIORAL_EVALUATION = "behavioral_evaluation"
    HIRING_MANAGER_EVALUATION = "hiring_manager_evaluation"
    SCORING_JUDGE = "scoring_judge"
    IMPROVEMENT_COACH = "improvement_coach"


class SpeakerRole(str, enum.Enum):
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"


class DocumentParseStatus(str, enum.Enum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"


class HireRecommendation(str, enum.Enum):
    STRONG_HIRE = "strong_hire"
    LEAN_HIRE = "lean_hire"
    NEUTRAL = "neutral"
    LEAN_NO_HIRE = "lean_no_hire"
    NO_HIRE = "no_hire"
