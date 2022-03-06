import os

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class TrimeshConan(ConanFile):
    name = "trimesh"
    version = "3.9.36"
    description = "Import, export, process, analyze and view triangular meshes."
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT"
    homepage = "https://github.com/mikedh/trimesh"
    url = "https://github.com/mikedh/trimesh"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "pypi"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable",\
               "numpy/1.21.5@pypi/stable"
    hashes = [
        "sha256:f01e8edab14d1999700c980c21a1546f37417216ad915a53be649d263130181e",
        "sha256:8ac8bea693b3ee119f11b022fc9b9481c9f1af06cb38bc859bf5d16bbbe49b23"
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
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))

    def package_id(self):
        self.info.settings.build_type = "Release"
