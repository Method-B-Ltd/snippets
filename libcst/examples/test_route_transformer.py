from typing import Sequence

import libcst as cst
import libcst.matchers as m
import pytest
import os.path
from .route_transformer import RouteTransformer, eligible_view_function_matcher, require_call_stmt_matcher, require_call_matcher, \
    require_call_expr_matcher, view_with_permission_decorator_matcher, func_with_single_require_call_matcher, \
    simple_view_function_matcher


def neighbouring_file(filename):
    return os.path.join(os.path.dirname(__file__), filename)


@pytest.fixture
def route_example_cst() -> cst.Module:
    with open(neighbouring_file("route_example_before.py"), "r") as file:
        return cst.parse_module(file.read())


def test_finds_all_view_functions(route_example_cst: cst.Module):
    expected_view_names = {"menu", "buy", "item", "users"}
    found_view_func_defs = m.findall(route_example_cst, simple_view_function_matcher)
    found_view_names = {func.name.value for func in found_view_func_defs}
    assert found_view_names == expected_view_names


def get_views(tree) -> Sequence[cst.FunctionDef]:
    return m.findall(tree, eligible_view_function_matcher)


def get_require_stmts(view_funcdef) -> Sequence[cst.SimpleStatementLine]:
    return [stmt for stmt in view_funcdef.body.body if m.matches(stmt, require_call_stmt_matcher)]


def test_find_view():
    code = \
"""
ADMIN_PERMISSION = "admin"

@admin.route("/users")
def users():
    g.user.require(ADMIN_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    views = get_views(tree)
    view = views[0]
    assert view.name.value == "users"



def test_match_require_call():
    code = "g.user.require(ADMIN_PERMISSION)"
    tree = cst.parse_expression(code)
    assert m.matches(tree, require_call_matcher)


def test_match_require_call_expr():
    code = "g.user.require(ADMIN_PERMISSION)"
    tree = cst.parse_statement(code)
    assert m.matches(tree.body[0], require_call_expr_matcher)


def test_match_require_call_stmt():
    code = "g.user.require(ADMIN_PERMISSION)"
    tree = cst.parse_statement(code)
    assert m.matches(tree, require_call_stmt_matcher)


def test_finds_require_stmt_in_view():
    code = \
"""
ADMIN_PERMISSION = "admin"

@admin.route("/users")
def users():
    g.user.require(ADMIN_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    view = get_views(tree)[0]
    require_stmts = get_require_stmts(view)
    assert len(require_stmts) == 1


def test_transform_noop():
    code = \
"""

@admin.route("/users")
def users():
    ...
"""
    tree = cst.parse_module(code)
    transformed_tree = tree.visit(RouteTransformer())
    assert transformed_tree.code == code


def test_transform_on_simple_case():
    code = \
"""
ADMIN_PERMISSION = "admin"

@admin.route("/users")
def users():
    g.user.require(ADMIN_PERMISSION)
    render_template("users.html")
"""
    expected = \
"""
ADMIN_PERMISSION = "admin"

@admin.route("/users", permission=ADMIN_PERMISSION)
def users():
    render_template("users.html")
"""
    tree = cst.parse_module(code)
    transformed_tree = tree.visit(RouteTransformer())
    assert transformed_tree.code == expected


def test_transform_on_simple_case_string():
    code = \
"""
@admin.route("/users")
def users():
    g.user.require("admin")
    render_template("users.html")
"""
    expected = \
"""
@admin.route("/users", permission="admin")
def users():
    render_template("users.html")
"""
    tree = cst.parse_module(code)
    transformed_tree = tree.visit(RouteTransformer())
    assert transformed_tree.code == expected


def test_transform_ignores_conditional_require():
    code = \
"""
@app.route("/items/<item_id>")
def item(item_id):
    item = get_item(item_id)
    if item.archived:
        g.user.require(ADMIN_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    transformed_tree = tree.visit(RouteTransformer())
    assert transformed_tree.code == code


def test_transform_multiple_routes_on_view():
    code = \
"""
@app.route("/buy", methods=["GET", "POST"], defaults={"offer": None})
@app.route("/offers/<offer>/buy", methods=["GET", "POST"], defaults={"offer": None})
def buy():
    g.user.require(BUY_PERMISSION)
    ...
"""
    expected = \
"""
@app.route("/buy", methods=["GET", "POST"], defaults={"offer": None}, permission=BUY_PERMISSION)
@app.route("/offers/<offer>/buy", methods=["GET", "POST"], defaults={"offer": None}, permission=BUY_PERMISSION)
def buy():
    ...
"""
    tree = cst.parse_module(code)
    transformed_tree = tree.visit(RouteTransformer())
    assert transformed_tree.code == expected


def test_match_view_with_permissioned_route():
    code = \
"""
@app.route("/buy", methods=["GET", "POST"], permission=BUY_PERMISSION)
def buy():
    ...
"""
    tree = cst.parse_module(code)
    res = m.findall(tree, view_with_permission_decorator_matcher)
    assert len(res) == 1


def test_match_contains_single_require_call():
    code = \
"""
@app.route("/buy", methods=["GET", "POST"])
def buy():
    g.user.require(BUY_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    res = m.findall(tree, func_with_single_require_call_matcher)
    assert len(res) == 1


def test_match_contains_single_require_call_no_match_multiples():
    code = \
"""
@app.route("/buy", methods=["GET", "POST"])
def buy():
    g.user.require(BUY_PERMISSION)
    g.user.require(OTHER_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    res = m.findall(tree, func_with_single_require_call_matcher)
    assert len(res) == 0


def test_transform_ignores_routes_with_permission_already_set():
    code = \
"""
@app.route("/buy", methods=["GET", "POST"], permission=BUY_PERMISSION)
def buy():
    g.user.require(ADDITIONAL_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    transformed_tree = tree.visit(RouteTransformer())
    assert transformed_tree.code == code


def test_transform_whole_example(route_example_cst: cst.Module):
    transformed_tree = route_example_cst.visit(RouteTransformer())
    with open(neighbouring_file("route_example_after.py"), "r") as file:
        expected_code = file.read()
    assert transformed_tree.code == expected_code