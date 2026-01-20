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

    def configure(self, sip_install_executable=None, cpython_dependency=None):
        """
        Configure the sip-build executable path.
        
        Args:
            sip_install_executable: Explicit path to sip-build executable
            cpython_dependency: The cpython dependency from which to derive sip-build path
        """
        if sip_install_executable:
            self._sip_install_executable = sip_install_executable
        elif cpython_dependency:
            # Auto-detect sip-build location from cpython dependency
            bindirs = cpython_dependency.cpp_info.bindirs
            if bindirs and len(bindirs) > 0:
                bin_path = Path(bindirs[0])
                
                # On Windows, sip-build is in Scripts subdirectory
                if self._conanfile.settings.os == "Windows":
                    sip_path = bin_path / "Scripts" / "sip-build.exe"
                else:
                    # On Linux/Mac, sip-build is in bin directory
                    sip_path = bin_path / "sip-build"
                
                if sip_path.exists():
                    self._sip_install_executable = str(sip_path)
                else:
                    self._conanfile.output.warning(f"sip-build not found at expected path: {sip_path}")

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
