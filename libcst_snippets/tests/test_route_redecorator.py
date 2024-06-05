from typing import Sequence

import libcst as cst
import libcst.matchers as m
import pytest
import os.path
from codemods.route_redecorator import (
    RouteRedecorateCommand,
    eligible_view_function_matcher,
    require_call_stmt_matcher,
    require_call_matcher,
    require_call_expr_matcher,
    view_with_permission_decorator_matcher,
    func_with_single_require_call_matcher,
    simple_view_function_matcher,
)
from libcst.codemod import CodemodTest


def project_file(filename):
    return os.path.join(os.path.dirname(__file__), "..", filename)


@pytest.fixture
def route_example_cst() -> cst.Module:
    with open(project_file("fixup_examples/route_example_before.py"), "r") as file:
        return cst.parse_module(file.read())


def test_finds_all_view_functions(route_example_cst: cst.Module):
    expected_view_names = {"menu", "buy", "item", "users"}
    found_view_func_defs = m.findall(route_example_cst, simple_view_function_matcher)
    found_view_names = {func.name.value for func in found_view_func_defs}
    assert found_view_names == expected_view_names


def get_views(tree) -> Sequence[cst.FunctionDef]:
    return m.findall(tree, eligible_view_function_matcher)


def get_require_stmts(view_funcdef) -> Sequence[cst.SimpleStatementLine]:
    return [
        stmt
        for stmt in view_funcdef.body.body
        if m.matches(stmt, require_call_stmt_matcher)
    ]


def test_find_view():
    code = """
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
    code = """
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


def test_match_view_with_permissioned_route():
    code = """
@app.route("/buy", methods=["GET", "POST"], permission=BUY_PERMISSION)
def buy():
    ...
"""
    tree = cst.parse_module(code)
    res = m.findall(tree, view_with_permission_decorator_matcher)
    assert len(res) == 1


def test_match_contains_single_require_call():
    code = """
@app.route("/buy", methods=["GET", "POST"])
def buy():
    g.user.require(BUY_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    res = m.findall(tree, func_with_single_require_call_matcher)
    assert len(res) == 1


def test_match_contains_single_require_call_no_match_multiples():
    code = """
@app.route("/buy", methods=["GET", "POST"])
def buy():
    g.user.require(BUY_PERMISSION)
    g.user.require(OTHER_PERMISSION)
    ...
"""
    tree = cst.parse_module(code)
    res = m.findall(tree, func_with_single_require_call_matcher)
    assert len(res) == 0


class TestRouteRedecorateCommand(CodemodTest):
    TRANSFORM = RouteRedecorateCommand

    def test_transform_noop(self):
        code = """

@admin.route("/users")
def users():
    ...
"""
        self.assertCodemod(code, code)

    def test_transform_on_simple_case(self):
        code = """
ADMIN_PERMISSION = "admin"

@admin.route("/users")
def users():
    g.user.require(ADMIN_PERMISSION)
    render_template("users.html")
"""
        expected = """
ADMIN_PERMISSION = "admin"

@admin.route("/users", permission=ADMIN_PERMISSION)
def users():
    render_template("users.html")
"""
        self.assertCodemod(code, expected)

    def test_transform_on_simple_case_string(self):
        code = """
@admin.route("/users")
def users():
    g.user.require("admin")
    render_template("users.html")
"""
        expected = """
@admin.route("/users", permission="admin")
def users():
    render_template("users.html")
"""
        self.assertCodemod(code, expected)

    def test_transform_ignores_conditional_require(self):
        code = """
@app.route("/items/<item_id>")
def item(item_id):
    item = get_item(item_id)
    if item.archived:
        g.user.require(ADMIN_PERMISSION)
    ...
"""
        self.assertCodemod(code, code)

    def test_transform_multiple_routes_on_view(self):
        code = """
@app.route("/buy", methods=["GET", "POST"], defaults={"offer": None})
@app.route("/offers/<offer>/buy", methods=["GET", "POST"], defaults={"offer": None})
def buy():
    g.user.require(BUY_PERMISSION)
    ...
"""
        expected = """
@app.route("/buy", methods=["GET", "POST"], defaults={"offer": None}, permission=BUY_PERMISSION)
@app.route("/offers/<offer>/buy", methods=["GET", "POST"], defaults={"offer": None}, permission=BUY_PERMISSION)
def buy():
    ...
"""
        self.assertCodemod(code, expected)

    def test_transform_ignores_routes_with_permission_already_set(self):
        code = """
@app.route("/buy", methods=["GET", "POST"], permission=BUY_PERMISSION)
def buy():
    g.user.require(ADDITIONAL_PERMISSION)
    ...
"""
        self.assertCodemod(code, code)

    def test_transform_whole_example(self):
        with open(project_file("fixup_examples/route_example_before.py"), "r") as file:
            before = file.read()
        with open(project_file("fixed_examples/route_example_after.py"), "r") as file:
            after = file.read()
        self.assertCodemod(before, after)
