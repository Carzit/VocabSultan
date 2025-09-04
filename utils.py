from enum import Enum

def enum_asdict(dictionary: dict):
    return {k: (v.value if isinstance(v, Enum) else v) for k, v in dictionary.items()}

def enum_asdict_factory(data):
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value   # 或者 obj.name
        return obj
    return dict((k, convert_value(v)) for k, v in data)