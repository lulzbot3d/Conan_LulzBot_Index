import os

from conan import ConanFile

class PipBuildTool(object):
    def __init__(self, conanfile: ConanFile, parallel=True):
        # Store a reference to useful data
        self._conanfile = conanfile
        exec_ext = ".exe" if self._conanfile.settings.os == "Windows" else ""
        self._interp = os.path.join(self._conanfile.dependencies['python'].package_folder, self._conanfile.dependencies['python'].cpp_info.bindirs[0], f"python3{exec_ext}")
        self._hashes = self._conanfile.hashes
        self._check_hash = False
        self._parallel = parallel

    def configure(self,  check_hash = False):
        if not self._conanfile.should_configure:
            return
        self._check_hash = check_hash

    def build(self):
        if not self._conanfile.should_build:
            return

        cmd = f"{self._interp} -m pip install --no-deps --prefix {self._conanfile.package_folder} --force-reinstall {self._conanfile.name}=={self._conanfile.version}"
        self._conanfile.run(cmd)


class Pkg(ConanFile):
    name = "PipBuildTool"
    version = "0.2"
    default_user = "ultimaker"
    default_channel = "testing"
