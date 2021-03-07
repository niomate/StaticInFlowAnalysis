# Core Library modules
import ast
import copy
from typing import List, Optional, Sequence, Callable, Tuple

# Local modules
from .collector import (
    collect_all_variables,
    collect_free_variables,
    extract_flow_config,
)
from .typedefs import Confidentiality, Errors, FlowConfig, Indeps, Variables

ErrorCode = Callable[[str, str, str], str]


def intersect(sets: Sequence[Variables]) -> Variables:
    """ Compute intersection of the given sets """
    if not sets:
        return set()
    combined: Variables = sets[0].copy()
    for s in sets:
        combined &= s
    return combined


def union(sets: Sequence[Variables]) -> Variables:
    """ Compute union of the given sets """
    if not sets:
        return set()
    combined: Variables = sets[0].copy()
    for s in sets:
        combined |= s
    return combined


def join(s1: Indeps, s2: Indeps) -> Indeps:
    """ Join two independency sets by intersection """
    return {x: s1[x] & s2[x] for x in s1}


class Hoare(ast.NodeVisitor):
    STA100: ErrorCode = (
        "STA100 Information flow from high variable '{high}' to "
        "low variable '{low}' in function '{func}'".format
    )
    STA101: ErrorCode = (
        "STA101 Information flow from low variable '{low}' to "
        "high variable '{high}' in function '{func}'".format
    )
    STA200: ErrorCode = (
        "STA200 Information flow from local high variable '{high}' to "
        "low variable '{low}' in function '{func}'".format
    )
    STA201: ErrorCode = (
        "STA201 Information flow from local low variable '{low}' to "
        "high variable '{high}' in function '{func}'".format
    )
    STA300: ErrorCode = (
        "STA300 Information flow from high variable '{high}' to "
        "local low variable '{low}' in function '{func}'".format
    )
    STA301: ErrorCode = (
        "STA301 Information flow from low variable '{low}' to "
        "local high variable '{high}' in function '{func}'".format
    )

    # TODO: Make varset optional and extract it on the go on every function
    # definition node
    def __init__(self, lines: Sequence[str], varset: Variables) -> None:
        # Context for Hoare logic
        self.context: Variables = set()
        # Independency sets for Hoare Logic
        self.indeps: Indeps = {}
        # Set of all variables that we want to consider for the analysis
        self.all_vars: Variables = varset
        # Errors we found (for flake8).
        # TODO: Might have to be extracted to a different module since this is
        # not really Hoare logic related
        self.errors: Errors = []

        # High and low variables. Extracted during the analysis
        self.high: Variables = set()
        self.low: Variables = set()
        self.locals: Variables = set()

        # Parameters
        # Code lines
        self.lines: Sequence[str] = lines

        # Initialize independency sets
        for var in varset:
            self.indeps[var] = {x for x in varset if x != var}

    def calc_indeps(self, free_vars_in_expr: Variables) -> Variables:
        """Calculate the set of independencies for the
        given set of variables."""
        if not free_vars_in_expr:
            return self.all_vars

        indeps: Variables = intersect([self.indeps[x] for x in free_vars_in_expr])
        return indeps

    def calc_deps(self, free_vars_in_expr: Variables) -> Variables:
        """Calculate the set of dependencies for the
        given set of variables."""
        return union([self.all_vars - self.indeps[var] for var in free_vars_in_expr])

    def add_var(self, var: str, confidentiality: Confidentiality) -> None:
        if confidentiality == Confidentiality.High:
            self.high.add(var)
        elif confidentiality == Confidentiality.Low:
            self.low.add(var)

    def add_error(
        self, line: int, col: int, tp: ErrorCode, low: str, high: str, func: str
    ) -> None:
        self.errors += [(line, col, tp(low=low, high=high, func=func))]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """For each function detect if there is any flow from high to low or
        low to high variables."""
        flow_conf = extract_flow_config(self.lines[node.lineno - 1])
        var_names: List[str] = [arg.arg for arg in node.args.args]

        old_high = self.high.copy()
        old_low = self.low.copy()
        old_locals = self.locals.copy()

        self.high = set()
        self.low = set()
        self.locals = set()

        for x, y in zip(var_names, flow_conf):
            self.add_var(x, y)

        self.generic_visit(node)

        for high_var in self.high:
            for low_var in self.low:
                error_type: ErrorCode
                if low_var not in self.indeps[high_var]:
                    # Information flow from low_var to high_var
                    if low_var in self.locals:
                        error_type = self.STA201
                    elif high_var in self.locals:
                        error_type = self.STA301
                    else:
                        error_type = self.STA101
                if high_var not in self.indeps[low_var]:
                    # Information flow from high_var to low_var
                    if high_var in self.locals:
                        error_type = self.STA200
                    elif low_var in self.locals:
                        error_type = self.STA300
                    else:
                        error_type = self.STA100

                self.add_error(
                    line=node.lineno,
                    col=node.col_offset,
                    tp=error_type,
                    low=low_var,
                    high=high_var,
                    func=node.name,
                )

        self.high = old_high
        self.low = old_low
        self.locals = old_locals

    def visit_While(self, node: ast.While) -> None:
        """ Fixpoint iteration for Hoare logic """
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
        """ Fixpoint iteration for Hoare logic """
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
        extracted = extract_flow_config(self.lines[node.lineno - 1])
        var_node: ast.Name = node.targets[0]
        if extracted:
            # If there was a flow configuration for this assignment, we assume
            # that it was an initial assignment and thus do not analyse it at
            # this point in time.
            self.add_var(var_node.id, extracted[0])
            self.locals.add(var_node.id)
            return
        free_vars: Variables = collect_free_variables(node.value)
        indeps: Variables = self.calc_indeps(free_vars) - self.context
        self.indeps[var_node.id] = indeps

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        old_ctx: Variables = self.context.copy()
        target: ast.Name = node.target
        self.context |= {target.id}
        free_vars: Variables = collect_free_variables(node.value)
        indeps: Variables = self.calc_indeps(free_vars) - self.context
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

        if hasattr(node, "orelse"):
            self.context = intermediate_ctx

            for n in node.body:
                self.visit(n)

            else_indeps: Indeps = copy.deepcopy(self.indeps)

            self.indeps = join(if_indeps, else_indeps)

        self.context = old_ctx


def analyse(
    tree: ast.AST, flow_conf: FlowConfig, var_set: Optional[Variables] = None
) -> Errors:
    """Statically analyze the given tree using Hoare logic and return any
    errors found"""
    if not var_set:
        var_set = collect_all_variables(tree)
    hoare = Hoare(flow_conf, var_set)
    hoare.visit(tree)
    return hoare.errors
