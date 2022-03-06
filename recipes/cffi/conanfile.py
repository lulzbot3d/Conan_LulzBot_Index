from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"

# TODO: Compile from source using libffi


class CffiConan(ConanFile):
    name = "cffi"
    version = "1.14.1"
    description = "Foreign Function Interface for Python calling C code."
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT"
    homepage = "http://cffi.readthedocs.org"
    url = "http://cffi.readthedocs.org"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "pypi"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable",\
               "pycparser/2.20@pypi/stable"
    hashes = [
        "sha256:267adcf6e68d77ba154334a3e4fc921b8e63cbb38ca00d33d40655d4228502bc",
        "sha256:6923d077d9ae9e8bacbdb1c07ae78405a9306c8fd1af13bfa06ca891095eb995",
        "sha256:98be759efdb5e5fa161e46d404f4e0ce388e72fbf7d9baf010aff16689e22abe",
        "sha256:b1d6ebc891607e71fd9da71688fcf332a6630b7f5b7f5549e6e631821c0e5d90",
        "sha256:b2a2b0d276a136146e012154baefaea2758ef1f56ae9f4e01c612b0831e0bd2f",
        "sha256:d3148b6ba3923c5850ea197a91a42683f946dba7e8eb82dfa211ab7e708de939"
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
