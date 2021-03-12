def baz(x):
    def foobar(z, y):  # flow: High, Low
        x = z + y
        return x
    return foobar(x, 10)
