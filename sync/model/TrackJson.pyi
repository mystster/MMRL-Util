from enum import Enum
from pathlib import Path
from typing import Dict, Type

from .AttrDict import AttrDict
from .JsonIO import JsonIO


class TrackJson(AttrDict, JsonIO):
    id: str
    enable: bool
    verified: bool
    update_to: str
    changelog: str
    license: str
    homepage: str
    source: str
    support: str
    donate: str
    max_num: int
    # author: str
    # contributors: list[str]
    cover: str
    icon: str
    screenshots: list[str]
    require: list[str]
    category: str
    categories: list[str]
    readme: str
    require: list[str]
    antifeatures: list[str]

    # without manually
    added: float 
    last_update: float
    versions: int

    @property
    def type(self) -> TrackType: ...
    def json(self) -> AttrDict: ...
    def write(self, file: Path): ...
    @classmethod
    def load(cls, file: Path) -> TrackJson: ...
    @classmethod
    def filename(cls, yaml: bool) -> str: ...
    @classmethod
    @classmethod
    def expected_fields(cls, __type: bool = ...) -> Dict[str, Type]: ...


class TrackType(Enum):
    UNKNOWN: TrackType
    ONLINE_JSON: TrackType
    ONLINE_ZIP: TrackType
    GIT: TrackType
    LOCAL_JSON: TrackType
    LOCAL_ZIP: TrackType
