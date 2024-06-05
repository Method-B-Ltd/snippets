import libcst as cst
import libcst.matchers as m

from codemods.sa_column_to_mapped import column_def_matcher, name_or_empty_call_of_inferrable_type_matcher, ColumnToMappedCommand, process_column_call, resolve_py_type_and_is_optional, replacement_assignment
from libcst.codemod import CodemodTest

before = """
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    fullname = Column(String)
    nickname = Column(String(30))
    data = Column(JSONB)
    created_at = Column(DateTime, nullable=False)
"""


after = """
import datetime

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    fullname: Mapped[Optional[str]] = mapped_column(String)
    nickname: Mapped[Optional[str]] = mapped_column(String(30))
    data = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column()

"""

sa_type_to_py_type = {
    "Integer": "int",
    "String": "str",
    "Text": "str",
    "Date": "datetime.date",
    "DateTime": "datetime.datetime",
    "Boolean": "bool",
    "Numeric": "decimal.Decimal",
    "Float": "float",
}

# Find column type (Name or Call), resolve the type Name
# If the call has arguments, retain_type_in_mapped_column = True
# If the type is Text or String, retain_type_in_mapped_column = False
# If the type isn't in the sa_type_to_py_type map, retain_type_in_mapped_column = True
# Look for nullable kwarg, if found set is_optional = nullable
# Look for primary_key kwarg, if found and True set is_optional = False
# Ignore Columns with ForeignKey



def test_find_column_assignment():
    tree = cst.parse_module(before)
    found = m.findall(tree, column_def_matcher)
    assert len(found) == 6

def test_name_or_empty_call_of_inferrable_type_matcher():
    challenges = [
        ("Integer", True),
        ("Integer()", True),
        ("JSONB", False),
        ("Text", False),
        ("Numeric", True),
        ("Numeric(4,2)", False)
    ]
    for challenge, expected in challenges:
        node = cst.parse_expression(challenge)
        assert m.matches(node, name_or_empty_call_of_inferrable_type_matcher) == expected, \
            f"Challenge: {challenge} failed, expected {expected}"


def test_process_column_call_type_only():
    node = cst.parse_expression("Column(Integer, primary_key=True)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    assert explicit_column_name_arg is None
    assert column_type_arg.value.value == "Integer"
    assert len(other_args) == 1


def test_process_column_call_name_and_type():
    node = cst.parse_expression("Column(\"id\", Integer, primary_key=True)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    assert explicit_column_name_arg.value.value == '"id"'
    assert column_type_arg.value.value == "Integer"
    assert len(other_args) == 1


def test_resolve_py_type_and_is_optional_for_int_pk():
    node = cst.parse_expression("Column(Integer, primary_key=True)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    py_type, is_optional = resolve_py_type_and_is_optional(node, column_type_arg)
    assert py_type == "int"
    assert not is_optional


def test_resolve_py_type_and_is_optional_for_int():
    node = cst.parse_expression("Column(Integer)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    py_type, is_optional = resolve_py_type_and_is_optional(node, column_type_arg)
    assert py_type == "int"
    assert is_optional

def test_resolve_py_type_and_is_optional_for_int_nullable():
    node = cst.parse_expression("Column(Integer, nullable=True)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    py_type, is_optional = resolve_py_type_and_is_optional(node, column_type_arg)
    assert py_type == "int"
    assert is_optional

def test_resolve_py_type_and_is_optional_for_int_nonnullable():
    node = cst.parse_expression("Column(Integer, nullable=False)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    py_type, is_optional = resolve_py_type_and_is_optional(node, column_type_arg)
    assert py_type == "int"
    assert not is_optional


def test_resolve_py_type_and_is_optional_for_int_dynamic():
    node = cst.parse_expression("Column(Integer, nullable=dynamic)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    py_type, is_optional = resolve_py_type_and_is_optional(node, column_type_arg)
    # Can't determine if it's optional or not, so we can't type it.
    assert py_type is None
    assert is_optional is None


def test_resolve_py_type_and_is_optional_for_some_custom_type():
    node = cst.parse_expression("Column(Bucket)")
    explicit_column_name_arg, column_type_arg, other_args = process_column_call(node)
    py_type, is_optional = resolve_py_type_and_is_optional(node, column_type_arg)
    assert py_type is None
    assert is_optional is None


def test_replacement_assignment():
    challenges = [
        ("id = Column(Integer, primary_key=True)", "id: Mapped[int] = mapped_column(primary_key=True)"),
        ("name = Column(String(50), nullable=False)", "name: Mapped[str] = mapped_column(String(50))"),
        ("fullname = Column(String)", "fullname: Mapped[Optional[str]] = mapped_column(String)"),
        ("nickname = Column(String(30))", "nickname: Mapped[Optional[str]] = mapped_column(String(30))"),
        ("data = Column(JSONB)", "data = mapped_column(JSONB)"),
        ("data = Column(JSONB, nullable=True)", "data = mapped_column(JSONB, nullable=True)"),
        ("cost = Column(Numeric(4,2), nullable=False)", "cost: Mapped[decimal.Decimal] = mapped_column(Numeric(4,2))"),
    ]
    for before, after in challenges:
        node = cst.parse_statement(before).body[0]
        replacement, py_type = replacement_assignment(node)
        new_stmt = cst.SimpleStatementLine(body=[replacement])
        new_module = cst.Module(body=[new_stmt])
        assert new_module.code.strip() == after


class TestColumnToMappedCommand(CodemodTest):
    TRANSFORM = ColumnToMappedCommand

    def test_mixed_example(self):
        self.assertCodemod(before, after)
