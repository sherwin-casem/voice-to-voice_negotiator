from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.core.uploads import read_text_upload

from app.modules.context.deps import get_context_preparation_service, get_context_repository
from app.modules.context.repository import ContextRepository
from app.modules.context.service import ContextPreparationService
from app.modules.interview.deps import get_interview_repository, get_user_id
from app.modules.interview.repository import InterviewRepository
from app.schemas.common import ApiResponse
from app.schemas.context import (
    CreateJobDescriptionRequest,
    CreateResumeRequest,
    ParsedProfileSummary,
    ParsedRequirementsSummary,
    PreparedJobDescriptionResponse,
    PreparedResumeResponse,
)

router = APIRouter(prefix="/context", tags=["context"])

_TEXT_UPLOAD_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/octet-stream",
}


def _profile_summary(profile) -> ParsedProfileSummary:
    return ParsedProfileSummary(
        skills=profile.skills,
        experience_count=len(profile.experience),
        project_count=len(profile.projects),
        likely_interview_topics=profile.likely_interview_topics,
    )


def _requirements_summary(requirements) -> ParsedRequirementsSummary:
    return ParsedRequirementsSummary(
        required_skills=requirements.required_skills,
        responsibilities=requirements.responsibilities,
        technical_topics=requirements.technical_topics,
        behavioral_topics=requirements.behavioral_topics,
        likely_interview_topics=requirements.likely_interview_topics,
        evaluation_rubric_hints=requirements.evaluation_rubric_hints,
    )


def _prepared_resume_response(resume, profile) -> PreparedResumeResponse:
    return PreparedResumeResponse(
        id=resume.id,
        title=resume.title,
        summary_text=resume.summary_text,
        parse_status=resume.parse_status,
        created_at=resume.created_at,
        parsed_profile=_profile_summary(profile),
    )


def _prepared_job_description_response(job_description, requirements) -> PreparedJobDescriptionResponse:
    return PreparedJobDescriptionResponse(
        id=job_description.id,
        title=job_description.title,
        company_name=job_description.company_name,
        summary_text=job_description.summary_text,
        parse_status=job_description.parse_status,
        created_at=job_description.created_at,
        parsed_requirements=_requirements_summary(requirements),
    )


@router.post("/resumes", response_model=ApiResponse[PreparedResumeResponse])
async def create_resume(
    body: CreateResumeRequest,
    user_id: UUID = Depends(get_user_id),
    repository: InterviewRepository = Depends(get_interview_repository),
    context_service: ContextPreparationService = Depends(get_context_preparation_service),
    context_repository: ContextRepository = Depends(get_context_repository),
) -> ApiResponse[PreparedResumeResponse]:
    resume = await repository.create_resume(
        user_id,
        title=body.title,
        raw_text=body.raw_text,
        summary_text=body.summary_text,
    )
    profile = await context_service.prepare_resume(resume.id, user_id)
    refreshed = await context_repository.get_resume(resume.id, user_id)
    return ApiResponse(data=_prepared_resume_response(refreshed, profile))


@router.post("/resumes/upload", response_model=ApiResponse[PreparedResumeResponse])
async def upload_resume(
    file: UploadFile = File(...),
    title: str = Form(...),
    user_id: UUID = Depends(get_user_id),
    repository: InterviewRepository = Depends(get_interview_repository),
    context_service: ContextPreparationService = Depends(get_context_preparation_service),
    context_repository: ContextRepository = Depends(get_context_repository),
) -> ApiResponse[PreparedResumeResponse]:
    if file.content_type not in _TEXT_UPLOAD_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only plain-text resume uploads are supported in MVP")

    raw_text = await read_text_upload(file, max_bytes=settings.max_upload_bytes)
    resume = await repository.create_resume(user_id, title=title, raw_text=raw_text)
    profile = await context_service.prepare_resume(
        resume.id,
        user_id,
        source_filename=file.filename,
        mime_type=file.content_type,
    )
    refreshed = await context_repository.get_resume(resume.id, user_id)
    return ApiResponse(data=_prepared_resume_response(refreshed, profile))


