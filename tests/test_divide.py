from coron.divide.divide_by_three import divide_by_three


def test_method():
    import os

    print(os.getcwd())


def test_divide_by_three():
    assert divide_by_three(45) == 15
