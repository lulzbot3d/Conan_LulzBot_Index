from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"

# TODO: Compile from source using clipper

class PyclipperConan(ConanFile):
    name = "pyclipper"
    version = "1.3.0.post2"
    description = "Cython wrapper for the C++ translation of the Angus Johnson's Clipper library (ver. 6.4.2)"
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT"
    homepage = "https://github.com/greginvm/pyclipper"
    url = "https://github.com/greginvm/pyclipper"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable"
    hashes = [
        "sha256:c096703dc32f2e4700a1f7054e8b58c29fe86212fa7a2c2adecb0102cb639fb2",
        "sha256:a1525051ced1ab74e8d32282299c24c68f3e31cd4b64e0b368720b5da65aad67",
        "sha256:5960aaa012cb925ef44ecabe69528809564a3c95ceac874d95c6600f207138d3",
        "sha256:d3954330c02a19f7566651a909ec4bc5733ba6c62a228ab26db4a90305748430",
        "sha256:5175ee50772a7dcc0feaab19ccf5b979b6066f4753edb330700231cf70d0c918",
        "sha256:19a6809d9cbd535d0fe922e9315babb8d70b5c7dcd43e0f89740d09c406b40f8",
        "sha256:5c5d50498e335d7f969ca5ad5886e77c40088521dcabab4feb2f93727140251e"
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
