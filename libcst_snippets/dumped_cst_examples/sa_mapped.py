Module(
  body=[
    ClassDef(
      name=Name(
        value='User',
      ),
      body=IndentedBlock(
        body=[
          SimpleStatementLine(
            body=[
              Assign(
                targets=[
                  AssignTarget(
                    target=Name(
                      value='__tablename__',
                    ),
                  ),
                ],
                value=SimpleString(
                  value='"user"',
                ),
              ),
            ],
          ),
          SimpleStatementLine(
            body=[
              AnnAssign(
                target=Name(
                  value='id',
                ),
                annotation=Annotation(
                  annotation=Subscript(
                    value=Name(
                      value='Mapped',
                    ),
                    slice=[
                      SubscriptElement(
                        slice=Index(
                          value=Name(
                            value='int',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                value=Call(
                  func=Name(
                    value='mapped_column',
                  ),
                  args=[
                    Arg(
                      value=Name(
                        value='True',
                      ),
                      keyword=Name(
                        value='primary_key',
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          SimpleStatementLine(
            body=[
              AnnAssign(
                target=Name(
                  value='name',
                ),
                annotation=Annotation(
                  annotation=Subscript(
                    value=Name(
                      value='Mapped',
                    ),
                    slice=[
                      SubscriptElement(
                        slice=Index(
                          value=Name(
                            value='str',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                value=Call(
                  func=Name(
                    value='mapped_column',
                  ),
                  args=[
                    Arg(
                      value=Call(
                        func=Name(
                          value='String',
                        ),
                        args=[
                          Arg(
                            value=Integer(
                              value='50',
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          SimpleStatementLine(
            body=[
              AnnAssign(
                target=Name(
                  value='fullname',
                ),
                annotation=Annotation(
                  annotation=Subscript(
                    value=Name(
                      value='Mapped',
                    ),
                    slice=[
                      SubscriptElement(
                        slice=Index(
                          value=Subscript(
                            value=Name(
                              value='Optional',
                            ),
                            slice=[
                              SubscriptElement(
                                slice=Index(
                                  value=Name(
                                    value='str',
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          SimpleStatementLine(
            body=[
              AnnAssign(
                target=Name(
                  value='nickname',
                ),
                annotation=Annotation(
                  annotation=Subscript(
                    value=Name(
                      value='Mapped',
                    ),
                    slice=[
                      SubscriptElement(
                        slice=Index(
                          value=Subscript(
                            value=Name(
                              value='Optional',
                            ),
                            slice=[
                              SubscriptElement(
                                slice=Index(
                                  value=Name(
                                    value='str',
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                value=Call(
                  func=Name(
                    value='mapped_column',
                  ),
                  args=[
                    Arg(
                      value=Call(
                        func=Name(
                          value='String',
                        ),
                        args=[
                          Arg(
                            value=Integer(
                              value='30',
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      bases=[
        Arg(
          value=Name(
            value='Base',
          ),
        ),
      ],
    ),
  ],
)