import os

from conans import tools
from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.files.packager import AutoPackager

required_conan_version = ">=1.44.1"


class ScipyConan(ConanFile):
    name = "scipy"
    version = "1.8.0rc2"
    description = "SciPy: Scientific Library for Python"
    topics = ("conan", "python", "pypi", "pip")
    license = "BSD"
    homepage = "https://www.scipy.org"
    url = "https://www.scipy.org"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = "PipBuildTool/0.1@ultimaker/testing"
    requires = "python/3.10.2@python/stable",\
               "numpy/1.21.5@python/stable"
    hashes = [
        "sha256:d73b13eb0452c178f946b4db60b27e400225df02e926609652ed67798054e77d",
        "sha256:8db99b6c017ab971b04a0781103a31ce745d4f0ac2b7db999523d4a94549ae15",
        "sha256:739ee3f6688c96516248f88725bbe1f241f3e0ab708f5eda98e2a9fe5cf38fba",
        "sha256:aa31ae8d8cf0abba07bc795f75b1aacf46b6136be22eefb4435040386f0f2bec",
        "sha256:4035b0f70d1bdbfe143005bb1033938529f684c0b93b4a90c2f59bbd88bcd0d3",
        "sha256:d6ccda8592a30120ea4c3ab669a10ab6e0c45284df9066b6583165d5092e75a7",
        "sha256:94a33efa21cffc5c3f8d416c0c1c79914019b9e3a82b5461176e4dc1c42218ea"
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
