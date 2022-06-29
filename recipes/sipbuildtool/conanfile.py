import os
import sys

from pathlib import Path
from io import StringIO

from jinja2 import Template

from conan import ConanFile
from conan.tools.env import VirtualRunEnv
from conan.tools.files import files
from conans.errors import ConanException


class SipBuildTool(object):
    """
    A generator that creates a CMake script to build python bindings for
    projects using Sip.

    This generator expects the project to have a pyproject.toml.jinja file that
    determines which Sip files to compile. It configures that file to a TOML
    file that Sip can use.

    Usage in a conanfile for a Sip project:
    sip = self.python_requires["sipbuildtool"].module.SipBuildTool(self)
    sip.configure()
    sip.generate("projectName")
    """
    def __init__(self, conanfile: ConanFile):
        self.conanfile = conanfile
        env = VirtualRunEnv(self.conanfile)
        self.run_env = env.environment()
        self.envvars = None
        self.python_venv_interpreter = None
        self.sip_build_executable = None

    @property
    def _venv_base_path(self):
        return os.path.join(self.conanfile.build_folder, "venv")

    @property
    def _venv_bin_path(self):
        if self.conanfile.settings.os == "Windows":
            return os.path.join(self._venv_base_path, "Scripts")
        return os.path.join(self._venv_base_path, "bin")

    def configure(self, sip_version = "6.5.1", python_interpreter = sys.executable):
        python_interpreter = Path(python_interpreter)

        # When on Windows execute as Windows Path
        if self.conanfile.settings.os == "Windows":
            python_interpreter = Path(*[f'"{p}"' if " " in p else p for p in python_interpreter.parts])

        # Create the virtual environment
        self.conanfile.run(f"""{python_interpreter} -m venv {self._venv_base_path}""", env = "conanbuild")

        # Make sure there executable is named the same on all three OSes this allows it to be called with `python`
        # simplifying GH Actions steps
        if self.conanfile.settings.os != "Windows":
            self.python_venv_interpreter = Path(self.conanfile.build_folder, self._venv_bin_path, "python")
            if not self.python_venv_interpreter.exists():
                self.python_venv_interpreter.hardlink_to(Path(self.conanfile.build_folder, self._venv_bin_path,
                                                              Path(sys.executable).stem + Path(sys.executable).suffix))
        else:
            self.python_venv_interpreter = Path(self.conanfile.build_folder, self._venv_bin_path,
                                                Path(sys.executable).stem + Path(sys.executable).suffix)

        if not self.python_venv_interpreter.exists():
            raise ConanException(f"Virtual environment Python interpreter not found at: {self.python_venv_interpreter}")
        if self.conanfile.settings.os == "Windows":
            self.python_venv_interpreter = Path(*[f'"{p}"' if " " in p else p for p in self.python_venv_interpreter.parts])

        buffer = StringIO()
        outer = '"' if self.conanfile.settings.os == "Windows" else "'"
        inner = "'" if self.conanfile.settings.os == "Windows" else '"'
        self.conanfile.run(
            f"{self.python_venv_interpreter} -c {outer}import sysconfig; print(sysconfig.get_path({inner}purelib{inner})){outer}",
            env = "conanbuild",
            output = buffer)
        pythonpath = buffer.getvalue().splitlines()[-1]

        self.run_env.define_path("VIRTUAL_ENV", self._venv_base_path)
        self.run_env.prepend_path("PATH", self._venv_bin_path)
        self.run_env.prepend_path("PYTHONPATH", pythonpath)
        self.run_env.unset("PYTHONHOME")

        self.envvars = self.run_env.vars(self.conanfile, scope = "run")

        with self.envvars.apply():
            # Install some base_packages
            self.conanfile.run(f"""{self.python_venv_interpreter} -m pip install wheel setuptools""", run_environment = True,
                               env = "conanrun")
            # Install sip
            self.conanfile.run(f"""{self.python_venv_interpreter} -m pip install sip=={sip_version}""", run_environment = True,
                               env = "conanrun")

        self.sip_build_executable = Path(self._venv_bin_path, "sip-build")
        if self.conanfile.settings.os == "Windows":
            self.sip_build_executable = Path(*[f'"{p}"' if " " in p else p for p in self.sip_build_executable.parts])

    def generate(self, module_name, sip_dir = "python", sip_include_dirs = "python", args = "--pep484-pyi --no-protected-is-public"):
        # Generate the CMakeBuilder
        cmake_builder = r"""from sipbuild import SetuptoolsBuilder


class CMakeBuilder(SetuptoolsBuilder):
    def __init__(self, project, **kwargs):
        print("Using the Conan SipBuildTool")
        super().__init__(project, **kwargs)

    def build(self):
        "Only Generate the source files "
        print("Generating the source files")
        self._generate_bindings()
        self._generate_scripts()
        """

        files.save(self.conanfile, os.path.join(self.conanfile.build_folder, "CMakeBuilder.py"), cmake_builder)

        # Generate the pyproject.toml
        pyproject_toml_template = Template(files.load(self.conanfile, os.path.join(self.conanfile.source_folder, "pyproject.toml.jinja")))
        files.save(self.conanfile, os.path.join(self.conanfile.build_folder, "pyproject.toml"), pyproject_toml_template.render(
            module_name = module_name,
            sip_dir = os.path.join(self.conanfile.source_folder, sip_dir).replace("\\", "\\\\"),
            sip_include_dirs = os.path.join(self.conanfile.source_folder, sip_include_dirs).replace("\\", "\\\\"),
            build_dir = os.path.join(self.conanfile.build_folder, module_name).replace("\\", "\\\\")))

        with self.envvars.apply():
            # Run sip-build to generate the source code
            self.conanfile.run(f"""{self.sip_build_executable} {args}""", run_environment = True, env = "conanrun",
                               cwd = self.conanfile.build_folder)

        files.rmdir(self.conanfile, self._venv_base_path)


class Pkg(ConanFile):
    name = "sipbuildtool"
    version = "0.1"
    default_user = "ultimaker"
    default_channel = "testing"
