import libcst as cst
import libcst.matchers as m
from libcst.codemod import VisitorBasedCodemodCommand, CodemodContext
from libcst.codemod.visitors import AddImportsVisitor

from .sa_common import class_probably_an_sa_model


column_def_matcher = m.Assign(
    targets=[m.AssignTarget(target=m.Name())],
    value=m.Call(
        func=m.Name(value="Column"),
    ),
)


def match_pos_arg(**kwargs):
    return m.Arg(**kwargs, keyword=~m.Name())


def match_kwarg(**kwargs):
    return m.Arg(**kwargs, keyword=m.Name())


column_call_with_name_and_type = m.Call(
    func=m.Name(value="Column"),
    args=[
        match_pos_arg(value=m.Name() | m.SimpleString()),
        match_pos_arg(value=m.Name()),
        m.AtLeastN(n=0, matcher=match_kwarg()),
    ],
)


column_call_with_type = m.Call(
    func=m.Name(value="Column"),
    args=[
        match_pos_arg(value=m.Name() | m.Call()),
        m.AtLeastN(n=0, matcher=match_kwarg()),
    ],
)


empty_call_matcher = m.Call(args=[m.AtMostN(n=0)])

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

unambiguously_inferable_sa_types = set(sa_type_to_py_type.keys()) - {"String", "Text"}

name_of_inferrable_type_matcher = m.OneOf(*[m.Name(value=sa_type) for sa_type in unambiguously_inferable_sa_types])
name_or_empty_call_of_inferrable_type_matcher = (name_of_inferrable_type_matcher |
                                                 m.Call(args=[m.AtMostN(n=0)], func=name_of_inferrable_type_matcher))


# If not retained_type_in_mapped_column, pop the type from the call
# If there are no arguments left, use an assignment like this instead: name: Mapped[Optional[str]]
# If there are arguments left, modify the assigment to add a type hint on the LHS and the RHS to be a mapped_column call


call_has_no_kwarg_nullable = m.Call(
    args=[m.AtLeastN(n=0, matcher=~m.Arg(keyword=m.Name(value="nullable")))],
)

call_has_nullable_true = m.Call(
    args=[
        m.AtLeastN(n=0),
        m.Arg(keyword=m.Name(value="nullable"), value=m.Name(value="True")),
        m.AtLeastN(n=0)
    ]
)
call_has_nullable_false = m.Call(
    args=[
        m.AtLeastN(n=0),
        m.Arg(keyword=m.Name(value="nullable"), value=m.Name(value="False")),
        m.AtLeastN(n=0)
    ]
)
call_has_primary_key_true = m.Call(
    args=[
        m.AtLeastN(n=0),
        m.Arg(keyword=m.Name(value="primary_key"), value=m.Name(value="True")),
        m.AtLeastN(n=0)
    ]
)


def build_param_type(outer, inner):
    return cst.Subscript(
        value=outer,
        slice=[
            cst.SubscriptElement(
                slice=cst.Index(
                    value=inner
                )
            )
        ]
    )


def must_retain_type_arg(column_type_arg: cst.Arg):
    if column_type_arg is None:
        return False
    if m.matches(column_type_arg.value, name_or_empty_call_of_inferrable_type_matcher):
        return False
    return True


def attempt_to_build_annotation(py_type, is_optional):
    if py_type:
        annotation_type = cst.parse_expression(py_type)
        if is_optional:
            annotation_type = build_param_type(cst.Name(value="Optional"), annotation_type)
        mapped_annotation_type = build_param_type(cst.Name(value="Mapped"), annotation_type)
        return cst.Annotation(annotation=mapped_annotation_type)
    else:
        return


