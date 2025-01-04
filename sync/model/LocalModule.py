import json
import yaml
from pathlib import Path

from .AttrDict import AttrDict
from .ArchiveIO import ArchiveIO
from ..error import MagiskModuleError

from .JsonIO import JsonIO

from .ModuleNote import ModuleNote
from .ModuleFeatures import ModuleFeatures
from .ModuleManager import ModuleManager
from .RootSolutions import RootSolutions

class LocalModule(AttrDict):
    id: str
    name: str
    version: str
    versionCode: int
    author: str
    description: str
    
    added: float
    timestamp: float
    size: float
    
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
    verified: bool
    note: ModuleNote
    features: ModuleFeatures
    root: RootSolutions
    manager: ModuleManager

    @classmethod
    def clean_json(cls, data):
        if isinstance(data, dict):
            cleaned_dict = {
                key: cls.clean_json(value)
                for key, value in data.items()
                if value not in (None, [], {}, "")
            }
            return {k: v for k, v in cleaned_dict.items() if v not in (None, [], {}, "")}
        elif isinstance(data, list):
            cleaned_list = [cls.clean_json(item) for item in data]
            return [item for item in cleaned_list if item not in (None, [], {}, "")]
        return data

    @classmethod
    def load(cls, file, track, config):    
        zip_compression = track.deep_get("options.archive.compression", default="stored")
        disable_metadata = track.deep_get("options.disableRemoteMetadata", default=False)
        
        cls._zipfile = ArchiveIO(file=file, mode="r", compression=zip_compression)
        fields = cls.expected_fields()

        cleaned_track = cls.clean_json(track)

        try:
            if ("#MAGISK" not in cls._zipfile.file_read("META-INF/com/google/android/updater-script")):
                raise
            if (not cls._zipfile.file_exists("META-INF/com/google/android/update-binary")):
                raise
        except BaseException:
            msg = f"{file.name} is not a magisk module"
            raise MagiskModuleError(msg)

        try:
            props = cls._zipfile.file_read("module.prop")
        except BaseException as err:
            raise MagiskModuleError(err.args)

        obj = AttrDict()
        for item in props.splitlines():
            prop = item.split("=", maxsplit=1)
            if len(prop) != 2:
                continue

            key, value = prop
            if key == "" or key.startswith("#") or key not in fields:
                continue

            _type = fields[key]
            obj[key] = _type(value)

        local_module = LocalModule()
        for key in fields.keys():
            if config.allowedCategories and key == "categories" and cleaned_track.get("categories"):
                local_module[key] = JsonIO.filterArray(config.allowedCategories, cleaned_track.get(key))
            else:
                value = cleaned_track.get(key) if cleaned_track.get(key) is not None else obj.get(key)
                if value is not None and value is not False:
                    local_module[key] = value

        try:
            if not disable_metadata:
                has_yaml = cls._zipfile.file_exists("common/repo.yaml")
                if has_yaml:
                    raw_json = yaml.load(cls._zipfile.file_read("common/repo.yaml"), Loader=yaml.FullLoader)
                else:
                    raw_json = json.loads(cls._zipfile.file_read("common/repo.json"))
                raw_json = cls.clean_json(raw_json)

                for item in raw_json.items():
                    key, value = item

                    _type = fields[key]
                    obj[key] = _type(value)

                for key in fields.keys():
                    value = obj.get(key)
                    if value is not None and value is not False: 
                        local_module[key] = value
                    
        except BaseException:
            pass

        local_module.verified = track.verified or False
        local_module.added = track.added or 0
        local_module.timestamp = track.last_update
        local_module.size = Path(file).stat().st_size        
        
        features = {
            "service": cls._zipfile.file_exists(f"service.sh") or cls._zipfile.file_exists(f"common/service.sh"),
            "post_fs_data": cls._zipfile.file_exists(f"post-fs-data.sh") or cls._zipfile.file_exists(f"common/post-fs-data.sh"),
            # system.prop
            "resetprop": cls._zipfile.file_exists(f"system.prop") or cls._zipfile.file_exists(f"common/system.prop"),
            "sepolicy": cls._zipfile.file_exists(f"sepolicy.rule"),
            
            "zygisk": cls._zipfile.file_exists(f"zygisk/"),
            "action": cls._zipfile.file_exists(f"action.sh") or cls._zipfile.file_exists(f"common/action.sh"),
            
            # KernelSU
            "webroot": cls._zipfile.file_exists(f"webroot/index.html"),
            "post_mount": cls._zipfile.file_exists(f"post-mount.sh") or cls._zipfile.file_exists(f"common/post-mount.sh"),
            "boot_completed": cls._zipfile.file_exists(f"boot-completed.sh") or cls._zipfile.file_exists(f"common/boot-completed.sh"),

            # MMRL
            "modconf": cls._zipfile.file_exists(f"system/usr/share/mmrl/config/{local_module.id}/index.jsx"),
            
            "apks": len([name for name in cls._zipfile.namelist() if name.endswith('.apk')]) != 0
        }
        
        local_module.features = {k: v for k, v in features.items() if v is not None and v is not False}

        return cls.clean_json(local_module)
   
    @classmethod
    def expected_fields(cls, __type=True):
        if __type:
            return cls.__annotations__

        return {k: v.__name__ for k, v in cls.__annotations__.items() if v is not None and v is not False}
