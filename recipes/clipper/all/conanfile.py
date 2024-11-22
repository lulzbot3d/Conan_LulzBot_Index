import os

from shutil import which

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=1.54.0"


class ClipperConan(ConanFile):
    name = "clipper"
    description = "Clipper is an open source freeware polygon clipping library"
    license = "BSL-1.0"
    topics = ("clipping", "polygon")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.angusj.com/delphi/clipper.php"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_sentry": [True, False],
        "sentry_project": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_sentry": False,
        "sentry_project": name,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.options.enable_sentry:
            for sentry_setting in ["organization", "token"]:
                if self.conf.get(f"user.sentry:{sentry_setting}", "", check_type=str) == "":
                    raise ConanInvalidConfiguration(f"Unable to enable Sentry because no {sentry_setting} was configured")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def generate(self):
        tc = CMakeToolchain(self)
        # Export symbols for msvc shared
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        # To install relocatable shared libs on Macos
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0042"] = "NEW"
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "cpp"))
        cmake.build()

        sentry_project = self.options.sentry_project
        sentry_organization = self.conf.get("user.sentry:organization", "", check_type=str)
        sentry_token = self.conf.get("user.sentry:token", "", check_type=str)
        if self.options.enable_sentry:
            if which("sentry-cli") is None:
                raise ConanException("sentry-cli is not installed, unable to upload debug symbols")

            if self.settings.os == "Linux":
                self.output.info("Stripping debug symbols from binary")
                ext = ".so" if self.options.shared else ".a"
                self.run(f"objcopy --only-keep-debug --compress-debug-sections=zlib libpolyclipping{ext} libpolyclipping.debug")
                self.run(f"objcopy --strip-debug --strip-unneeded libpolyclipping{ext}")
                self.run(f"objcopy --add-gnu-debuglink=libpolyclipping.debug libpolyclipping{ext}")

            build_source_dir = self.build_path.parent.parent.as_posix()
            self.output.info("Uploading debug symbols to sentry")
            self.run(f"sentry-cli --auth-token {sentry_token} debug-files upload --include-sources -o {sentry_organization} -p {sentry_project} {build_source_dir}")

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
