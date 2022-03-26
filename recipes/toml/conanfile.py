from pathlib import Path
from conan import ConanFile
from conan.tools.files import files

required_conan_version = ">=1.33.0"


class TomlConan(ConanFile):
    name = "toml"
    description = "Python Library for Tom's Obvious, Minimal Language"
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT"
    homepage = "https://github.com/uiri/toml"
    url = "https://github.com/uiri/toml"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    requires = "cpython/[>=2.6.0]@python/stable"
    no_copy_source = True

    @property
    def _site_packages(self):
        return "site-packages"

    def source(self):
        files.get(self, **self.conan_data["sources"][self.version], destination = self._site_packages)

    def package(self):
        self.copy("*", src = self._site_packages, dst = self._site_packages)

    def package_info(self):
        self.env_info.PYTHONPATH = Path(self.package_folder, self._site_packages)
        self.user_info.pythonpath = Path(self.package_folder, self._site_packages)

    def package_id(self):
        self.info.header_only()
