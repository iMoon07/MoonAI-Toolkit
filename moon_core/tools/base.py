from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

class PermissionTier(Enum):
    SAFE = "SAFE"           # Direct execution (e.g., read_file)
    CONFIRM = "CONFIRM"     # Requires Approval Token (e.g., nmap, ffuf)
    DANGEROUS = "DANGEROUS" # Requires typed confirmation (e.g., rm, exploit)
    BLOCKED = "BLOCKED"     # Never execute

@dataclass
class ToolResult:
    """Structured result returned by every tool in MoonAI."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    artifacts: List[str] = field(default_factory=list)
    summary: str = ""
    confidence: float = 1.0

class ToolBase(ABC):
    """
    Abstract base class for all Moon tools.
    Enforces that tools provide a name, description, permission tier,
    and a structured execution method returning a ToolResult.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def tier(self) -> PermissionTier:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given arguments."""
        pass
