"""Shared Pydantic base models for tile payloads and results."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TileModel(BaseModel):
    """Base Pydantic model with relaxed settings for tile data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TilePayload(TileModel):
    """Marker base class for tile input models."""


class TileResult(TileModel):
    """Marker base class for tile output models."""
