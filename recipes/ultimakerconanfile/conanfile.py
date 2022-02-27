import os

from conans import ConanFile, tools
from conans.errors import ConanException


class UltimakerBase(object):
    def set_version(self):
        # TODO: the current function doesn't handle previous versions as good as it should do
        git = tools.Git()
        branch = str(git.get_branch()).replace("conan/", "")  # FIXME: after the switch to Conan
        rev = git.get_commit()[:6]
        if branch == "master":  # we're on master
            self.version += f"-a+{rev}"
        else:
            try:
                branch_version = tools.Version(branch)
            except ConanException:
                branch_version = None
            if branch_version:  # We're on a release branch
                tag = git.get_tag()
                if tag:
                    try:
                        tag_version = tools.Version(tag)
                    except:
                        tag_version = None
                    if tag_version:  # We're on an actual release
                        self.version = f"{tag_version.major}.{tag_version.minor}.{tag_version.patch}"
                    else:  # We're on a beta branch
                        self.version = f"-b+{rev}"
            else:  # We're on development branch
                if "CURA-" in branch:
                    self.version += f"-a+{branch[5:9]}.{rev}"  # only use the Jira-ticket number
                else:
                    self.version += f"-a+{branch}.{rev}"  # only use rev

    def ultimaker_layout(self, include_dir = "src"):
        compiler = self.settings.get_safe("compiler")
        multi = compiler in ("Visual Studio", "msvc")

        self.folders.source = "."
        try:
            build_type = str(self.settings.build_type)
        except ConanException:
            raise ConanException("'build_type' setting not defined, it is necessary for cmake_layout()")
        if multi:
            self.folders.build = "build"
        else:
            comp = "" if compiler in ("gcc", "apple-clang") else f"-{compiler}"
            build_type = build_type.lower()
            self.folders.build = f"cmake-build-{build_type}{comp}"
        self.folders.generators = os.path.join(self.folders.build, "conan")
        self.cpp.source.includedirs = [include_dir]
        if multi:
            self.cpp.build.libdirs = [f"{build_type}"]
            self.cpp.build.bindirs = [f"{build_type}"]
        else:
            self.cpp.build.libdirs = ["."]
            self.cpp.build.bindirs = ["."]


class Pkg(ConanFile):
    name = "UltimakerBase"
    version = "0.2"
    default_user = "ultimaker"
    default_channel = "testing"
