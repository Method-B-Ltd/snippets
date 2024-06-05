import argparse
from typing import Sequence

import libcst as cst
import libcst.matchers as m
from libcst.codemod import VisitorBasedCodemodCommand, CodemodContext
from libcst.codemod.visitors import AddImportsVisitor

from .sa_common import class_probably_an_sa_model

before = """
from sqlalchemy import Column, Integer, Boolean
from .base import Base

class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    ...

    @classmethod
    def get_active(cls, session):
        return session.query(cls).filter(cls.archived.is_(False)).all()
    
    @classmethod
    def get_archived(cls, session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
"""


after = """
from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.orm import Session
from .base import Base


class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    ...

    @classmethod
    def get_active(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(False)).all()

    @classmethod
    def get_archived(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
"""

# Tips:
# - Where matchers are in a list, you'll need to use something like AtLeastN or AtMostN to match the correct number of items.
# - Use m.AtLeastN(n=0) as a wildcard where necessary
# - Often, you'll want to sandwich a matcher between two AtLeastN(n=0) matchers to match any number of items before and after the matcher


classmethod_decorator_matcher = m.Decorator(decorator=m.Name(value="classmethod"))


def build_classmethod_with_session_arg_matcher(
    possible_session_names: Sequence[str] = ("session",)
) -> m.FunctionDef:
    session_param = m.OneOf(
        *(m.Param(name=m.Name(value=name)) for name in possible_session_names)
    )
    return m.FunctionDef(
        decorators=[
            m.AtLeastN(n=0),
            m.AtLeastN(n=1, matcher=classmethod_decorator_matcher),
            m.AtLeastN(n=0),
        ],
        params=m.Parameters(
            params=[
                m.Param(),  # We could choose to be stricter: m.Param(name=m.Name(value="cls"))
                session_param,
                m.AtLeastN(n=0),
            ]
        ),
    )


class AddSessionTypeAnnotationCommand(VisitorBasedCodemodCommand):
    DESCRIPTION = (
        "Annotate session parameter of classmethods that appear to be part of an SQLAlchemy model "
        "(have column definitions or a __tablename__)."
    )

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        arg_parser.add_argument(
            "--session-type-name",
            default="Session",
            help="The name of the session type to annotate with.",
        )
        arg_parser.add_argument(
            "--import-session-from",
            default="sqlalchemy.orm",
            help="The module to import the session type from.",
        )
        arg_parser.add_argument(
            "--possible-session-names",
            nargs="+",
            default=["session"],
            help="The names of the session parameter to annotate.",
        )

    def __init__(
        self,
        context: CodemodContext,
        session_type_name: str = "Session",
        import_session_from: str = "sqlalchemy.orm",
        possible_session_names: Sequence[str] = ("session",),
    ) -> None:
        super().__init__(context)
        self.in_model = False
        self.in_classmethod = False
        self.session_type_name = session_type_name
        self.import_session_from = import_session_from
        self.possible_session_names = possible_session_names
        self.classmethod_matcher = build_classmethod_with_session_arg_matcher(
            self.possible_session_names
        )

    def visit_ClassDef(self, node: cst.ClassDef):
        if m.matches(node, class_probably_an_sa_model):
            self.in_model = True
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.in_model = False
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef):
        if self.in_model and m.matches(node, self.classmethod_matcher):
            self.in_classmethod = True
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        self.in_classmethod = False
        return updated_node

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        if (
            self.in_classmethod
            and updated_node.name.value in self.possible_session_names
            and not updated_node.annotation
        ):
            AddImportsVisitor.add_needed_import(
                self.context, self.import_session_from, self.session_type_name
            )
            return updated_node.with_changes(
                annotation=cst.Annotation(
                    annotation=cst.Name(value=self.session_type_name)
                )
            )
        return updated_node
