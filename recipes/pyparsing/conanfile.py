from pathlib import Path

from conan import ConanFile

from conans.errors import ConanInvalidConfiguration
from conans.tools import Version
from conan.tools.files import files

required_conan_version = ">=1.33.0"


class PyparsingConan(ConanFile):
    name = "pyparsing"
    description = "Python parsing module"
    topics = ("conan", "python", "pypi", "pip")
    license = "MIT License"
    homepage = "https://github.com/pyparsing/pyparsing/"
    url = "https://github.com/pyparsing/pyparsing/"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    no_copy_source = True
    options = {
        "python_version": "ANY"
    }
    default_options = {
        "python_version": "3.0"
    }

    @property
    def _site_packages(self):
        return "site-packages"

    def source(self):
        sources = self.conan_data["sources"][self.version]
        if self.settings.get_safe("os") in sources:
            os_bin = self.settings.get_safe("os")
        elif "Any" in sources:
            os_bin = "Any"
        else:
            raise ConanInvalidConfiguration("Invalid version for Operating System")

        actual_python_version = Version(self.options.python_version)

        python_version = Version("1.0")
        python_version_key = "1.0"

        for py_version in sources[os_bin].keys():
            available_python_version = Version(py_version)
            if python_version < available_python_version <= actual_python_version:
                python_version = available_python_version
                python_version_key = py_version

        if python_version is Version("1.0"):
            raise ConanInvalidConfiguration("No compatible Python Version")

        self.output.info(f"Using wheel = {sources[os_bin][python_version_key]['url']}")
        files.get(self, **sources[os_bin][python_version_key], destination = self._site_packages)

    def package(self):
        self.copy("*", src = self._site_packages, dst = self._site_packages)

    def package_info(self):
        self.env_info.PYTHONPATH = Path(self.package_folder, self._site_packages)
        self.user_info.pythonpath = Path(self.package_folder, self._site_packages)

    def package_id(self):
        if len(self.conan_data["sources"][self.version]) >= 1 or "Any" not in self.conan_data["sources"][self.version]:
            self.info.settings.build_type = "Release"
        else:
            self.info.header_only()
