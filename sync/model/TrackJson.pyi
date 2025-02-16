from enum import Enum
from pathlib import Path
from typing import Dict, Type

from .AttrDict import AttrDict
from .JsonIO import JsonIO

from .ModuleNote import ModuleNote
from .ModuleFeatures import ModuleFeatures
from .ModuleManager import ModuleManager
from .RootSolutions import RootSolutions
from .TrackOptions import TrackOptions

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
 
    # FoxMMM supported props
    maxApi: int
    minApi: int
    
    # MMRL supported props
    category: str
    categories: list[str]
    icon: str
    homepage: str
    donate: str
    support: str
    cover: str
    screenshots: list[str]
    license: str
    screenshots: list[str]
    readme: str
    require: list[str]
    arch: list[str]
    devices: list[str]
    verified: bool
    note: ModuleNote
    features: ModuleFeatures
    root: RootSolutions
    manager: ModuleManager
    
    options: TrackOptions

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
    def filename(cls, module_folder: Path) -> str: ...
    @classmethod
    def expected_fields(cls, __type: bool = ...) -> Dict[str, Type]: ...


class TrackType(Enum):
    UNKNOWN: TrackType
    ONLINE_JSON: TrackType
    ONLINE_ZIP: TrackType
    GIT: TrackType
    LOCAL_JSON: TrackType
    LOCAL_ZIP: TrackType
