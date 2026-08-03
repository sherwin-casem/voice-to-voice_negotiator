from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.interview.deps import get_interview_orchestrator, get_interview_repository, get_user_id
from app.modules.interview.orchestrator import InterviewOrchestrator
from app.modules.interview.repository import InterviewRepository
from app.modules.interview.schemas import (
    AnswerRecord,
    QuestionRecord,
    SessionConfigInput,
    SessionRecord,
)
from app.schemas.common import ApiResponse
from app.schemas.interview import (
    ConfigureSessionRequest,
    CreateSessionRequest,
    EndSessionRequest,
    QuestionResponse,
    QuestionResultResponse,
    SessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    AnswerResponse,
)

router = APIRouter(tags=["interviews"])


def _session_response(record: SessionRecord) -> SessionResponse:
    return SessionResponse(
        id=record.id,
        user_id=record.user_id,
        status=record.status,
        interview_type=record.interview_type,
        title=record.title,
        config=record.config_snapshot,
        question_count=record.question_count,
        resume_id=record.resume_id,
        job_description_id=record.job_description_id,
        started_at=record.started_at,
        ended_at=record.ended_at,
        end_reason=record.end_reason,
    )


def _question_response(record: QuestionRecord) -> QuestionResponse:
    return QuestionResponse(
        id=record.id,
        session_id=record.session_id,
        sequence_num=record.sequence_num,
        question_text=record.question_text,
        topic_tag=record.topic_tag,
        follow_up_intent=record.follow_up_intent,
        is_follow_up=record.is_follow_up,
        asked_at=record.asked_at,
        agent_metadata=record.agent_metadata,
    )


def _answer_response(record: AnswerRecord) -> AnswerResponse:
    return AnswerResponse(
        id=record.id,
        session_id=record.session_id,
        question_id=record.question_id,
        answer_text=record.answer_text,
        answered_at=record.answered_at,
        duration_ms=record.duration_ms,
        word_count=record.word_count,
    )


@router.post("/sessions", response_model=ApiResponse[SessionResponse])
async def create_session(
    body: CreateSessionRequest,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[SessionResponse]:
    session = await orchestrator.create_session(user_id, title=body.title)
    return ApiResponse(data=_session_response(session))


@router.patch("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def configure_session(
    session_id: UUID,
    body: ConfigureSessionRequest,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[SessionResponse]:
    config = SessionConfigInput(
        interview_type=body.interview_type,
        difficulty=body.difficulty,
        target_role=body.target_role,
        company_context=body.company_context,
        max_questions=body.max_questions,
        target_duration_minutes=body.target_duration_minutes,
        title=body.title,
        resume_id=body.resume_id,
        job_description_id=body.job_description_id,
    )
    session = await orchestrator.configure_session(session_id, user_id, config)
    return ApiResponse(data=_session_response(session))


@router.get("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def get_session(
    session_id: UUID,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[SessionResponse]:
    session = await orchestrator.get_session(session_id, user_id)
    return ApiResponse(data=_session_response(session))


@router.post("/sessions/{session_id}/start", response_model=ApiResponse[QuestionResultResponse])
async def start_session(
    session_id: UUID,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[QuestionResultResponse]:
    result = await orchestrator.start(session_id, user_id)
    return ApiResponse(
        data=QuestionResultResponse(
            session=_session_response(result.session),
            question=_question_response(result.question),
            should_end_session=result.should_end_session,
        )
    )


@router.post(
    "/sessions/{session_id}/questions/next",
    response_model=ApiResponse[QuestionResultResponse],
)
async def ask_next_question(
    session_id: UUID,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[QuestionResultResponse]:
    result = await orchestrator.ask_next_question(session_id, user_id)
    return ApiResponse(
        data=QuestionResultResponse(
            session=_session_response(result.session),
            question=_question_response(result.question),
            should_end_session=result.should_end_session,
        )
    )


@router.post("/sessions/{session_id}/answers", response_model=ApiResponse[SubmitAnswerResponse])
async def submit_answer(
    session_id: UUID,
    body: SubmitAnswerRequest,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[SubmitAnswerResponse]:
    result = await orchestrator.submit_answer(
        session_id,
        user_id,
        body.question_id,
        answer_text=body.answer_text,
        duration_ms=body.duration_ms,
    )
    return ApiResponse(
        data=SubmitAnswerResponse(
            session=_session_response(result.session),
            answer=_answer_response(result.answer),
        )
    )


@router.post("/sessions/{session_id}/end", response_model=ApiResponse[SessionResponse])
async def end_session(
    session_id: UUID,
    body: EndSessionRequest,
    user_id: UUID = Depends(get_user_id),
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> ApiResponse[SessionResponse]:
    session = await orchestrator.end_session(session_id, user_id, reason=body.reason)
    return ApiResponse(data=_session_response(session))
