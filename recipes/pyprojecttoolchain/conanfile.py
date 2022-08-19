import textwrap
from pathlib import Path

from jinja2 import Template

from conan import ConanFile
from conan.tools.microsoft import VCVars
from conan.tools.cmake.toolchain.blocks import Block
from conan.tools.cmake.toolchain.toolchain import ToolchainBlocks
from conan.tools.gnu.autotoolstoolchain import AutotoolsToolchain
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
            try:
                python_version = self._conanfile.dependencies["cpython"].ref.version
            except:
                raise ConanInvalidConfiguration(
                    "No minimum required Python version specified, either add the options: 'py_version' of add cpython as a Conan dependency!")

        mod_version = Version(self._conanfile.version)
        pypi_version = f"{mod_version.major}.{mod_version.minor}.{mod_version.patch}"
        if mod_version.prerelease != "":
            split_prerelease = mod_version.prerelease.split(".")
            if len(split_prerelease) > 1:
                pypi_version += f"{split_prerelease[0][0]}{split_prerelease[1]}"
            else:
                pypi_version += split_prerelease[0][0]

        return {
            "name": self._conanfile.name,
            "version": pypi_version,
            "description": self._conanfile.description,
            "url": self._conanfile.url,
            "author": self._conanfile.author,
            "license": self._conanfile.license,
            "python_version": python_version
        }


