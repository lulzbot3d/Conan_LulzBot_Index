import os

from conans import tools
from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.files.packager import AutoPackager

required_conan_version = ">=1.44.1"


class KeyringConan(ConanFile):
    name = "keyring"
    version = "23.0.1"
    description = "Store and access your passwords safely."
    topics = ("conan", "python", "pypi", "pip")
    license = ""
    homepage = "https://github.com/jaraco/keyring"
    url = "https://github.com/jaraco/keyring"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = "PipBuildTool/0.1@ultimaker/testing"
    hashes = [
        "sha256:045703609dd3fccfcdb27da201684278823b72af515aedec1a8515719a038cb8",
        "sha256:8f607d7d1cc502c43a932a275a56fe47db50271904513a379d39df1af277ac48"
    ]

    def requirements(self):
        self.requires("python/3.10.2@python/stable")
        self.requires(f"importlib-metadata/4.10.1@python/stable")
        if self.settings.os == "Windows":
            self.requires("pywin32-ctypes/0.2.0@python/stable")
        # TODO: We currently don't support Linux
        # if self.settings.os == "Linux":
        #     self.requires("secretstorage/3.3.1@python/stable")
        #     self.requires("jeepney/0.7.1@python/stable")

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
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
        self.buildenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}", "site-packages"))
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
