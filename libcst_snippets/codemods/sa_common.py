import libcst.matchers as m

column_definition_line_matcher = m.SimpleStatementLine(
    body=[m.AtLeastN(n=1, matcher=m.Assign(value=m.Call(func=m.Name(value="Column"))))]
)

class_has_tablename_attribute_matcher = m.ClassDef(
    body=m.IndentedBlock(
        body=[
            m.AtLeastN(n=0),
            m.AtLeastN(
                n=1,
                matcher=m.SimpleStatementLine(
                    body=[
                        m.AtLeastN(
                            n=1,
                            matcher=m.Assign(
                                targets=[
                                    m.AtLeastN(
                                        n=1,
                                        matcher=m.AssignTarget(
                                            target=m.Name(value="__tablename__")
                                        ),
                                    )
                                ]
                            ),
                        )
                    ]
                ),
            ),
            m.AtLeastN(n=0),
        ]
    )
)

class_has_column_definitions_matcher = m.ClassDef(
    body=m.IndentedBlock(
        body=[
            m.AtLeastN(n=0),
            m.AtLeastN(n=1, matcher=column_definition_line_matcher),
            m.AtLeastN(n=0),
        ]
    )
)

class_probably_an_sa_model = (
    class_has_tablename_attribute_matcher | class_has_column_definitions_matcher
)
