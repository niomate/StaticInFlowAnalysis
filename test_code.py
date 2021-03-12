def foo(a_long_variable_name, z, y):  # flow: Low, High, High
    if a_long_variable_name > 10:
        z = y
        y = 13
    return z


def baz(x):
    def foobar(z, y):  # flow: High, Low
        x = z + y
        return x
    return foobar(x, 10)


def bar(x, y):  # flow: Low, High
    c = 34  # flow: High
    if x > c:
        y = 13
        c = x
    return y
