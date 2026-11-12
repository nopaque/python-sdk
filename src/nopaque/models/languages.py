"""Models for GET /languages."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name."""
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class _LanguagesBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class TranscriptionLanguageEntry(_LanguagesBase):
    """One transcription language. ``code`` is a :data:`TranscriptionLanguage`
    value, typed ``str`` so an unknown code never makes a read raise."""

    code: str
    label: str
    #: The Deepgram models that accept this code. Informational only.
    models: List[str] = []
    #: True only for ``multi``.
    code_switching: Optional[bool] = None


class CallLanguageEntry(_LanguagesBase):
    """One call language. ``code`` is a :data:`CallLanguage` value."""

    code: str
    label: str
    #: The live model this language runs on. Informational only.
    model: Optional[str] = None
    #: True only for ``multi``.
    code_switching: Optional[bool] = None


class TranscriptionLanguageSet(_LanguagesBase):
    default: str
    languages: List[TranscriptionLanguageEntry] = []


class CallLanguageSet(_LanguagesBase):
    default: str
    languages: List[CallLanguageEntry] = []


class LanguageCatalogue(_LanguagesBase):
    """Both language sets, which are distinct and never merged.

    ``transcription`` is what a standard test or mapping run is transcribed
    in; ``call`` is what a mission test is spoken in.
    """

    transcription: TranscriptionLanguageSet
    call: CallLanguageSet
