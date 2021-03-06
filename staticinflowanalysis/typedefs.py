# Core Library modules
from typing import Dict, Set, List, Tuple
from enum import Enum


class Confidentiality(Enum):
    High = "High"
    Low = "Low"
    NA = "None"


Variables = Set[str]
Indeps = Dict[str, Set[str]]
Errors = List[Tuple[int, int, str]]
FlowConfig = Dict[str, List[Confidentiality]]
