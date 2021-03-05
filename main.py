# Core Library modules
import ast

# First party modules
from staticinflowanalysis.hoare import analyse

if __name__ == '__main__':
    code = """
def foo(x, z):  # type: x: Low, z: High
    if x > 10:
        z = y
    else:
        z = -x
    return z

def bar(x, z, y, a): # type: x:High, z:Low
    while y < z:
        x *= y
    return y + a
    """
    print("Analysed code:")
    print(code)
    t = ast.parse(code, type_comments=True)
    errors = analyse(t)
    if not errors:
        print("No errors found")
    else:
        print("Found errors:")
        print("\n".join(errors))