class ToolSipProjectBlock(Block):
    template = textwrap.dedent("""
    [tool.sip.project]
    builder-factory = "{{ builder_factory }}"
    sip-files-dir = "{{ sip_files_dir }}"
    build-dir = "{{ build_folder }}"
    target-dir = "{{ package_folder }}"
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
            try:
                python_version = self._conanfile.dependencies["cpython"].ref.version
            except:
                self._conanfile.output.warn(
                    "No minimum required Python version specified, either add the options: 'py_version' of add cpython as a Conan dependency!")

        if python_version is not None:
            py_version = Version(python_version)
            py_major_version = py_version.major
            py_minor_version = py_version.minor

            if py_include_dir is None:
                try:
                    py_include_dir = Path(self._conanfile.deps_cpp_info['cpython'].rootpath,
                                          self._conanfile.deps_cpp_info['cpython'].includedirs[0],
                                          f"python{py_major_version}.{py_minor_version}").as_posix()
                    py_include_dir = f"py-include-dir = \"{py_include_dir}\""
                except:
                    self._conanfile.output.warn(
                        "No include directory set for Python.h, either add the options: 'py_include' of add cpython as a Conan dependency!")
            else:
                py_include_dir = f"py-include-dir = \"{Path(py_include_dir).as_posix()}\""

            py_major_version = f"py-major-version = {py_version.major}"
            py_minor_version = f"py-minor-version = {py_version.minor}"

        if self._conanfile.package_folder:
            package_folder = Path(self._conanfile.package_folder, "site-packages").as_posix()
        else:
            package_folder = Path(self._conanfile.build_folder, "site-packages").as_posix()
        sip_files_dir = Path(self._conanfile.source_folder, self._conanfile.name).as_posix()

        return {
            "builder_factory": Path(self._conanfile.generators_folder, "cpp_builder.py").as_posix(),
            "sip_files_dir": sip_files_dir,
            "build_folder": Path(self._conanfile.build_folder).as_posix(),
            "package_folder": package_folder,
            "py_include_dir": py_include_dir,
            "py_major_version": py_major_version,
            "py_minor_version": py_minor_version
        }


class ToolSipBindingsExtraSourcesBlock(Block):
    template = textwrap.dedent("""
    headers = {{ headers }}
    sources = {{ sources }}
    """)

    def context(self):
        return {
            "headers": [],
            "sources": []
        }


class ToolSipBindingBlockCompile(Block):
    template = textwrap.dedent("""
    extra-compile-args = {{ compileargs }}
    extra-link-args = {{ linkargs }}
    """)

    def context(self):
        return {
            "compileargs": list(filter(lambda item: item is not None and item != '', self._toolchain.cxxflags)),
            "linkargs":  list(filter(lambda item: item is not None and item != '', self._toolchain.ldflags)),
        }


class ToolSipBindingsBlock(Block):
    template = textwrap.dedent("""
    [tool.sip.bindings.{{ name }}]
    exceptions = true
    release-gil = true
    libraries = {{ libs }}
    library-dirs = {{ libdirs }}
    include-dirs = {{ includedirs }}
    pep484-pyi = true
    static = {{ build_static | lower }}
    debug = {{ build_debug | lower }}
    """)

    def context(self):
        settings = self._conanfile.settings
        deps_cpp_info = self._conanfile.deps_cpp_info
        build_type = settings.get_safe("build_type", "Release")
        shared = settings.get_safe("shared", True)

        libs = deps_cpp_info.libs
        libdirs = [Path(d).as_posix() for d in deps_cpp_info.libdirs]
        includedirs = [Path(d).as_posix() for d in deps_cpp_info.includedirs]
        if self._conanfile.cpp.source.includedirs:
            includedirs.extend(self._conanfile.cpp.source.includedirs)

        return {
            "name": self._conanfile.name,
            "libs": libs,
            "libdirs": libdirs,
            "includedirs": includedirs,
            "build_static": str(not shared),
            "build_debug": str(build_type == "Debug")
        }


class PyProjectToolchain(AutotoolsToolchain):
    _pyproject_filename = Path("pyproject.toml")

    _pyproject_template = textwrap.dedent("""
    # Conan automatically generated pyproject.toml file
    # DO NOT EDIT MANUALLY, it will be overwritten

    {% for conan_block in conan_blocks %}{{ conan_block }}
    {% endfor %}
    """)

    _sip_builder_filename = Path("cpp_builder.py")

    _sip_builder_template = textwrap.dedent("""
    # Conan automatically generated pyproject.toml file
    # DO NOT EDIT MANUALLY, it will be overwritten
    from sipbuild.setuptools_builder import SetuptoolsBuilder


    class CppBuilder(SetuptoolsBuilder):
        def __init__(self, project, **kwargs):
            print("Using the CppBuilder")
            super().__init__(project, **kwargs)
    
        def _build_extension_module(self, buildable):
            buildable.sources = [b for b in buildable.sources if str(b).endswith(".cpp")]
            super(CppBuilder, self)._build_extension_module(buildable)
    """)

    def __init__(self, conanfile: ConanFile, namespace = None):
        super().__init__(conanfile, namespace)
        check_using_build_profile(self._conanfile)
        self.blocks = ToolchainBlocks(self._conanfile, self, [
            ("build_system", BuildSystemBlock),
            ("tool_sip_metadata", ToolSipMetadataBlock),
            ("tool_sip_project", ToolSipProjectBlock),
            ("tool_sip_bindings", ToolSipBindingsBlock),
            ("extra_sources", ToolSipBindingsExtraSourcesBlock),
            ("compiling", ToolSipBindingBlockCompile),
        ])

    @property
    def _context(self):
        blocks = self.blocks.process_blocks()
        print(blocks)
        return {"conan_blocks": blocks}

    @property
    def content(self):
        content = Template(self._pyproject_template, trim_blocks = True, lstrip_blocks = True).render(**self._context)
        return content

    def generate(self, env = None, scope = "build"):
        env = env or self.environment()
        env = env.vars(self._conanfile, scope = scope)
        env.save_script("conanpyprojecttoolchain")
        VCVars(self._conanfile).generate(scope = scope)

        py_project_filename = Path(self._conanfile.source_folder, self._pyproject_filename)
        save(self._conanfile, py_project_filename, self.content)

        sip_builder_filename = Path(self._conanfile.generators_folder, self._sip_builder_filename)
        save(self._conanfile, sip_builder_filename, self._sip_builder_template)


class PyProjectToolchainPkg(ConanFile):
    name = "pyprojecttoolchain"
    version = "0.1.4"
    default_user = "ultimaker"
    default_channel = "testing"
