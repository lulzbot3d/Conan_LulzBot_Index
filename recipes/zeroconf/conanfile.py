import os

from conans import tools
from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.files.packager import AutoPackager

required_conan_version = ">=1.44.1"


class ZeroconfConan(ConanFile):
    name = "zeroconf"
    version = "0.31.0"
    description = "Pure Python Multicast DNS Service Discovery Library (Bonjour/Avahi compatible)"
    topics = ("conan", "python", "pypi", "pip")
    license = "LGPL"
    homepage = "https://github.com/jstasiak/python-zeroconf"
    url = "https://github.com/jstasiak/python-zeroconf"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = "PipBuildTool/0.1@ultimaker/testing"
    requires = "python/3.10.2@python/stable",\
                "ifaddr/0.1.7@python/stable"
    hashes = [
        "sha256:53a180248471c6f81bd1fffcbce03ed93d7d8eaf10905c9121ac1ea996d19844",
        "sha256:5a468da018bc3f04bbce77ae247924d802df7aeb4c291bbbb5a9616d128800b0"
    ]

    def layout(self):
        self.folders.build = "build"
        self.folders.package = "package"
        self.folders.generators = os.path.join("build", "conan")

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
        packager = AutoPackager(self)
        packager.patterns.lib = ["*.so", "*.so.*", "*.a", "*.lib", "*.dylib", "*.py*"]
        packager.run()

    def package_info(self):
        v = tools.Version(self.dependencies['python'].ref.version)
        self.runenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}", "site-packages"))
        self.buildenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}", "site-packages"))
