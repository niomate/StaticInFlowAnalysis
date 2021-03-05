# Core Library modules
import ast

# Local modules
from .typedefs import Variables


class VariableCollector(ast.NodeVisitor):

    def __init__(self) -> None:
        self.vars: Variables = set()
        self.free_only: bool = False

    def visit_Call(self, node: ast.Call) -> None:
        for arg in node.args:
            self.visit(arg)

    def visit_Name(self, node: ast.Name) -> None:
        if not self.free_only or isinstance(node.ctx, ast.Load):
            self.vars.add(node.id)

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        for n in node.body + node.orelse:
            self.visit(n)

    def collect(self, tree: ast.AST, free_only: bool = True) -> Variables:
        self.vars = set()
        self.free_only = free_only
        self.visit(tree)
        return self.vars


def collect_free_variables(tree: ast.AST) -> Variables:
    c = VariableCollector()
    return c.collect(tree)


def collect_all_variables(tree: ast.AST) -> Variables:
    c = VariableCollector()
    return c.collect(tree, free_only=False)