@router.get("/resumes/{resume_id}", response_model=ApiResponse[PreparedResumeResponse])
async def get_resume(
    resume_id: UUID,
    user_id: UUID = Depends(get_user_id),
    context_repository: ContextRepository = Depends(get_context_repository),
) -> ApiResponse[PreparedResumeResponse]:
    resume = await context_repository.get_resume(resume_id, user_id)
    profile_summary = ParsedProfileSummary()
    if resume.parsed_profile:
        profile_summary = ParsedProfileSummary(
            skills=resume.parsed_profile.get("skills", []),
            experience_count=len(resume.parsed_profile.get("experience", [])),
            project_count=len(resume.parsed_profile.get("projects", [])),
            likely_interview_topics=resume.parsed_profile.get("likely_interview_topics", []),
        )
    return ApiResponse(
        data=PreparedResumeResponse(
            id=resume.id,
            title=resume.title,
            summary_text=resume.summary_text,
            parse_status=resume.parse_status,
            created_at=resume.created_at,
            parsed_profile=profile_summary,
        )
    )


@router.post("/job-descriptions", response_model=ApiResponse[PreparedJobDescriptionResponse])
async def create_job_description(
    body: CreateJobDescriptionRequest,
    user_id: UUID = Depends(get_user_id),
    repository: InterviewRepository = Depends(get_interview_repository),
    context_service: ContextPreparationService = Depends(get_context_preparation_service),
    context_repository: ContextRepository = Depends(get_context_repository),
) -> ApiResponse[PreparedJobDescriptionResponse]:
    job_description = await repository.create_job_description(
        user_id,
        title=body.title,
        raw_text=body.raw_text,
        company_name=body.company_name,
        summary_text=body.summary_text,
    )
    requirements = await context_service.prepare_job_description(job_description.id, user_id)
    refreshed = await context_repository.get_job_description(job_description.id, user_id)
    return ApiResponse(data=_prepared_job_description_response(refreshed, requirements))


@router.post("/job-descriptions/upload", response_model=ApiResponse[PreparedJobDescriptionResponse])
async def upload_job_description(
    file: UploadFile = File(...),
    title: str = Form(...),
    company_name: str | None = Form(default=None),
    user_id: UUID = Depends(get_user_id),
    repository: InterviewRepository = Depends(get_interview_repository),
    context_service: ContextPreparationService = Depends(get_context_preparation_service),
    context_repository: ContextRepository = Depends(get_context_repository),
) -> ApiResponse[PreparedJobDescriptionResponse]:
    if file.content_type not in _TEXT_UPLOAD_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only plain-text job description uploads are supported in MVP",
        )

    raw_text = await read_text_upload(file, max_bytes=settings.max_upload_bytes)
    job_description = await repository.create_job_description(
        user_id,
        title=title,
        raw_text=raw_text,
        company_name=company_name,
    )
    requirements = await context_service.prepare_job_description(
        job_description.id,
        user_id,
        source_filename=file.filename,
        mime_type=file.content_type,
    )
    refreshed = await context_repository.get_job_description(job_description.id, user_id)
    return ApiResponse(data=_prepared_job_description_response(refreshed, requirements))


@router.get(
    "/job-descriptions/{job_description_id}",
    response_model=ApiResponse[PreparedJobDescriptionResponse],
)
async def get_job_description(
    job_description_id: UUID,
    user_id: UUID = Depends(get_user_id),
    context_repository: ContextRepository = Depends(get_context_repository),
) -> ApiResponse[PreparedJobDescriptionResponse]:
    job_description = await context_repository.get_job_description(job_description_id, user_id)
    requirements_summary = ParsedRequirementsSummary()
    if job_description.parsed_requirements:
        parsed = job_description.parsed_requirements
        requirements_summary = ParsedRequirementsSummary(
            required_skills=parsed.get("required_skills", []),
            responsibilities=parsed.get("responsibilities", []),
            technical_topics=parsed.get("technical_topics", []),
            behavioral_topics=parsed.get("behavioral_topics", []),
            likely_interview_topics=parsed.get("likely_interview_topics", []),
            evaluation_rubric_hints=parsed.get("evaluation_rubric_hints", []),
        )
    return ApiResponse(
        data=PreparedJobDescriptionResponse(
            id=job_description.id,
            title=job_description.title,
            company_name=job_description.company_name,
            summary_text=job_description.summary_text,
            parse_status=job_description.parse_status,
            created_at=job_description.created_at,
            parsed_requirements=requirements_summary,
        )
    )
