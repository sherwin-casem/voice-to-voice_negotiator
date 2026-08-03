from pathlib import Path

from app.ai.prompts.evaluation._shared import format_evaluation_context
from app.modules.evaluation.schemas import EvaluationContext

PROMPT_VERSION = "1.0"
SCHEMA_VERSION = "1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def build_hiring_manager_messages(context: EvaluationContext) -> list[dict[str, str]]:
    fields = format_evaluation_context(context)
    return [
        {
            "role": "system",
            "content": _load_template("system.txt").format(prompt_version=PROMPT_VERSION, **fields).strip(),
        },
        {"role": "user", "content": _load_template("user.txt").format(**fields).strip()},
    ]
