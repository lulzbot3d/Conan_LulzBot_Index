import os

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class Pyqt6Conan(ConanFile):
    name = "pyqt6"
    version = "6.2.2"
    description = "Python bindings for the Qt cross platform application toolkit"
    topics = ("conan", "python", "pypi", "pip")
    license = "GPL v3"
    homepage = "https://www.riverbankcomputing.com/software/pyqt/"
    url = "https://www.riverbankcomputing.com/software/pyqt/"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "pypi"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = ["python/3.10.2@python/stable",
                "pyqt6-sip/13.2.0@pypi/stable",
                "pyqt6-qt6/6.2.2@pypi/stable"]
    hashes = [ ]

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
