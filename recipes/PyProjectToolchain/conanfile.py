import textwrap
from pathlib import Path

from jinja2 import Template

from conan import ConanFile
from conan.tools.cmake.toolchain.blocks import Block
from conan.tools.cmake.toolchain.toolchain import ToolchainBlocks
from conan.tools.files import save
from conan.errors import ConanInvalidConfiguration
from conan.tools._check_build_profile import check_using_build_profile
from conans.tools import Version


class BuildSystemBlock(Block):
    template = textwrap.dedent("""
    [build-system]
    requires = [{{ build_requires }}]
    {{ build_backend }}
    """)

    def context(self):
        build_requires = self._conanfile.options.get_safe("py_build_requires")
        if build_requires is None:
            build_requires = "setuptools>=40.8.0", "wheel"
        else:
            build_requires = [r.strip() for r in build_requires.split(",")]
        build_backend = self._conanfile.options.get_safe("py_build_backend")
        if build_backend is not None:
            build_backend = f"build-backend = \"{build_backend}\""
        return {"build_requires": build_requires, "build_backend": build_backend}


class ToolSipMetadataBlock(Block):
    template = textwrap.dedent("""
    [tool.sip.metadata]
    name = "{{ name }}"
    version = "{{ version }}"
    summary = "{{ description }}"
    home-page = "{{ url }}"
    author = "{{ author }}"
    license = "{{ license }}"
    description-file = "README.md"
    requires-python = ">={{ python_version }}"
    """)

    def context(self):
        python_version = self._conanfile.options.get_safe("py_version")
        if python_version is None:
            if "cpython" in self._conanfile.dependencies:
                python_version = self._conanfile["cpython"].ref.version
            else:
                raise ConanInvalidConfiguration(
                    "No minimum required Python version specified, either add the options: 'py_version' of add cpython as a Conan dependency!")

        return {
            "name": self._conanfile.name,
            "version": self._conanfile.version,
            "description": self._conanfile.description,
            "url": self._conanfile.url,
            "author": self._conanfile.author,
            "license": self._conanfile.license,
            "python_version": python_version
        }


class ToolSipProjectBlock(Block):
    template = textwrap.dedent("""
    [tool.sip.project]
    sip-files-dir = "{{ sip_files_dir }}"
    build-dir = "{{ build_folder }}"
    {{ py_include_dir }}
    {{ py_major_version }}
    {{ py_minor_version }}
    """)

    def context(self):
        python_version = self._conanfile.options.get_safe("py_version")
        py_include_dir = self._conanfile.options.get_safe("py_include")
        py_major_version = None
        py_minor_version = None

        if python_version is None:
            if "cpython" in self._conanfile.dependencies:
                python_version = self._conanfile.dependencies["cpython"].ref.version
            else:
                raise self._conanfile.output.warn(
                    "No minimum required Python version specified, either add the options: 'py_version' of add cpython as a Conan dependency!")

        if python_version is not None:
            py_version = Version(python_version)
            py_major_version = py_version.major
            py_minor_version = py_version.minor

            if py_include_dir is None:
                if "cpython" in self._conanfile.dependencies:
                    py_include_dir = f"{self._conanfile.deps_cpp_info['cpython'].includedirs[0]}/python{py_major_version}.{py_minor_version}"
                else:
                    raise self._conanfile.output.warn(
                        "No include directory set for Python.h, either add the options: 'py_include' of add cpython as a Conan dependency!")
                py_include_dir = f"py-include-dir = \"{py_include_dir}\""

            py_major_version = f"py-major-version = {py_version.major}"
            py_minor_version = f"py-minor-version = {py_version.minor}"

        sip_files_dir = Path(self._conanfile.source_folder, self._conanfile.name)

        return {
            "sip_files_dir": sip_files_dir,
            "build_folder": self._conanfile.build_folder,
            "py_include_dir": py_include_dir,
            "py_major_version": py_major_version,
            "py_minor_version": py_minor_version
        }


class ToolSipBindingsExtraSourcesBlock(Block):
    template = textwrap.dedent("""
    headers = [{% for linkarg in linkeargs %}}"{{ linkarg }}", {% endfor %}]
    include-dirs = [{% for linkarg in linkeargs %}}"{{ linkarg }}", {% endfor %}]
    sources = [{% for linkarg in linkeargs %}}"{{ linkarg }}", {% endfor %}]
    """)

    def context(self):
        libs = []
        libdirs = []
        includedirs = []

        return {
            "name": self._conanfile.name,
            "libs": libs,
            "libdirs": libdirs,
            "includedirs": includedirs
        }


class ToolSipBindingsBlock(Block):
    template = textwrap.dedent("""
    [tool.sip.bindings.{{ name }}]
    exceptions = true
    release-gil = true
    libraries = [{% for lib in libs %}}"{{ lib }}", {% endfor %}]
    library-dirs = [{% for libdir in libdirs %}}"{{ libdir }}", {% endfor %}]
    include-dirs = [{% for includedir in includedirs %}}"{{ includedir }}", {% endfor %}]
    extra-compile-args = [{% for compilearg in compileargs %}}"{{ compilearg }}", {% endfor %}]
    extra-link-args = [{% for linkarg in linkargs %}}"{{ linkarg }}", {% endfor %}]
    pep484-pyi = true
    static = {{ build_static | lower }}
    """)

    def context(self):
        libs = []
        libdirs = []
        includedirs = []
        compileargs = []
        linkargs = []

        return {
            "name": self._conanfile.name,
            "libs": libs,
            "libdirs": libdirs,
            "includedirs": includedirs,
            "compileargs": compileargs,
            "linkargs": linkargs,
            "build_static": str(not self._conanfile.settings.get_safe("build_type", True))
        }


class PyProjectToolchain:
    filename = Path("pyproject.toml")

    _template = textwrap.dedent("""
    # Conan automatically generated pyproject.toml file
    # DO NOT EDIT MANUALLY, it will be overwritten

    {% for conan_block in conan_blocks %}
    {{ conan_block }}
    {% endfor %}
    """)

    def __init__(self, conanfile: ConanFile):
        self._conanfile: ConanFile = conanfile
        self.blocks = ToolchainBlocks(self._conanfile, self, [
            ("build_system", BuildSystemBlock),
            ("tool_sip_metadata", ToolSipMetadataBlock),
            ("tool_sip_project", ToolSipProjectBlock),
            ("tool_sip_bindings", ToolSipBindingsBlock),
            ("extra_sources", ToolSipBindingsExtraSourcesBlock)
        ])

        check_using_build_profile(self._conanfile)

    @property
    def _context(self):
        blocks = self.blocks.process_blocks()
        return {"conan_blocks": blocks}

    @property
    def content(self):
        content = Template(self._template, trim_blocks = True, lstrip_blocks = True).render(**self._context)
        return content

    def generate(self):
        filename = Path(self._conanfile.generators_folder).joinpath(self.filename)
        save(self._conanfile, filename, self.content)


class PyProjectToolchainPkg(ConanFile):
    name = "pyprojecttoolchain"
    version = "0.1.0"
    default_user = "ultimaker"
    default_channel = "testing"
