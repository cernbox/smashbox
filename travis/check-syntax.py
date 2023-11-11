import py_compile
import sys

sys.stderr = sys.stdout
py_compile.compile(sys.argv[1])
