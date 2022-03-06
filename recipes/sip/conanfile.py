import os

from jinja2 import Template

from conans import tools

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

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
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable", "toml/0.10.2@python/stable", "packaging/21.3@python/stable"
    exports = ["sip.cmake.jinja", "CMakeBuilder.py"]
    exports_sources = ["sip.cmake.jinja", "CMakeBuilder.py"]
    hashes = []

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
            python_path = self._python_site_packages_path
            for dep in self.deps_user_info.values():
                if hasattr(dep, "pythonpath"):
                    python_path += path_sep + dep.pythonpath
            result = tm.render(sip_build_script = self._sip_buildscript_path,
                               conan_python_path = python_path,
                               site_packages = os.path.join("..", self._python_site_packages_path),
                               sip_cmake_module_path = os.path.join(self.package_folder, self._cmake_install_base_path))
            tools.save(os.path.join(self.package_folder, self._cmake_install_base_path, "sip.cmake"), result)
        self.copy("CMakeBuilder.py", dst=os.path.join(self.package_folder, self._cmake_install_base_path), keep_path = False)
        self.copy("*")

    def package_info(self):
        self._set_python_site_packages()
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))

        self.cpp_info.set_property("cmake_file_name", "sip")
        self.cpp_info.set_property("cmake_target_name", "sip::sip")
        self.cpp_info.set_property("cmake_target_aliases", ["SIP::SIP"])

        self.cpp_info.set_property("cmake_build_modules", [os.path.join(self._cmake_install_base_path, "sip.cmake")])
        sip_v = tools.Version(self.version)
        self.cpp_info.set_property("defines", f"-DSIP_VERSION=0x{int(sip_v.major):02d}{int(sip_v.minor):02d}{int(sip_v.patch):02d}")

    def package_id(self):
        self.info.settings.build_type = "Release"

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake", "sip")

    @property
    def _sip_buildscript_path(self):
        sipbuild_script = f"sip-build{self._executable_ext}"
        return os.path.join(self.package_folder, "bin", sipbuild_script)
