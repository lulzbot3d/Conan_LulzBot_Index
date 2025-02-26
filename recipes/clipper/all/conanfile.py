import os

from shutil import which

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=2.7.0"


class ClipperConan(ConanFile):
    name = "clipper"
    description = "Clipper is an open source freeware polygon clipping library"
    license = "BSL-1.0"
    topics = ("clipping", "polygon")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.angusj.com/delphi/clipper.php"
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    python_requires = "sentrylibrary/1.0.0"
    python_requires_extend = "sentrylibrary.SentryLibrary"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def init(self):
        base = self.python_requires["sentrylibrary"].module.SentryLibrary
        self.options.update(base.options, base.default_options)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        super().config_options()

        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        super().configure()

        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def generate(self):
        tc = CMakeToolchain(self)
        # Export symbols for msvc shared
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        # To install relocatable shared libs on Macos
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        self.setup_cmake_toolchain_sentry(tc)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "cpp"))
        cmake.build()

        self.send_sentry_debug_files(binary_basename = "libpolyclipping")

    def package(self):
        copy(self, "License.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "polyclipping")
        self.cpp_info.libs = ["polyclipping"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")

        # TODO: to remove in conan v2 once cmake_find_package* & pkg_config generators removed.
        #       Do not use these CMake names in CMakeDeps, it was a mistake,
        #       clipper doesn't provide CMake config file
        self.cpp_info.names["cmake_find_package"] = "polyclipping"
        self.cpp_info.names["cmake_find_package_multi"] = "polyclipping"
