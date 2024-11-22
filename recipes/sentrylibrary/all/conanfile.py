from conan import ConanFile

from pathlib import Path
from shutil import which

from conan.errors import ConanInvalidConfiguration, ConanException

required_conan_version = ">=2.7.0"


class SentryLibrary:
    options = {
        "enable_sentry": [True, False],
        "sentry_create_release": [True, False],
        "sentry_project": ["ANY"],
    }
    default_options = {
        "enable_sentry": False,
        "sentry_create_release": False,
        "sentry_project": "",
    }

    def config_options(self):
        if self.options.sentry_project == "":
            self.options.sentry_project = self.name

    def configure(self):
        if self.options.enable_sentry:
            self.options["sentry-native"].backend = "breakpad"

    def validate(self):
        if self.options.enable_sentry:
            for sentry_conf in ["organization", "url", "token"]:
                conf_name = f"user.sentry:{sentry_conf}"
                if self.conf.get(conf_name, "", check_type=str) == "":
                    raise ConanInvalidConfiguration(f"Unable to enable Sentry because no {conf_name} was configured (use '-c {conf_name}={sentry_conf}')")

    def requirements(self):
        if self.options.enable_sentry:
            self.requires("sentry-native/0.7.0")

    def setup_cmake_toolchain_sentry(self, cmake_toolchain):
        '''
        Method to be called by actual packages at generate() time to setup the cmake toolchain according to the sentry configuration
        '''
        cmake_toolchain.variables["ENABLE_SENTRY"] = self.options.enable_sentry
        cmake_toolchain.variables["SENTRY_URL"] = self.conf.get("user.sentry:url", "", check_type=str)

    def send_sentry_debug_files(self, binary_basename):
        '''
        Method to be called by actual packages at build() time, after the actual build has been done, to send the binary files to sentry
        '''
        if self.options.enable_sentry:
            sentry_project = self.options.sentry_project
            sentry_organization = self.conf.get("user.sentry:organization", "", check_type=str)
            sentry_token = self.conf.get("user.sentry:token", "", check_type=str)

            if which("sentry-cli") is None:
                raise ConanException("sentry-cli is not installed, unable to upload debug symbols")

            if self.package_type == "application":
                binary_name = binary_basename
            else:
                binary_name = binary_basename + ('.so' if self.options.get_safe("shared", True) else '.a')

            if self.settings.os == "Linux":
                self.output.info("Stripping debug symbols from binary")
                self.run(f"objcopy --only-keep-debug --compress-debug-sections=zlib {binary_name} {binary_name}.debug")
                self.run(f"objcopy --strip-debug --strip-unneeded {binary_name}")
                self.run(f"objcopy --add-gnu-debuglink={binary_name}.debug {binary_name}")
            elif self.settings.os == "Macos":
                self.run(f"dsymutil {binary_name}")

            self.output.info("Uploading debug symbols to sentry")
            build_source_dir = Path(self.build_folder).parent.parent.as_posix()
            self.run(
                f"sentry-cli --auth-token {sentry_token} debug-files upload --include-sources -o {sentry_organization} -p {sentry_project} {build_source_dir}")

            if self.sentry_create_release:
                # create a sentry release and link it to the commit this is based upon
                self.output.info(f"Creating a new release {self.version} in Sentry and linking it to the current commit {self.conan_data['commit']}")
                self.run(f"sentry-cli --auth-token {sentry_token} releases new -o {sentry_organization} -p {sentry_project} {self.version}")
                self.run(f"sentry-cli --auth-token {sentry_token} releases set-commits -o {sentry_organization} -p {sentry_project} --commit \"Ultimaker/CuraEngine@{self.conan_data['commit']}\" {self.version}")
                self.run(f"sentry-cli --auth-token {sentry_token} releases finalize -o {sentry_organization} -p {sentry_project} {self.version}")


class PyReq(ConanFile):
    name = "sentrylibrary"
    description = "This is a base conan file description for C++ libraries/applications that can embed sentry"
    package_type = "python-require"
