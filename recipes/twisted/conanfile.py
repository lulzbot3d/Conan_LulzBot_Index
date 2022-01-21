import os

from conans import tools
from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.files.packager import AutoPackager

required_conan_version = ">=1.44.1"


class TwistedConan(ConanFile):
    name = "twisted"
    version = "21.2.0"
    description = "An asynchronous networking framework written in Python"
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT"
    homepage = "https://twistedmatrix.com/"
    url = "https://twistedmatrix.com/"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = "PipBuildTool/0.1@ultimaker/testing"
    requires = "python/3.10.2@python/stable", \
               "constantly/15.1.0@python/stable", \
               "hyperlink/21.0.0@python/stable", \
               "incremental/21.3.0@python/stable", \
               "zope_interface/5.4.0@python/stable", \
               "twisted-iocpsupport/1.0.2@python/stable", \
               "Automat/20.2.0@python/stable", \
               "attrs/21.2.0@python/stable"
    hashes = [
        "sha256:77544a8945cf69b98d2946689bbe0c75de7d145cdf11f391dd487eae8fc95a12",
        "sha256:aab38085ea6cda5b378b519a0ec99986874921ee8881318626b0a3414bb2631e"
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
        self.runenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}"), "site-packages")
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))

        self.buildenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}"), "site-packages")
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
