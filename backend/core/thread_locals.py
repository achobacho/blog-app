import threading

_local = threading.local()


def set_admin_request_flag(value: bool):
    _local.from_admin = value


def get_admin_request_flag() -> bool:
    return getattr(_local, "from_admin", False)
