from conan import ConanFile
from conans import tools


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
        self.conanfile = conanfile
        self._sip_install_executable = None

    def configure(self, sip_install_executable = None):
        if not sip_install_executable:
            sip_install_executable = "sip-install"
            if self.conanfile.settings.os == "Windows":
                sip_install_executable += ".exe"

        self._sip_install_executable = sip_install_executable

    def build(self):
        with tools.chdir(self.conanfile.source_folder):
            self.conanfile.run(f"{self._sip_install_executable}", env = "run")

class Pkg(ConanFile):
    name = "sipbuildtool"
    version = "0.2.0"
    default_user = "ultimaker"
    default_channel = "testing"
