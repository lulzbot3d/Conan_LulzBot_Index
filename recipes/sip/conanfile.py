import os
import stat
from pathlib import Path

from jinja2 import Template

from conans import tools
from conans.model import Generator

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv
from conan.tools.files.packager import AutoPackager

required_conan_version = ">=1.44.1"

class sip(Generator):

    @property
    def filename(self):
        pass

    @property
    def content(self):
        ext_deps = []
        deps_libs = []
        deps_lib_dirs = []
        deps_inc_dirs = []
        deps_compile_args = []
        deps_link_args = []
        deps_defines = []

        # Loop through all dependencies and collect needed necessary compile and link information
        for dep_name, dep_cpp_info in self.deps_build_info.dependencies:
            ext_deps.append(f'"{dep_name}"')

            for dep in dep_cpp_info.libs:  # The libs to link against
                deps_libs.append(f'"{dep}"')
            for dep in dep_cpp_info.system_libs:  # System libs to link against
                deps_libs.append(f'"{dep}"')

            for dep in dep_cpp_info.lib_paths:  # Directories where libraries can be found
                deps_lib_dirs.append(f'"{dep}"'.replace("\\", "/"))

            for dep in dep_cpp_info.include_paths:  # Directories where headers can be found
                deps_inc_dirs.append(f'"{dep}"'.replace("\\", "/"))

            for dep in dep_cpp_info.cppflags:  # C++ compilation flags
                deps_compile_args.append(f'"{dep}"')
            for dep in dep_cpp_info.cflags:  # pure C flags
                deps_compile_args.append(f'"{dep}"')

            for dep in dep_cpp_info.sharedlinkflags:  # linker flags
                deps_link_args.append(f'"{dep}"')
            for dep in dep_cpp_info.exelinkflags:  # linker flags
                deps_link_args.append(f'"{dep}"')

            for dep in dep_cpp_info.defines:  # preprocessor definitions
                deps_defines.append(f'"{dep}"')

        # Python version binary compatible (major.minor)
        python_version = tools.Version(self.conanfile.dependencies['python'].ref.version)

        with open(os.path.join(Path(__file__).parent, "ConanBuilder.py"), "r") as f:
            conan_builder_content = f.read()

        with open(os.path.join(Path(__file__).parent, "pyproject.toml.pre.jinja"), "r") as f:
            tm = Template(f.read())
            pyproject_toml_content = tm.render(
                module_version = self.conanfile.version,
                module_homepage = self.conanfile.url if self.conanfile.url else "",
                module_author = self.conanfile.author if self.conanfile.author else "",
                module_license = self.conanfile.license if self.conanfile.license else "",
                python_version = f"{python_version.major}.{python_version.minor}",
                external_deps = ",".join(ext_deps) if len(ext_deps) > 0 else "",
                deps_include_dirs = ",".join(deps_inc_dirs) if len(deps_inc_dirs) > 0 else "",
                deps_libraries = ",".join(deps_libs) if len(deps_libs) > 0 else "",
                deps_library_dirs = ",".join(deps_lib_dirs) if len(deps_lib_dirs) > 0 else "",
                deps_compile_args = ",".join(deps_compile_args) if len(deps_lib_dirs) > 0 else "",
                deps_link_args = ",".join(deps_link_args) if len(deps_link_args) > 0 else "",
                deps_define_macros = ",".join(deps_defines) if len(deps_lib_dirs) > 0 else "",
                build_type = "false" if self.settings.build_type == "Release" else "true")
            return {
                "pyproject.toml.pre": pyproject_toml_content,
                "ConanBuilder.py": conan_builder_content
            }


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
    requires = "python/3.10.2@python/stable"
    exports = ["sip.cmake.jinja", "pyproject.toml.pre.jinja", "sip_buildscript.jinja", "ConanBuilder.py"]
    exports_sources = ["sip.cmake.jinja", "pyproject.toml.pre.jinja", "sip_buildscript.jinja", "ConanBuilder.py"]
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
            result = tm.render(sip_build_script = self._sip_buildscript_path)
            tools.save(os.path.join(self.package_folder, self._cmake_install_base_path, "sip.cmake"), result)

        # Add the sip buildscript
        with open(os.path.join(self.source_folder, "sip_buildscript.jinja"), "r") as f:
            tm = Template(f.read())
            sip_executable = str(os.path.join(self.package_folder, "bin", "sip-build"))

            sip_build_env = ""
            pre_script = ""
            if self.settings.os == "Windows":
                sip_executable += ".exe"
                sip_build_env = f"env: PYTHONPATH+=;{self._pythonpath}"  # TODO: check on Windows
            else:
                pre_script = "#!/bin/bash"
                sip_build_env = f"export PYTHONPATH={self._pythonpath}:$PYTHONPATH"

            result = tm.render(pre_script = pre_script, sip_build_executable = sip_executable, sip_build_env = sip_build_env)
            tools.save(self._sip_buildscript_path, result)

        # set the executable bit TODO: check on Windows
        st = os.stat(self._sip_buildscript_path)
        os.chmod(self._sip_buildscript_path, st.st_mode | stat.S_IEXEC)

        # Add the rest of the sip files
        packager = AutoPackager(self)
        packager.patterns.lib = ["*.so", "*.so.*", "*.a", "*.lib", "*.dylib", "*.py*"]
        packager.run()

    def package_info(self):
        self.runenv_info.prepend_path("PYTHONPATH", self._pythonpath)
        self.buildenv_info.prepend_path("PYTHONPATH", self._pythonpath)
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
        sipbuild_script = "sip_buildscript"
        if self.settings.os == "Windows":
            sipbuild_script += ".ps1"
        else:
            sipbuild_script += ".sh"
        return os.path.join(self.package_folder, self._cmake_install_base_path, sipbuild_script)
