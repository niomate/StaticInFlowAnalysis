import importlib.metadata as importlib_metadata
import ast


class Visitor(ast.NodeVisitor):

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.highs = set()
        self.lows = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.args.


class Plugin:

    name = __name__
    version = importlib_metadata.version(__name__)

    def __init__(self, tree: ast.AST):
        self._tree = tree
