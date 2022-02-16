from conan import ConanFile


class PythonVirtualEnvironment(object):
    def __init__(self, conanfile: ConanFile):
        self._conanfile = conanfile
        self._python_interpreter = None

    def configure(self, python_interpreter):
        if not self._conanfile.should_configure:
            return

        self._python_interpreter = python_interpreter

    def generate(self):
        if not self._conanfile.should_build:
            return

        cmd = f"{self._python_interpreter} -m venv {self._conanfile.folders.imports}"
        self._conanfile.run(cmd)


class Pkg(ConanFile):
    name = "PythonVirtualEnvironment"
    version = "0.1"
    default_user = "ultimaker"
    default_channel = "testing"
