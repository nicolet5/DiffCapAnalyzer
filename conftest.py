# pytest looks for the conftest modules on test collection
# to gather custom hooks and fixtures, and in order to
# import the custom objects from them, pytest adds the parent
# directory of the conftest.py to sys.path
# so this will ensure sys.path has the project directory to run tests
