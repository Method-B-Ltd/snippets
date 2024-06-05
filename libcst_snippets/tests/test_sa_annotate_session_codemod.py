import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodTest

from codemods.sa_annotate_session_codemod import (
    class_has_tablename_attribute_matcher,
    column_definition_line_matcher,
    class_has_column_definitions_matcher,
    AddSessionTypeAnnotationCommand,
    build_classmethod_with_session_arg_matcher,
)


def test_class_has_tablename_attribute_found():
    code = """
class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    ...
"""
    tree = cst.parse_module(code)
    found = m.findall(tree, class_has_tablename_attribute_matcher)
    assert len(found) == 1


def test_class_has_tablename_attribute_not_found():
    code = """
class MyModel(Base):
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    ...
"""
    tree = cst.parse_module(code)
    found = m.findall(tree, class_has_tablename_attribute_matcher)
    assert len(found) == 0


def test_match_column_definition_line():
    code = "id = Column(Integer, primary_key=True)"
    stmt = cst.parse_statement(code)
    assert m.matches(stmt, column_definition_line_matcher)


def test_class_has_column_definitions():
    code = """
class MyModel(Base):
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    ...
"""
    tree = cst.parse_module(code)
    found = m.findall(tree, class_has_column_definitions_matcher)
    assert len(found) == 1


def test_class_has_column_definitions_not_found():
    code = """
class MyModel(Base):
    __tablename__ = "mymodels"
    ...
"""
    tree = cst.parse_module(code)
    found = m.findall(tree, class_has_column_definitions_matcher)
    assert len(found) == 0


def test_classmethod_with_session_arg_matcher():
    code = """
@classmethod
def get_active(cls, session, **kwargs):
    return session.query(cls).filter(cls.archived.is_(False)).all()
    """
    tree = cst.parse_module(code)
    found = m.findall(
        tree,
        build_classmethod_with_session_arg_matcher(possible_session_names=("session",)),
    )
    assert len(found) == 1


class TestAddSessionTypeAnnotationCommand(CodemodTest):
    TRANSFORM = AddSessionTypeAnnotationCommand

    def test_add_session_type_annotation(self):
        before = """
class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    
    @classmethod
    def get_active(cls, session):
        return session.query(cls).filter(cls.archived.is_(False)).all()
    """
        after = """
from sqlalchemy.orm import Session

class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    
    @classmethod
    def get_active(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(False)).all()
    """
        self.assertCodemod(before, after)

    def test_add_session_type_annotation_alt_naming(self):
        before = """
class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    
    @classmethod
    def get_active(cls, sess):
        return sess.query(cls).filter(cls.archived.is_(False)).all()
        
    @classmethod
    def get_archived(cls, session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
    """
        after = """
from sqlalchemy.orm import Session

class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)
    
    @classmethod
    def get_active(cls, sess: Session):
        return sess.query(cls).filter(cls.archived.is_(False)).all()
        
    @classmethod
    def get_archived(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
    """
        self.assertCodemod(before, after, possible_session_names=("sess", "session"))

    def test_add_session_type_annotation_partial(self):
        # Here we already have the import and one method annotated, so we should only add the annotation to the other.
        before = """
from sqlalchemy.orm import Session

class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)

    @classmethod
    def get_active(cls, session):
        return session.query(cls).filter(cls.archived.is_(False)).all()

    @classmethod
    def get_archived(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
    """
        after = """
from sqlalchemy.orm import Session

class MyModel(Base):
    __tablename__ = "mymodels"
    id = Column(Integer, primary_key=True)
    archived = Column(Boolean, default=False)

    @classmethod
    def get_active(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(False)).all()

    @classmethod
    def get_archived(cls, session: Session):
        return session.query(cls).filter(cls.archived.is_(True)).all()
"""
        self.assertCodemod(before, after)

    def test_add_session_type_annotation_no_change(self):
        before = """
class NotActuallyAModel:
    @classmethod
    def get_user(cls, session):
        ...
"""
        self.assertCodemod(before, before)
