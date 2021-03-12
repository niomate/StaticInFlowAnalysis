def foo(a_long_variable_name, z, y):  # flow: Low, High, High
    if a_long_variable_name > 10:
        z = y
        y = 13
    return z
