"""Converter registry for plugin management."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aixtract.converters.base import BaseConverter
    from aixtract.models.config import ExtractionConfig


class ConverterRegistry:
    """Registry for document converters."""

    _converters: dict[str, type["BaseConverter"]] = {}
    _extension_map: dict[str, str] = {}
    _mimetype_map: dict[str, str] = {}

    @classmethod
    def register(cls, converter_class: type["BaseConverter"]) -> type["BaseConverter"]:
        """Register a converter class.

        Can be used as a decorator:
            @ConverterRegistry.register
            class MyConverter(BaseConverter):
                ...
        """
        name = converter_class.name
        cls._converters[name] = converter_class

        # Map extensions
        for ext in converter_class.supported_extensions:
            ext_clean = ext.lower().lstrip('.')
            cls._extension_map[ext_clean] = name

        # Map mimetypes
        for mime in converter_class.supported_mimetypes:
            cls._mimetype_map[mime] = name

        return converter_class

    @classmethod
    def get_converter(
        cls,
        extension: str | None = None,
        mimetype: str | None = None,
        config: "ExtractionConfig | None" = None,
    ) -> "BaseConverter | None":
        """Get appropriate converter for file type."""
        from aixtract.models.config import ExtractionConfig

        config = config or ExtractionConfig()
        name = None

        if extension:
            ext = extension.lower().lstrip('.')
            name = cls._extension_map.get(ext)

        if not name and mimetype:
            name = cls._mimetype_map.get(mimetype)

        if not name:
            return None

        if name in config.disabled_converters:
            return None

        converter_class = cls._converters.get(name)
        if not converter_class:
            return None

        return converter_class(config)

    @classmethod
    def list_converters(cls) -> list[dict]:
        """List all registered converters."""
        return [
            {
                "name": name,
                "extensions": conv.supported_extensions,
                "mimetypes": conv.supported_mimetypes,
                "requires": conv.requires,
            }
            for name, conv in cls._converters.items()
        ]

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get all supported file extensions."""
        return list(cls._extension_map.keys())
