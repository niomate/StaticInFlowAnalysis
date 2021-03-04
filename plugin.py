import importlib.metadata as importlib_metadata
import ast


class Plugin:

    name = __name__
    version = importlib_metadata.version(__name__)

    def __init__(self, tree: ast.AST):
        self._tree = tree
