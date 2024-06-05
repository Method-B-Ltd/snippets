from typing import Union, Optional, TypeVar

import libcst as cst
import libcst.matchers as m



T = TypeVar("T")
LeaveRet = Union[T, cst.RemovalSentinel]


def match_call_with_kwarg(keyword_name: str):
    """
    Matches a call with at least one keyword argument with the given name.
    :param keyword_name: The name of the kwarg to match
    :return: A matcher
    """
    return m.Call(
        args=[m.AtLeastN(n=0), m.AtLeastN(n=1, matcher=m.Arg(keyword=m.Name(value=keyword_name))), m.AtLeastN(n=0)]
    )


def match_method_call_named(method_name: str):
    """
    Matches a call of a method with the given name.
    :param method_name: The name of the method
    :return: A matcher
    """
    return m.Call(
        func=m.Attribute(
            attr=m.Name(value=method_name)
        )
    )


# A decorator like @x.route(...)
route_decorator_matcher = m.Decorator(
    decorator=match_method_call_named("route")
)


# A decorator like @x.route(..., permission=...)
route_with_permission_decorator_matcher = m.Decorator(
    decorator=match_method_call_named("route") & match_call_with_kwarg("permission"))


# Any function decorated at least once with @x.route
simple_view_function_matcher = (
    m.FunctionDef(decorators=
                  [m.AtLeastN(n=1, matcher=route_decorator_matcher)]))


# Any function decorated at least once with @x.route(..., permission=...)
view_with_permission_decorator_matcher = (
    m.FunctionDef(decorators=
                  [m.AtLeastN(n=1, matcher=route_with_permission_decorator_matcher)]))


# A call to g.user.require(...)
require_call_matcher = m.Call(
    func=m.Attribute(
        value=m.Attribute(
            value=m.Name(value="g"),
            attr=m.Name(value="user")
        ),
        attr=m.Name(value="require")
    )
)

# An expression that is a call to g.user.require(...)
require_call_expr_matcher = m.Expr(value=require_call_matcher)


# A statement that includes a call to g.user.require(...)
require_call_stmt_matcher = m.SimpleStatementLine(body=[m.AtLeastN(n=1, matcher=require_call_expr_matcher)])


# Function that contains a single require call (and possibly other statements)
body_with_single_require_call_matcher = m.IndentedBlock(body=[
    m.AtLeastN(n=0, matcher=~require_call_stmt_matcher),
    require_call_stmt_matcher,
    m.AtLeastN(n=0, matcher=~require_call_stmt_matcher)
])

func_with_single_require_call_matcher = m.FunctionDef(body=body_with_single_require_call_matcher)


# Any function decorated at least once with @x.route, but not with @x.route(...), containing a single require call
eligible_view_function_matcher = (simple_view_function_matcher
                                  & ~view_with_permission_decorator_matcher
                                  & func_with_single_require_call_matcher)


def build_kwarg_node(keyword: str, value: cst.BaseExpression):
    """
    Build a keyword argument node with the given keyword and value.
    :param keyword: Name of the kwarg
    :param value: Value of the kwarg (e.g. a Name, SimpleString etc.)
    :return: The Arg node
    """
    return cst.Arg(value=value,
                   keyword=cst.Name(keyword),
                   equal=cst.AssignEqual(
                       whitespace_before=cst.SimpleWhitespace(""),
                       whitespace_after=cst.SimpleWhitespace("")
                   ))


class RouteTransformer(cst.CSTTransformer):
    def __init__(self) -> None:
        super().__init__()
        self.inside_eligible_view_function = None
        self.permission: Optional[cst.BaseExpression] = None  # Likely a Name or SimpleString.

    def get_require_stmts(self, view_node: cst.FunctionDef):
        # Find all require call statements in the view function
        stmts = []
        for stmt in view_node.body.body:
            if m.matches(stmt, require_call_stmt_matcher):
                stmts.append(stmt)
        return stmts

    def extract_call_from_require_stmt(self, stmt: cst.SimpleStatementLine):
        # Extract the call from its statement
        assert isinstance(stmt, cst.SimpleStatementLine)
        assert isinstance(stmt.body[0], cst.Expr)
        call = stmt.body[0].value
        assert isinstance(call, cst.Call)
        return call

    def get_permission(self, view_node: cst.FunctionDef):
        # Get the permission from the require call in the view function
        require_stmts = self.get_require_stmts(view_node)
        n_require_stmts = len(require_stmts)
        if n_require_stmts != 1:
            raise ValueError("View functions must have exactly one require call")
        call: cst.Call = self.extract_call_from_require_stmt(require_stmts[0])
        permission = call.args[0].value
        return permission

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        if m.matches(node, eligible_view_function_matcher):
            if self.inside_eligible_view_function:
                raise ValueError("Nested view functions are not supported")
            self.inside_eligible_view_function = node
            self.permission = self.get_permission(node)
        return True

    def leave_FunctionDef(self,
                          original_node: cst.FunctionDef,
                          updated_node: cst.FunctionDef) -> LeaveRet[cst.FunctionDef]:
        if self.inside_eligible_view_function:
            self.inside_eligible_view_function = None
            self.permission = None
        return updated_node

    def leave_Decorator(self,
                        original_node: cst.Decorator,
                        updated_node: cst.Decorator) -> Union[cst.Decorator, cst.RemovalSentinel]:
        if self.inside_eligible_view_function:
            # If this is a route decorator, add the permission kwarg
            if m.matches(updated_node, route_decorator_matcher):
                inner: cst.Call = updated_node.decorator
                new_inner = inner.with_changes(args=list(inner.args) +
                                                    [build_kwarg_node("permission", self.permission)])
                return updated_node.with_changes(decorator=new_inner)

        return updated_node

    def leave_SimpleStatementLine(self,
                                  original_node: cst.SimpleStatementLine,
                                  updated_node: cst.SimpleStatementLine) -> LeaveRet[cst.SimpleStatementLine]:
        if self.inside_eligible_view_function:
            if m.matches(original_node, require_call_stmt_matcher):
                return cst.RemoveFromParent()
        return updated_node

