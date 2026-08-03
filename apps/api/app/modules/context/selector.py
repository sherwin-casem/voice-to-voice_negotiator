from app.db.enums import InterviewType
from app.modules.context.schemas import InterviewStep, PreparedContextBundle, StepContext

MAX_SUMMARY_CHARS = 600
MAX_LIST_ITEMS = 8
MAX_ITEM_CHARS = 120


class ContextSelector:
    """Select compact, step-relevant slices from prepared context."""

    def select(
        self,
        bundle: PreparedContextBundle,
        step: InterviewStep,
        *,
        asked_topics: list[str] | None = None,
        current_topic_tag: str | None = None,
        prior_answer_text: str | None = None,
    ) -> StepContext:
        asked = {topic.lower() for topic in (asked_topics or [])}
        selectors = {
            InterviewStep.INTERVIEWER_OPENING: self._for_interviewer_opening,
            InterviewStep.INTERVIEWER_FOLLOW_UP: self._for_interviewer_follow_up,
            InterviewStep.EVALUATION_ANSWER: self._for_evaluation_answer,
            InterviewStep.EVALUATION_RUBRIC: self._for_evaluation_rubric,
            InterviewStep.COACH: self._for_coach,
        }
        return selectors[step](
            bundle,
            asked_topics=asked,
            current_topic_tag=current_topic_tag,
            prior_answer_text=prior_answer_text,
        )

    def _for_interviewer_opening(
        self,
        bundle: PreparedContextBundle,
        *,
        asked_topics: set[str],
        current_topic_tag: str | None,
        prior_answer_text: str | None,
    ) -> StepContext:
        _ = current_topic_tag, prior_answer_text
        resume = bundle.resume_profile
        jd = bundle.job_requirements

        skills = _truncate_list(resume.skills if resume else [])
        if jd:
            skills = _truncate_list(_unique(skills + jd.required_skills))

        topics = _remaining_topics(
            (resume.likely_interview_topics if resume else [])
            + (jd.likely_interview_topics if jd else []),
            asked_topics,
        )

        technical = jd.technical_topics[:MAX_LIST_ITEMS] if jd else skills[:MAX_LIST_ITEMS]
        behavioral = jd.behavioral_topics[:MAX_LIST_ITEMS] if jd else [
            "Past behavior and impact",
            "Team collaboration",
        ]

        return StepContext(
            resume_summary=_summary(resume.summary_text if resume else None),
            job_description_summary=_summary(jd.summary_text if jd else None),
            candidate_skills=skills,
            relevant_experience=_experience_lines(resume),
            relevant_projects=_project_lines(resume),
            role_responsibilities=_truncate_list(
                (jd.responsibilities if jd else []) or (resume.responsibilities if resume else [])
            ),
            technical_focus_areas=_truncate_list(technical),
            behavioral_focus_areas=_truncate_list(behavioral),
            likely_interview_topics=_truncate_list(topics),
            evaluation_rubric_hints=_truncate_list(jd.evaluation_rubric_hints if jd else []),
            suggested_difficulty=_suggest_difficulty(bundle),
        )

    def _for_interviewer_follow_up(
        self,
        bundle: PreparedContextBundle,
        *,
        asked_topics: set[str],
        current_topic_tag: str | None,
        prior_answer_text: str | None,
    ) -> StepContext:
        opening = self._for_interviewer_opening(
            bundle,
            asked_topics=asked_topics,
            current_topic_tag=current_topic_tag,
            prior_answer_text=prior_answer_text,
        )

        resume = bundle.resume_profile
        focus_skills = opening.candidate_skills[:4]
        if current_topic_tag and resume:
            matched = [
                skill
                for skill in resume.skills
                if current_topic_tag.lower() in skill.lower()
                or skill.lower() in current_topic_tag.lower()
            ]
            if matched:
                focus_skills = _truncate_list(matched + focus_skills)

        projects = opening.relevant_projects
        if prior_answer_text and resume:
            lowered_answer = prior_answer_text.lower()
            matched_projects = [
                project
                for project in _project_lines(resume)
                if any(token in lowered_answer for token in project.lower().split()[:3])
            ]
            if matched_projects:
                projects = _truncate_list(matched_projects + projects)

        topics = _remaining_topics(opening.likely_interview_topics, asked_topics)
        return StepContext(
            resume_summary=opening.resume_summary,
            job_description_summary=opening.job_description_summary,
            candidate_skills=focus_skills,
            relevant_experience=opening.relevant_experience[:4],
            relevant_projects=projects[:4],
            role_responsibilities=opening.role_responsibilities[:4],
            technical_focus_areas=opening.technical_focus_areas[:4],
            behavioral_focus_areas=opening.behavioral_focus_areas[:4],
            likely_interview_topics=topics[:5],
            evaluation_rubric_hints=opening.evaluation_rubric_hints[:4],
            suggested_difficulty=opening.suggested_difficulty,
        )

    def _for_evaluation_answer(
        self,
        bundle: PreparedContextBundle,
        *,
        asked_topics: set[str],
        current_topic_tag: str | None,
        prior_answer_text: str | None,
    ) -> StepContext:
        _ = asked_topics, prior_answer_text
        opening = self._for_interviewer_opening(
            bundle,
            asked_topics=set(),
            current_topic_tag=current_topic_tag,
            prior_answer_text=None,
        )
        jd = bundle.job_requirements
        resume = bundle.resume_profile

        rubric = jd.evaluation_rubric_hints[:6] if jd else []
        if current_topic_tag:
            rubric = _truncate_list(
                [f"Assess depth on topic: {current_topic_tag}"] + rubric
            )

        responsibilities = opening.role_responsibilities[:5]
        if current_topic_tag and jd:
            matched = [
                item
                for item in jd.responsibilities
                if current_topic_tag.lower() in item.lower()
            ]
            if matched:
                responsibilities = _truncate_list(matched + responsibilities)

        skills = opening.candidate_skills[:6]
        if resume and current_topic_tag:
            matched_skills = [
                skill
                for skill in resume.skills
                if current_topic_tag.lower() in skill.lower()
            ]
            if matched_skills:
                skills = _truncate_list(matched_skills + skills)

        return StepContext(
            resume_summary=opening.resume_summary,
            job_description_summary=opening.job_description_summary,
            candidate_skills=skills,
            relevant_experience=opening.relevant_experience[:4],
            relevant_projects=opening.relevant_projects[:3],
            role_responsibilities=responsibilities,
            technical_focus_areas=opening.technical_focus_areas[:5],
            behavioral_focus_areas=opening.behavioral_focus_areas[:4],
            likely_interview_topics=opening.likely_interview_topics[:4],
            evaluation_rubric_hints=rubric,
            suggested_difficulty=opening.suggested_difficulty,
        )

    def _for_evaluation_rubric(
        self,
        bundle: PreparedContextBundle,
        *,
        asked_topics: set[str],
        current_topic_tag: str | None,
        prior_answer_text: str | None,
    ) -> StepContext:
        _ = asked_topics, current_topic_tag, prior_answer_text
        jd = bundle.job_requirements
        resume = bundle.resume_profile
        interview_type = bundle.interview_type

        technical = jd.technical_topics[:MAX_LIST_ITEMS] if jd else []
        behavioral = jd.behavioral_topics[:MAX_LIST_ITEMS] if jd else []
        if interview_type == InterviewType.TECHNICAL.value:
            behavioral = behavioral[:3]
        elif interview_type == InterviewType.BEHAVIORAL.value:
            technical = technical[:3]

        rubric = jd.evaluation_rubric_hints[:MAX_LIST_ITEMS] if jd else [
            "Role alignment",
            "Answer structure",
            "Evidence of impact",
        ]

        return StepContext(
            resume_summary=_summary(resume.summary_text if resume else None),
            job_description_summary=_summary(jd.summary_text if jd else None),
            candidate_skills=_truncate_list((resume.skills if resume else [])[:6]),
            relevant_experience=_experience_lines(resume)[:3],
            relevant_projects=_project_lines(resume)[:2],
            role_responsibilities=_truncate_list(jd.responsibilities[:6] if jd else []),
            technical_focus_areas=_truncate_list(technical),
            behavioral_focus_areas=_truncate_list(behavioral),
            likely_interview_topics=_truncate_list(jd.likely_interview_topics[:6] if jd else []),
            evaluation_rubric_hints=_truncate_list(rubric),
            suggested_difficulty=_suggest_difficulty(bundle),
        )

    def _for_coach(
        self,
        bundle: PreparedContextBundle,
        *,
        asked_topics: set[str],
        current_topic_tag: str | None,
        prior_answer_text: str | None,
    ) -> StepContext:
        _ = asked_topics, current_topic_tag, prior_answer_text
        rubric = self._for_evaluation_rubric(
            bundle,
            asked_topics=set(),
            current_topic_tag=None,
            prior_answer_text=None,
        )
        return StepContext(
            resume_summary=rubric.resume_summary,
            job_description_summary=rubric.job_description_summary,
            candidate_skills=rubric.candidate_skills[:5],
            relevant_experience=rubric.relevant_experience[:2],
            relevant_projects=rubric.relevant_projects[:2],
            role_responsibilities=rubric.role_responsibilities[:3],
            technical_focus_areas=rubric.technical_focus_areas[:3],
            behavioral_focus_areas=rubric.behavioral_focus_areas[:3],
            likely_interview_topics=rubric.likely_interview_topics[:3],
            evaluation_rubric_hints=rubric.evaluation_rubric_hints[:5],
            suggested_difficulty=rubric.suggested_difficulty,
        )


