import os
from pathlib import Path

from conan import ConanFile


class PipBuildTool(object):
    def __init__(self, conanfile: ConanFile):
        # Store a reference to useful data
        self._conanfile = conanfile
        exec_ext = ".exe" if self._conanfile.settings.os == "Windows" else ""
        self._interp = os.path.join(f"python3{exec_ext}")
        self._conanfile.run("python -c 'import sys; print(sys.path)'")

    def configure(self):
        if not self._conanfile.should_configure:
            return

    def build(self):
        if not self._conanfile.should_build:
            return

        for whl in Path(self._conanfile.source_folder).glob("*.whl"):
            cmd = f"{self._interp} -m pip install --no-input --no-cache-dir --no-deps --root {self._conanfile.package_folder} --force-reinstall {whl}"
            self._conanfile.run(cmd)


class Pkg(ConanFile):
    name = "PipBuildTool"
    version = "0.3"
    default_user = "ultimaker"
    default_channel = "testing"
