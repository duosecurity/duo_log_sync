# Since there are no tests currently written for DuoLogSync, this basic 
# example is given to ensure that the test script for CI works
def inc(x):
    return x + 1

def test_inc():
    assert inc(4) == 5
