from chachies import add

def test_add(a,b):
    assert add(1,1) == 2
    assert add(0,1) == 1
    assert add(-1,1) == 0
