# Core Library modules
import ast
import copy
from collections import defaultdict
from enum import Enum
from typing import Dict, Sequence

# Local modules
from .collector import collect_free_variables
from .typedefs import Indeps, Variables


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
    # TODO: Check if this is the correct implementation of the join
    return {x: s1[x] & s2[x] for x in s1}


class Hoare(ast.NodeVisitor):

    def __init__(self, varset: Variables) -> None:
        self.context: Variables = set()
        self.indeps: Indeps = {}
        self.all_vars: Variables = varset
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
        prios = [x.split(":") for x in node.type_comment.split(",")]
        prios = {x.strip(): Confidentiality(y.strip()) for x, y in prios}
        high = {x for x, y in prios.items() if y == Confidentiality.High}
        low = {x for x, y in prios.items() if y == Confidentiality.Low}

        self.generic_visit(node)

        high &= self.indeps.keys()
        low &= self.indeps.keys()
        flow = defaultdict(set)
        errors = []
        for h in high:
            for l in low:
                if l not in self.indeps[h]:
                    # Information flow from l to h
                    flow[l].add(h)
                    errors += [
                        f"SFA01: {node.name}: Information flow from low variable {l} to high variable {h}"]
                if h not in self.indeps[l]:
                    flow[h].add(l)
                    errors += [
                        f"SFA02: {node.name}: Information flow from high variable {h} to low variable {l}"]

        print("\n".join(errors))

    def visit_While(self, node: ast.While) -> None:
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

    def print_independencies(self):
        for var, indeps in self.indeps.items():
            print(var + "#" + ",".join(iter(indeps)))

    def detect_flow(self, tree: ast.AST, high: Variables, low: Variables) -> Dict[str, str]:
        self.visit(tree)
        high &= self.indeps.keys()
        low &= self.indeps.keys()
        flow = defaultdict(set)
        for h in high:
            for l in low:
                if l not in self.indeps[h]:
                    flow[h].add(l)
                if h not in self.indeps[l]:
                    flow[l].add(h)

        return flow
