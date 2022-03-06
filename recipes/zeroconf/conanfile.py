from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

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
    default_user = "pypi"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable",\
                "ifaddr/0.1.7@pypi/stable"
    hashes = [
        "sha256:53a180248471c6f81bd1fffcbce03ed93d7d8eaf10905c9121ac1ea996d19844",
        "sha256:5a468da018bc3f04bbce77ae247924d802df7aeb4c291bbbb5a9616d128800b0"
    ]

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
