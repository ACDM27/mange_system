from typing import Optional, Any
from schemas import ResponseModel


def success_response(data: Any = None, msg: str = "success", code: int = 200) -> dict:
    """Create a successful response"""
    return ResponseModel(code=code, msg=msg, data=data).model_dump()


def error_response(msg: str = "error", code: int = 400, data: Any = None) -> dict:
    """Create an error response"""
    return ResponseModel(code=code, msg=msg, data=data).model_dump()