def _summary(value: str | None) -> str | None:
    if not value:
        return None
    return value[:MAX_SUMMARY_CHARS]


def _truncate_list(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        trimmed = item.strip()[:MAX_ITEM_CHARS]
        if trimmed:
            output.append(trimmed)
        if len(output) >= MAX_LIST_ITEMS:
            break
    return output


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _experience_lines(resume) -> list[str]:
    if resume is None:
        return []
    lines: list[str] = []
    for entry in resume.experience:
        company = f" at {entry.company}" if entry.company else ""
        duration = f" ({entry.duration})" if entry.duration else ""
        lines.append(f"{entry.title}{company}{duration}"[:MAX_ITEM_CHARS])
    return _truncate_list(lines)


def _project_lines(resume) -> list[str]:
    if resume is None:
        return []
    lines = [f"{project.name}: {project.description}"[:MAX_ITEM_CHARS] for project in resume.projects]
    return _truncate_list(lines)


def _remaining_topics(topics: list[str], asked_topics: set[str]) -> list[str]:
    return [topic for topic in topics if topic.lower() not in asked_topics]


def _suggest_difficulty(bundle: PreparedContextBundle) -> str | None:
    jd = bundle.job_requirements
    if jd and jd.experience_level:
        return jd.experience_level
    if bundle.difficulty:
        return bundle.difficulty
    resume = bundle.resume_profile
    if resume and resume.years_experience is not None:
        if resume.years_experience >= 8:
            return "senior"
        if resume.years_experience <= 2:
            return "junior"
        return "mid"
    return None
