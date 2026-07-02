from typing import Dict, Optional, List
import logging
from .base import ToolBase

logger = logging.getLogger("moon_core.tools.registry")

class ToolRegistry:
    """
    Central registry for managing available tools.
    Tools must be registered here before MoonAgent can request them.
    """
    def __init__(self):
        self._tools: Dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is already registered. Overwriting.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} (Tier: {tool.tier.value})")

    def get(self, name: str) -> Optional[ToolBase]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolBase]:
        return list(self._tools.values())