def replacement_assignment(node: cst.Assign):
    col_call: cst.Call = node.value

    explicit_column_name_arg, column_type_arg, other_args = process_column_call(col_call)

    new_args = []
    if explicit_column_name_arg:
        new_args.append(explicit_column_name_arg)

    if must_retain_type_arg(column_type_arg):
        new_args.append(column_type_arg)

    new_args.extend(other_args)

    py_type, is_optional = resolve_py_type_and_is_optional(col_call, column_type_arg)

    annotation = attempt_to_build_annotation(py_type, is_optional)

    if annotation:
        # Remove nullable arg
        new_args = [arg for arg in new_args if not m.matches(arg, m.Arg(keyword=m.Name(value="nullable")))]

    if len(new_args) > 0:
        new_args[-1] = new_args[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT
        )
    new_call = cst.Call(
        func=cst.Name(value="mapped_column"),
        args=new_args,
    )
    if annotation:
        new_assign = cst.AnnAssign(
            target=node.targets[0].target,
            annotation=annotation,
            value=new_call
        )
    else:
        new_assign = node.with_changes(
            value=new_call
        )
    return new_assign, py_type


class ColumnToMappedCommand(VisitorBasedCodemodCommand):
    def __init__(self, context: "CodemodContext"):
        super().__init__(context)
        self.in_model = False
        self.in_column_assignment = None

    def visit_ClassDef(self, node: cst.ClassDef):
        if m.matches(node, class_probably_an_sa_model):
            self.in_model = True
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.in_model = False
        return updated_node

    def visit_Assign(self, node: cst.Assign):
        if self.in_model:
            if m.matches(node, column_def_matcher):
                self.in_column_assignment = node
                col_call: cst.Call = node.value
                if m.matches(col_call, column_call_with_name_and_type):
                    self.explicit_column_name_arg = col_call.args[0]
                    self.column_type_arg = col_call.args[1]
                elif m.matches(col_call, column_call_with_type):
                    self.explicit_column_name_arg = None
                    self.column_type_arg = col_call.args[0]
                else:
                    raise ValueError(f"Don't understand column definition {node}")
        return True

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign:
        if self.in_column_assignment and self.in_column_assignment == original_node:
            self.in_column_assignment = None
            replacement, py_type = replacement_assignment(updated_node)
            if py_type and "." in py_type:
                # This is not a good way to handle this.
                # If we have something like Mapped[datetime.datetime], we'll add an import datetime
                mod_name, type_name = py_type.rsplit(".", 1)
                AddImportsVisitor.add_needed_import(self.context, mod_name)
            return replacement
        return updated_node


def resolve_py_type_and_is_optional(col_call: cst.Call, column_type_arg: cst.Arg):
    if m.matches(column_type_arg.value, m.Name()):
        assert isinstance(column_type_arg.value, cst.Name)
        column_type_name = column_type_arg.value.value
    else:
        assert isinstance(column_type_arg.value, cst.Call)
        func = column_type_arg.value.func
        assert isinstance(func, cst.Name)
        column_type_name = func.value
    py_type = sa_type_to_py_type.get(column_type_name)

    if not py_type:
        # Can't determine the type
        return None, None

    if m.matches(col_call, call_has_no_kwarg_nullable) & m.matches(col_call, call_has_primary_key_true):
        is_optional = False
    elif m.matches(col_call, call_has_no_kwarg_nullable):
        is_optional = True
    elif m.matches(col_call, call_has_nullable_true):
        is_optional = True
    elif m.matches(col_call, call_has_nullable_false):
        is_optional = False
    else:
        # Can't determine if it's optional or not
        is_optional = None
        py_type = None
    return py_type, is_optional


def process_column_call(col_call: cst.Call):
    if m.matches(col_call, column_call_with_name_and_type):
        explicit_column_name_arg = col_call.args[0]
        column_type_arg = col_call.args[1]
        other_args = col_call.args[2:]
    elif m.matches(col_call, column_call_with_type):
        explicit_column_name_arg = None
        column_type_arg = col_call.args[0]
        other_args = col_call.args[1:]
    else:
        raise ValueError(f"Don't understand column definition {col_call}")
    return explicit_column_name_arg, column_type_arg, other_args


