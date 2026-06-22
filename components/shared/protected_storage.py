"""User-scoped protected storage backed by Windows DPAPI."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os


CRYPTPROTECT_UI_FORBIDDEN = 0x01


class ProtectedStorageUnavailable(RuntimeError):
    """Raised when secure user-scoped storage is unavailable."""


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _blob_from_bytes(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    return _DataBlob(len(data), buffer), buffer


def _consume_blob(blob: _DataBlob) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob.pbData)


def protect_bytes(data: bytes, description: str = "Suite Digital Fresnillo") -> bytes:
    if os.name != "nt":
        raise ProtectedStorageUnavailable("DPAPI solo está disponible en Windows.")
    input_blob, _buffer = _blob_from_bytes(data)
    output_blob = _DataBlob()
    success = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        description,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    if not success:
        raise ctypes.WinError()
    return _consume_blob(output_blob)


def unprotect_bytes(data: bytes) -> bytes:
    if os.name != "nt":
        raise ProtectedStorageUnavailable("DPAPI solo está disponible en Windows.")
    input_blob, _buffer = _blob_from_bytes(data)
    output_blob = _DataBlob()
    success = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    if not success:
        raise ctypes.WinError()
    return _consume_blob(output_blob)


__all__ = [
    "ProtectedStorageUnavailable",
    "protect_bytes",
    "unprotect_bytes",
]
