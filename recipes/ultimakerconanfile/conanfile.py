import os

from conans import ConanFile, tools
from conans.errors import ConanException


class UltimakerBase(object):
    def ultimaker_layout(self, include_dir = "src"):
        compiler = self.settings.get_safe("compiler")
        multi = compiler in ("Visual Studio", "msvc")

        self.folders.source = "."
        try:
            build_type = str(self.settings.build_type)
        except ConanException:
            raise ConanException("'build_type' setting not defined, it is necessary for cmake_layout()")
        if multi:
            self.folders.build = "build"
        else:
            comp = "" if compiler in ("gcc", "apple-clang") else f"-{compiler}"
            build_type = build_type.lower()
            self.folders.build = f"cmake-build-{build_type}{comp}"
        self.folders.generators = os.path.join(self.folders.build, "conan")
        self.cpp.source.includedirs = [include_dir]
        if multi:
            self.cpp.build.libdirs = [f"{build_type}"]
            self.cpp.build.bindirs = [f"{build_type}"]
        else:
            self.cpp.build.libdirs = ["."]
            self.cpp.build.bindirs = ["."]

    @property
    def _executable_ext(self):
        if self.settings.os == "Windows":
            return ".exe"
        return ""

    @property
    def _python_name(self):
        v = tools.Version(self.dependencies["python"].ref.version)
        debug = "d" if self.info.settings.build_type == "Debug" else ""
        return f"python{v.major}.{v.minor}{debug}"

    @property
    def _python_site_packages_path(self):
        return os.path.join("lib", self._python_name, "site-packages")

    def _set_python_site_packages(self):
        site_package_path = os.path.join(self.folders.package_folder, self.self._python_site_packages_path)
        self.runenv_info.prepend_path("PYTHONPATH", site_package_path)
        self.buildenv_info.prepend_path("PYTHONPATH", site_package_path)
        self.user_info.pythonpath = site_package_path

    @property
    def _python_interp(self):
        if "python" in self.dependencies.items():
            return self.deps_user_info["python"].interp_path
        return None


class Pkg(ConanFile):
    name = "UltimakerBase"
    version = "0.4"
    default_user = "ultimaker"
    default_channel = "testing"
