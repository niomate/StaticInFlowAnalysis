import ast
import copy
from typing import Sequence
from .types import Variables, Indeps
from .collector import collect_free_variables


def intersect(sets: Sequence[Variables]) -> Variables:
    ''' Compute intersection of the given sets '''
    if not sets:
        return Variables()
    combined: Variables = sets[0].copy()
    for s in sets:
        combined.intersection_update(s)
    return combined


def union(sets: Sequence[Variables]) -> Variables:
    ''' Compute union of the given sets '''
    if not sets:
        return Variables()
    combined: Variables = sets[0].copy()
    for s in sets:
        combined.update(s)
    return combined


def join(s1: Indeps, s2: Indeps) -> Indeps:
    ''' Join two independency sets by intersection '''
    # TODO: Check if this is the correct implementation of the join
    return {x: s1[x] & s2[x] for x in s1}


class Hoare(ast.NodeVisitor):

    def __init__(self, varset: Variables) -> None:
        self.context: Variables = Variables()
        self.indeps: Indeps = Indeps()
        self.all_vars: Variables = varset
        for var in varset:
            self.indeps[var] = {x for x in varset if x != var}

    def visit_While(self, node: ast.While) -> None:
        free_vars: Variables = collect_free_variables(node.test)
        old_ctx: Variables = self.context.copy()
        deps: Variables = self.calc_deps(free_vars)

        # TODO: Fixpoint iteration
        self.context.update(deps)
        for n in node.body:
            self.visit(n)
        self.context = old_ctx

    def calc_indeps(self, free_vars_in_expr: Variables) -> Variables:
        ''' Calculate the set of independencies for the
        given set of variables. '''
        if not free_vars_in_expr:
            return self.all_vars
        else:
            indeps: Variables = intersect([
                self.indeps[x]
                for x in free_vars_in_expr
            ])
            return indeps

    def calc_deps(self, free_vars_in_expr: Variables) -> Variables:
        ''' Calculate the set of dependencies for the
        given set of variables. '''
        return union([
            self.all_vars - self.indeps[var]
            for var in free_vars_in_expr
        ])

    def visit_Assign(self, node: ast.Assign) -> None:
        free_vars: Variables = collect_free_variables(node.value)
        indeps: Variables = self.calc_indeps(free_vars) - self.context
        target: str = node.targets[0].id
        self.indeps[target] = indeps

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        old_ctx: Variables = self.context.copy()
        self.context.update(node.target.id)
        free_vars: Variables = collect_free_variables(node.value)
        indeps: Variables = self.calc_indeps(free_vars) - self.context
        self.indeps[node.target.id] = indeps
        self.context = old_ctx

    def visit_If(self, node: ast.If) -> None:
        old_ctx: Variables = self.context.copy()

        free_vars: Variables = collect_free_variables(node.test)

        deps: Variables = self.calc_deps(free_vars)
        self.context.update(deps)
        intermediate_ctx: Variables = self.context.copy()

        for n in node.body:
            self.visit(n)

        if_indeps: Indeps = copy.deepcopy(self.indeps)

        if hasattr(node, 'orelse'):
            self.context = intermediate_ctx

            for n in node.body:
                self.visit(n)

            else_indeps: Indeps = copy.deepcopy(self.indeps)

            self.indeps = join(if_indeps, else_indeps)

        self.context = old_ctx
