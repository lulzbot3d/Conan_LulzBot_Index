from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class IfaddrConan(ConanFile):
    name = "ifaddr"
    version = "0.1.7"
    description = "Cross-platform network interface and IP address enumeration library"
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT"
    homepage = "https://github.com/pydron/ifaddr"
    url = "https://github.com/pydron/ifaddr"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable"
    hashes = [
        "sha256:1f9e8a6ca6f16db5a37d3356f07b6e52344f6f9f7e806d618537731669eb1a94",
        "sha256:d1f603952f0a71c9ab4e705754511e4e03b02565bc4cec7188ad6415ff534cd3"
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
