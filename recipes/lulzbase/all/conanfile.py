import sys
import os

from io import StringIO
from pathlib import Path
from typing import Optional

from conans import ConanFile, tools
from conans.errors import ConanException


class LulzBaseConanfile(object):
    """
    LulzBot (formerly Ultimaker) base conanfile, for reusing Python code in our repositories
    https://docs.conan.io/en/latest/extending/python_requires.html
    """

    def _lulz_data(self) -> dict:
        """
        Extract the version specific data out of a conandata.yml
        """
        try:
            recipe_version = self.version
        except ConanException:
            recipe_version = "None"

        try:
            channel = self.channel
        except ConanException:
            channel = ""

        if channel:

            if channel == "testing":
                self.output.info(f"Using conandata.yml from channel: {channel}")
                return self.conan_data["None"]

            elif channel == "stable" or channel == "_" or channel == "":
                if recipe_version:
                    if recipe_version in self.conan_data:
                        self.output.info(f"Using conandata.yml from channel: {channel} and recipe version: {recipe_version}")
                        return self.conan_data[recipe_version]

                    recipe_version = tools.Version(recipe_version)
                    all_versions = []
                    for k in self.conan_data:
                        try:
                            v = tools.Version(k)
                        except ConanException:
                            continue
                        all_versions.append(v)

                    # First try to find a version which might take into account prereleases
                    satifying_versions = sorted([v for v in all_versions if v <= recipe_version])
                    if len(satifying_versions) == 0:
                        # Then try to find a version which only takes into account major.minor.patch
                        satifying_versions = sorted([v for v in all_versions if tools.Version(f"{v.major}.{v.minor}.{v.patch}") <= tools.Version(f"{recipe_version.major}.{recipe_version.minor}.{recipe_version.patch}")])
                        if len(satifying_versions) == 0:
                            self.output.warn(f"Could not find a maximum satisfying version from channel: {channel} for {recipe_version} in {[str(v) for v in all_versions]}, defaulting to testing channel")
                            return self.conan_data["None"]
                    version = str(satifying_versions[-1])
                    self.output.info(f"Using conandata.yml from channel: {channel} and recipe version: {version}")
                    return self.conan_data[version]

            elif channel in self.conan_data:
                self.output.info(f"Using conandata.yml from channel: {channel}")
                return self.conan_data[channel]

        self.output.info(f"Using conandata.yml defaulting to testing channel")
        return self.conan_data["None"]

    @property
    def _python_venv_bin_path(self) -> str:
        if self.settings.os == "Windows":
            return "Scripts"
        return "bin"

    @property
    def _python_interp(self) -> str:
        """
        The Python interpreter to use. If the recipe has `cpython` as a dependency it uses that interpreter otherwise it will use the system
        interpreter. Which in this case is the same as the Conan version.
        :return: str with the path to the Python interpreter
        """

        if "cpython" in self.deps_user_info:
            py_interp = Path(self.deps_user_info["cpython"].python)
        else:
            py_interp = Path(sys.executable)

        # When on Windows execute as Windows Path
        if self.settings.os == "Windows":
            py_interp = Path(*[f'"{p}"' if " " in p else p for p in py_interp.parts])

        return str(py_interp)

    @property
    def _py_venv_interp(self) -> str:
        if self.__py_venv_interp is not None:
            return self.__py_venv_interp
        else:
            self.output.warn("Virtual Python environment not yet generated, but requesting the path to interpreter")
            py_venv_interp = Path(self.install_folder, self._venv_path, Path(sys.executable).stem + Path(sys.executable).suffix)

            if self.settings.os == "Windows":
                py_venv_interp = Path(*[f'"{p}"' if " " in p else p for p in py_venv_interp.parts])

            return str(py_venv_interp)

    @_py_venv_interp.setter
    def _py_venv_interp(self, value: str):
        self.__py_venv_interp = value

    def _site_packages_path(self, interp: str) -> str:
        buffer = StringIO()
        outer = '"' if self.settings.os == "Windows" else "'"
        inner = "'" if self.settings.os == "Windows" else '"'
        self.run(f"{interp} -c {outer}import sysconfig; print(sysconfig.get_path({inner}purelib{inner})){outer}", env = "conanrun", output = buffer)
        pythonpath = buffer.getvalue().splitlines()[-1]
        return pythonpath

    def _generate_virtual_python_env(self, *initial_reqs):
        """
        Generates a virtual Python Environment and initializes is

        TODO: Check if we aren't in an actual virtual Python environment yet. Because running a venv in a venv is asking for troubles

        :param initial_reqs: Python modules which should be installed (strings)
        """
        self.output.info("Generating virtual Python environment")
        self.run(f"{self._python_interp} -m venv {self.install_folder}", run_environment = True, env = "conanrun")

        # Make sure there executable is named the same on all three OSes this allows it to be called with `python`
        # simplifying GH Actions steps
        if self.settings.os != "Windows":
            py_venv_interp = Path(self.install_folder, self._python_venv_bin_path, "python")
            if not py_venv_interp.exists():
                py_venv_interp.hardlink_to(Path(self.install_folder, self._python_venv_bin_path, Path(sys.executable).stem + Path(sys.executable).suffix))
        else:
            py_venv_interp = Path(self.install_folder, self._python_venv_bin_path, Path(sys.executable).stem + Path(sys.executable).suffix)

        if not py_venv_interp.exists():
            raise ConanException(f"Virtual environment Python interpreter not found at: {py_venv_interp}")
        if self.settings.os == "Windows":
            py_venv_interp = Path(*[f'"{p}"' if " " in p else p for p in py_venv_interp.parts])

        # Updating the run environment
        self.runenv_info.define_path("VIRTUAL_ENV", self.install_folder)
        self.runenv_info.prepend_path("PATH", os.path.join(self.install_folder, self._python_venv_bin_path))
        self.runenv_info.prepend_path("PYTHONPATH", self._site_packages_path(py_venv_interp))
        self.runenv_info.unset("PYTHONHOME")

        # Installing the initial_reqs
        reqs = " ".join(initial_reqs)
        self.run(f"{py_venv_interp} -m pip install {reqs}", run_environment = True, env = "conanrun")

        self.output.success(f"Created a Virtual Python Environment in {self.install_folder}")
        self._py_venv_interp = str(py_venv_interp)


class Pkg(ConanFile):
    name = "lulzbase"
    exports_sources = "StandardProjectSettings.cmake"

    def package(self):
        self.copy("StandardProjectSettings.cmake", "cmake")

    def package_info(self):
        self.cpp_info.set_property("name", "lulzbase")
        self.cpp_info.set_property("cmake_build_modules", [os.path.join("cmake", "StandardProjectSettings.cmake")])
