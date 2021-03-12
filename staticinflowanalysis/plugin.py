# Core Library modules
import ast
from typing import Any, Generator, Tuple, Type, Sequence

# First party modules
from staticinflowanalysis.hoare import analyse


class Plugin:

    name = 'staticinflowanalysis'
    version = '0.1.0'

    def __init__(self, tree: ast.AST, lines: Sequence[str]):
        self._tree = tree
        self._lines = lines

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        errors = analyse(self._tree, self._lines)

        for line, col, msg in errors:
            yield line, col, msg, type(self)
