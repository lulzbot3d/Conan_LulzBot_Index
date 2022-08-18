from conan import ConanFile
from conans import tools
from conans.client.subsystems import subsystem_path, deduce_subsystem


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
        self._sip_install_executable = "sip-install"

    def configure(self, sip_install_executable = None):
        if sip_install_executable:
            self._sip_install_executable = sip_install_executable

    def build(self):
        with tools.chdir(self._conanfile.source_folder):
            sip_cmd = self._sip_install_executable
            subsystem = deduce_subsystem(self._conanfile, scope = "build")
            sip_cmd = subsystem_path(subsystem, sip_cmd)
            cmd = '"{}"'.format(sip_cmd)
            self._conanfile.output.info(f"Calling:\n > {cmd}")
            self._conanfile.run(cmd)

class Pkg(ConanFile):
    name = "sipbuildtool"
    version = "0.2.1"
    default_user = "ultimaker"
    default_channel = "testing"
