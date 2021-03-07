# Static information flow analysis for Flake8

## What is this ?

The goal of this project was to create a plugin for Flake8 to statically analyse
your code and find dependencies between variables deemed _confidential_ or
_inconfidential_ (high/low in terms of security classes) by the user.

In the following code for example, we don't want any information about the
variable `high` to be leaked to the public. We furthermore have a variable `low`
that is available to the public. Note, that for Python specifically, this may
be less feasible as the inspection of variables is far easier than it is for
compiled languages like C. 

```
def foo(high, low): # flow: High, Low
    if high > 10:
        low = 10
    else:
        low = 0
    return low
```

(Note that for now that analysis only works on function parameters. Flow
specifications could also be added to local variables in the future)

Since high is a high confidentiality variable, we assume that the public does
not know anything about this variable. In the example function however, we have
an interaction between a publically accessible variable and a confidential
variable. The public variable is modified depending on the context of the
confidential variable and thus leaks information about the confidential
variable.

Using Static Flow Analysis, we can determine that in fact, there is an
information flow from a high to a low variable anbd display it as a Flake8
error.

## Disclaimer

As Static Information Flow Analysis may not be that useful in Python due to
inspection being easy, this could still be extended to work on ASTs for other
languages, e.g. C (check out the [pycparser project](https://github.com/eliben/pycparser)).
This however is just a simple demonstration of Static Information Flow Analysis
based on a so called _Hoare-Logic_. For fun, I added a binding to flake8 such
that we can also display the results in an IDE using this linter.
