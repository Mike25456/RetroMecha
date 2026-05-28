_REGISTRY: dict = {}

def register_animation(name: str):
    def decorator(cls):
        _REGISTRY[name] = cls
        return cls
    return decorator

def get_animation(name: str):
    return _REGISTRY.get(name)

def list_animations() -> list:
    return list(_REGISTRY.keys())
