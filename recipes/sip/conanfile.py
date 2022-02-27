import os

from jinja2 import Template

from conans import tools

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.files.packager import AutoPackager

required_conan_version = ">=1.44.1"

class Pyqt6SipConan(ConanFile):
    name = "sip"
    version = "6.5.0"
    description = "The sip module support for PyQt5"
    topics = ("conan", "python", "pypi", "pip")
    license = "GPL v3"
    homepage = "https://www.riverbankcomputing.com/software/sip/"
    url = "https://www.riverbankcomputing.com/software/sip/"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = "PipBuildTool/0.2@ultimaker/testing"
    requires = "python/3.10.2@python/stable", "toml/0.10.2@python/stable", "packaging/21.3@python/stable"
    exports = ["sip.cmake.jinja", "CMakeBuilder.py"]
    exports_sources = ["sip.cmake.jinja", "CMakeBuilder.py"]
    hashes = []

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
        # Add the sip CMake build module
        with open(os.path.join(self.source_folder, "sip.cmake.jinja"), "r") as f:
            tm = Template(f.read())
            path_sep = ";" if self.settings.os == "Windows" else ":"
            python_path = self._pythonpath
            for dep in self.deps_user_info.values():
                if hasattr(dep, "pythonpath"):
                    python_path += path_sep + dep.pythonpath
            result = tm.render(sip_build_script = self._sip_buildscript_path, conan_python_path = python_path)
            tools.save(os.path.join(self.package_folder, self._cmake_install_base_path, "sip.cmake"), result)

        # Add the rest of the sip files
        packager = AutoPackager(self)
        packager.patterns.lib = ["*.so", "*.so.*", "*.a", "*.lib", "*.dylib", "*.py*"]
        packager.run()

    def package_info(self):
        self.runenv_info.prepend_path("PYTHONPATH", self._pythonpath)
        self.buildenv_info.prepend_path("PYTHONPATH", self._pythonpath)
        self.user_info.python_path = self._pythonpath

        self.cpp_info.set_property("cmake_file_name", "sip")
        self.cpp_info.set_property("cmake_target_name", "sip::sip")
        self.cpp_info.set_property("cmake_build_modules", [os.path.join(self._cmake_install_base_path, "sip.cmake")])
        sip_v = tools.Version(self.version)
        self.cpp_info.set_property("defines", f"-DSIP_VERSION=0x{int(sip_v.major):02d}{int(sip_v.minor):02d}{int(sip_v.patch):02d}")

    def package_id(self):
        self.info.settings.build_type = "Release"

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake", "sip")

    @property
    def _pythonpath(self):
        v = tools.Version(self.dependencies['python'].ref.version)
        return os.path.join(self.package_folder, "lib", f"python{v.major}.{v.minor}", "site-packages")

    @property
    def _sip_buildscript_path(self):
        sipbuild_script = "sip-build"
        if self.settings.os == "Windows":
            sipbuild_script += ".exe"
        return os.path.join(self.package_folder, self._cmake_install_base_path, sipbuild_script)
