import os
from pathlib import Path

from conan import ConanFile
from conan.tools.files import chdir, copy

from conan.tools.microsoft.subsystems import unix_path


class SipBuildTool(object):
    """
    A build tool for sip

    This generator expects the project to have a pyproject.toml file.

    Usage in a conanfile for a Sip project:
    sip = self.python_requires["sipbuildtool"].module.SipBuildTool(self)
    sip.configure()
    sip.generate("projectName")
    """

    def __init__(self, conanfile: ConanFile):
        self._conanfile = conanfile
        self._sip_install_executable = "sip-build"

    def configure(self, sip_install_executable=None):
        if sip_install_executable:
            self._sip_install_executable = sip_install_executable

    def build(self):
        with chdir(self, self._conanfile.source_folder):
            sip_cmd = self._sip_install_executable
            subsystem = unix_path(self._conanfile, ".")
            sip_cmd = str(Path(subsystem).joinpath(sip_cmd))
            cmd = '"{}"'.format(sip_cmd)
            self._conanfile.output.info(f"Calling:\n > {cmd}")
            self._conanfile.run(cmd)


class Pkg(ConanFile):
    name = "sipbuildtool"
    package_type = "build-scripts"
    exports_sources = "SIPMacros.cmake"

    def package(self):
        copy(self, pattern="*.cmake", src=self.export_sources_folder, dst=os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        self.cpp_info.set_property("name", "sip")
        self.cpp_info.set_property("cmake_build_modules", [os.path.join("cmake", "SIPMacros.cmake")])
