from sqlalchemy import Enum

from app.db.enums import (
    AgentName,
    DocumentParseStatus,
    EvaluationRunStatus,
    EvaluationScope,
    HireRecommendation,
    InterviewSessionStatus,
    InterviewType,
    SpeakerRole,
)

InterviewTypeEnum = Enum(
    InterviewType,
    name="interview_type",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

InterviewSessionStatusEnum = Enum(
    InterviewSessionStatus,
    name="interview_session_status",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

EvaluationScopeEnum = Enum(
    EvaluationScope,
    name="evaluation_scope",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

EvaluationRunStatusEnum = Enum(
    EvaluationRunStatus,
    name="evaluation_run_status",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

AgentNameEnum = Enum(
    AgentName,
    name="agent_name",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

SpeakerRoleEnum = Enum(
    SpeakerRole,
    name="speaker_role",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

DocumentParseStatusEnum = Enum(
    DocumentParseStatus,
    name="document_parse_status",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)

HireRecommendationEnum = Enum(
    HireRecommendation,
    name="hire_recommendation",
    native_enum=True,
    create_constraint=True,
    values_callable=lambda enum: [member.value for member in enum],
)
