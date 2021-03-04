import ast
from types import Variables


class VariableCollector(ast.NodeVisitor):

    def __init__(self):
        self.vars = set()
        self.free_only = False

    def visit_Call(self, node: ast.Call):
        for arg in node.args:
            self.visit(arg)

    def visit_Name(self, node: ast.Name):
        if not self.free_only or isinstance(node.ctx, ast.Load):
            self.vars.add(node.id)

    def collect(self, tree: ast.AST, free_only: bool = True):
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
