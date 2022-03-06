from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class CryptographyConan(ConanFile):
    name = "cryptography"
    version = "3.4.8"
    description = "cryptography is a package which provides cryptographic recipes and primitives to Python developers."
    topics = ("conan", "python", "pypi", "pip")
    license = "BSD or Apache License, Version 2.0"
    homepage = "https://github.com/pyca/cryptography"
    url = "https://github.com/pyca/cryptography"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable",\
                "cffi/1.14.1@python/stable"
    hashes = [
        "sha256:a00cf305f07b26c351d8d4e1af84ad7501eca8a342dedf24a7acb0e7b7406e14",
        "sha256:3520667fda779eb788ea00080124875be18f2d8f0848ec00733c0ec3bb8219fc",
        "sha256:1eb7bb0df6f6f583dd8e054689def236255161ebbcf62b226454ab9ec663746b"
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
