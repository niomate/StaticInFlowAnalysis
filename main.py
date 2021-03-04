import ast
import inspect
import astpretty
from collections import defaultdict
from typing import TypeVar, Generic, Set, Dict, Any

T = TypeVar('T')


class High(Generic[T]):
    pass


class Low(Generic[T]):
    pass


def foo(l: Set[Any], h: High[Any], h2: High, h3: High[Any], l1: Low[Any]):
    l = h
    return l


class Visitor(ast.NodeVisitor):

    def __init__(self) -> None:
        self.highs: Set[str] = set()
        self.lows: Set[str] = set()

    def visit_FunctionDef(self, node: ast.AST):
        types = self.get_type_annotations(node)
        self.highs = self.highs.union(types['High'])
        self.lows = self.lows.union(types['Low'])
        if len(self.highs) > 0 and len(self.lows) > 0:
            # Perform static analysis
            pass
        self.generic_visit(node)

    def get_type_annotations(self, node: ast.AST) -> Dict[str, str]:
        assert isinstance(
            node, ast.FunctionDef), "Node is not a function definition"

        type_annotations = defaultdict(set)

        for arg in node.args.args:
            if isinstance(arg.annotation, ast.Subscript):
                type_annotations[arg.annotation.value.id].add(arg.arg)

        return type_annotations

    def check_types(self, tree: ast.AST):
        self.__init__()
        self.visit(tree)
        return self.highs, self.lows
