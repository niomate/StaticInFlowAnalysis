def foo(a_long_variable_name, z, y):  # flow: Low, High, High
    if a_long_variable_name > 10:
        z = y
        y = 13
    return z


def bar(x, y):  # flow: High, Low
    if x > 10:
        y = 13
    return y
