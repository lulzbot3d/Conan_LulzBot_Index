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


class Pkg(ConanFile):
    name = "UltimakerBase"
    version = "0.1"
    default_user = "ultimaker"
    default_channel = "testing"
