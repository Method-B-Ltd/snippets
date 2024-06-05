These are some examples of how to use libcst to refactor Python code.

The route_transformer.py shows a way to refactor a Flask route shaped like this:


```python
@admin.route("/users")
def users():
    g.user.require(ADMIN_PERMISSION)
    ...
```

To use a modified decorator that checks the user's permissions:

```python

@admin.route("/users", permission=ADMIN_PERMISSION)
def users():
    ...
```

NB: This isn't a feature of Flask, it's a hypothetical example of how you could use libcst to refactor code.