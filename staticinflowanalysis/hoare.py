# Core Library modules
import ast
import copy
from collections import defaultdict
from enum import Enum
from typing import Dict, Sequence, Optional

# Local modules
from .collector import collect_free_variables, collect_all_variables
from .typedefs import Indeps, Variables, Errors


class Confidentiality(Enum):
    High = "High"
    Low = "Low"
    NA = ""


def intersect(sets: Sequence[Variables]) -> Variables:
    ''' Compute intersection of the given sets '''
    if not sets:
        return set()
    combined: Variables = sets[0].copy()
    for s in sets:
        combined &= s
    return combined


def union(sets: Sequence[Variables]) -> Variables:
    ''' Compute union of the given sets '''
    if not sets:
        return set()
    combined: Variables = sets[0].copy()
    for s in sets:
        combined |= s
    return combined


def join(s1: Indeps, s2: Indeps) -> Indeps:
    ''' Join two independency sets by intersection '''
    return {x: s1[x] & s2[x] for x in s1}


class Hoare(ast.NodeVisitor):
    error_sa01 = "SFA01: {}: Information flow from low variable {} to high variable {}".format
    error_sa02 = "SFA02: {}: Information flow from high variable {} to low variable {}".format

    def __init__(self, varset: Variables) -> None:
        self.context: Variables = set()
        self.indeps: Indeps = {}
        self.all_vars: Variables = varset
        self.errors = []
        for var in varset:
            self.indeps[var] = {
                x
                for x in varset
                if x != var
            }

    def calc_indeps(self, free_vars_in_expr: Variables) -> Variables:
        ''' Calculate the set of independencies for the
        given set of variables. '''
        if not free_vars_in_expr:
            return self.all_vars

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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        ''' For each function detect if there is any flow from high to low or
        low to high variables. '''

        prios = [
            x.split(":")
            for x in node.type_comment.split(",")
        ]
        prios = {
            x.strip(): Confidentiality(y.strip())
            for x, y in prios
        }
        high = set()
        low = set()

        for x, y in prios.items():
            if x not in self.all_vars:
                continue
            if y == Confidentiality.High:
                high.add(x)
            elif y == Confidentiality.Low:
                low.add(x)

        self.generic_visit(node)

        for high_var in high:
            for low_var in low:
                if low_var not in self.indeps[high_var]:
                    # Information flow from low_var to high_var
                    self.errors += [self.error_sa01(node.name,
                                                    low_var, high_var)]
                if high_var not in self.indeps[low_var]:
                    # Information flow from high_var to low_var
                    self.errors += [self.error_sa02(node.name,
                                                    high_var, low_var)]

    def visit_While(self, node: ast.While) -> None:
        ''' Fixpoint iteration for Hoare logic '''
        free_vars: Variables = collect_free_variables(node.test)
        old_ctx: Variables = self.context.copy()

        while True:
            deps: Variables = self.calc_deps(free_vars)
            prev_indeps = copy.deepcopy(self.indeps)
            self.context |= deps

            for n in node.body:
                self.visit(n)

            self.indeps = join(self.indeps, prev_indeps)

            if self.indeps == prev_indeps:
                break

        self.context = old_ctx

    def visit_For(self, node: ast.For) -> None:
        ''' Fixpoint iteration for Hoare logic '''
        free_vars: Variables = collect_free_variables(node.test)
        free_vars: Variables = collect_free_variables(node.iter)
        old_ctx: Variables = self.context.copy()

        while True:
            deps: Variables = self.calc_deps(free_vars)
            prev_indeps = copy.deepcopy(self.indeps)
            self.context |= deps

            for n in node.body:
                self.visit(n)

            self.indeps = join(self.indeps, prev_indeps)

            if self.indeps == prev_indeps:
                break

        self.context = old_ctx

    def visit_Assign(self, node: ast.Assign) -> None:
        free_vars: Variables = collect_free_variables(node.value)
        indeps: Variables = self.calc_indeps(free_vars) - self.context
        var_node: ast.Name = node.targets[0]
        self.indeps[var_node.id] = indeps

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        old_ctx: Variables = self.context.copy()
        target: ast.Name = node.target
        self.context |= {target.id}
        free_vars: Variables = collect_free_variables(node.value)
        indeps: Variables = self.calc_indeps(free_vars) - self.context
        target: ast.Name = node.target
        self.indeps[target.id] = indeps
        self.context = old_ctx

    def visit_If(self, node: ast.If) -> None:
        old_ctx: Variables = self.context.copy()

        free_vars: Variables = collect_free_variables(node.test)

        deps: Variables = self.calc_deps(free_vars)
        self.context |= deps
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


def analyse(tree: ast.AST, var_set: Optional[Variables] = None) -> Errors:
    ''' Statically analyze the given tree using Hoare logic and return any
    errors found '''
    if not var_set:
        var_set = collect_all_variables(tree)
    hoare = Hoare(var_set)
    hoare.visit(tree)
    return hoare.errors
