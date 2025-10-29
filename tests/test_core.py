from coron.core import ExampleClass, add_two, example_function


def test_example_function():
    assert example_function(1, 2) == 3


def test_example_class():
    instance = ExampleClass()
    assert instance.example_class_method() == "expected result"


def test_add_two():
    assert add_two(5) == 7
