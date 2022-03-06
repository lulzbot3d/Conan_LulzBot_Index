import os

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class NumpySTLConan(ConanFile):
    name = "numpy-stl"
    version = "2.10.1"
    description = "Library to make reading, writing and modifying both binary and ascii STL files easy."
    topics = ("conan", "python", "pypi", "pip")
    license = "BSD"
    homepage = "https://github.com/WoLpH/numpy-stl/"
    url = "https://github.com/WoLpH/numpy-stl/"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable", \
               "numpy/1.21.5@python/stable"
    hashes = ["sha256:f6b529b8a8112dfe456d4f7697c7aee0aca62be5a873879306afe4b26fca963c"]

    def generate(self):
        rv = VirtualRunEnv(self)
        rv.generate()

        bv = VirtualBuildEnv(self)
        bv.generate()

    def build(self):
        pb = self.python_requires["PipBuildTool"].module.PipBuildTool(self)
        pb.configure()
        pb.build()

    def package(self):
        self.copy("*")

    def package_info(self):
        self._set_python_site_packages()
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))

    def package_id(self):
        self.info.settings.build_type = "Release"
