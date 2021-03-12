def bar(x, y):  # flow: Low, High
    c = 34  # flow: High
    if x > c:
        y = 13
        c = x
    return y
