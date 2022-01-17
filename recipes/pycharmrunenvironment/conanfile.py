import os
from copy import deepcopy
from jinja2 import Template

from conans import ConanFile
from conans.tools import save
from conan.tools.env import Environment
from conan.tools.env.virtualrunenv import VirtualRunEnv


class PyCharmRunEnvironment(VirtualRunEnv):
    """
    Creates a Pycharm.run.xml file based on the jinja template in .conan_gen where all environment variables are set,
    defined in the dependencies and in the current conanfile.

    The conan file needs to have a list called pycharm_targets with dicts (with the following struct::

        pycharm_targets = [
            {
                "jinja_path": str(os.path.join(pathlib.Path(__file__).parent.absolute(), ".conan_gen", "<TemplateFile>.run.xml.jinja")),
                "name": "<Name of the run file>",
                "entry_point": "<target it needs to run>",
                "arguments": "<extra command line arguments>"
            }
        ]
    """

    def generate(self, run_env = Environment(), scope = "run"):
        run_env.compose_env(self.environment())
        if run_env:
            if not hasattr(self._conanfile, "pycharm_targets"):
                self._conanfile.output.error("pycharm_targets not set in conanfile.py")
                return
            for ref_target in getattr(self._conanfile, "pycharm_targets"):
                target = deepcopy(ref_target)
                jinja_path = target.pop("jinja_path")
                with open(jinja_path, "r") as f:
                    tm = Template(f.read())
                    result = tm.render(env_vars = run_env.vars(self._conanfile, scope=scope), **target)
                    file_name = f"{target['name']}.run.xml"
                    path = os.path.join(target['run_path'], file_name)
                    save(path, result)
                    self._conanfile.output.info(f"PyCharm run file created: {path}")



class Pkg(ConanFile):
    name = "PyCharmRunEnvironment"
    version = "0.1"
    default_user = "ultimaker"
    default_channel = "testing"
