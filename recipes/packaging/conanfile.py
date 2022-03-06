import os

from conans import tools
from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class PackagingConan(ConanFile):
    name = "packaging"
    version = "21.3"
    description = "Core utilities for Python packages"
    topics = ("conan", "python", "pypi", "pip")
    license = "BSD-2-Clause or Apache-2.0"
    homepage = "https://github.com/pypa/packaging"
    url = "https://github.com/pypa/packaging"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable", "pyparsing/3.0.7@python/stable"
    hashes = []

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

    def package_id(self):
        self.info.settings.build_type = "Release"
