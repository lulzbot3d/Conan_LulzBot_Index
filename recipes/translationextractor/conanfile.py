from pathlib import Path
import os
import json
import logging
import time
import collections

from conan import ConanFile
from conan.tools.files import save, load


# Part of this script generates a POT file from a JSON settings file. It
# has been adapted from createjsoncontext.py of KDE's translation
# scripts. It extracts the "label" and "description" values of
# the JSON file using the structure as used by Uranium settings files.
# Copyright 2014  Burkhard Lück <lueck@hube-lueck.de>


class ExtractTranslations(object):
    def __init__(self, conanfile: ConanFile):
        self._conanfile = conanfile
        self._translations_root_path = self._conanfile.source_path.joinpath("resources", "i18n")
        self._gettext_path = self._conanfile.dependencies["gettext"].cpp_info.bindirs[0]
        self._all_strings_pot_path = self._translations_root_path.joinpath(self._conanfile.name + ".pot")  # pot file containing all strings untranslated

    def _update_po_files_all_languages(self) -> None:
        """ Updates all po files in translation_root_path with new strings mapped to blank translations."""
        for pot_file in Path(self._translations_root_path).rglob("*.pot"):
            for po_file in Path(self._translations_root_path).rglob(str(pot_file.with_suffix(".po").name)):
                self._conanfile.output.info(f"Updating {po_file} with {pot_file}...")
                self._conanfile.run(
                    f"{os.path.join(self._gettext_path, 'msgmerge')} --no-wrap --no-fuzzy-matching --sort-by-file -o {po_file} {po_file} {pot_file}",
                    env="conanbuild")

    def _extract_strings_to_pot_files(self) -> None:
        """
        Extracts all strings into a pot file with empty translations. Strings are extracted everywhere that i18n is
        used in python and qml in the project. It also checks the project for JSON files with 'settings' in the root node
        and extracts these for translation as well.
        """
        save(self._conanfile, self._all_strings_pot_path, "")  # Clear output file

        self._extract_python()
        self._extract_qml()
        self._extract_plugin()
        self._extract_settings()

    def _extract_python(self) -> None:
        """ Extract i18n strings from all .py files in root_path"""
        for path in self._conanfile.source_path.rglob("*.py"):
            if "venv" in path.parts:
                continue
            self._conanfile.output.info(f"Extracting python strings from {path}...")
            self._conanfile.run(
                f"{os.path.join(self._gettext_path, 'xgettext')} --from-code=UTF-8 --join-existing --sort-by-file --language=python --no-wrap -ki18n:1 -ki18nc:1c,2 -ki18np:1,2 -ki18ncp:1c,2,3 -o {self._all_strings_pot_path} {path}",
                env="conanbuild")

    def _extract_qml(self) -> None:
        """ Extract all i18n strings from qml files inside the root path """
        for path in self._conanfile.source_path.rglob("*.qml"):
            self._conanfile.output.info(f"Extracting python strings from {path}...")
            self._conanfile.run(
                f"{os.path.join(self._gettext_path, 'xgettext')} --from-code=UTF-8 --join-existing --sort-by-file --language=javascript --no-wrap -ki18n:1 -ki18nc:1c,2 -ki18np:1,2 -ki18ncp:1c,2,3 -o {self._all_strings_pot_path} {path}",
                env="conanbuild")

    def _extract_plugin(self) -> None:
        """ Extract the name and description from all plugins """
        plugin_paths = [path for path in self._conanfile.source_path.rglob("plugin.json") if "test" not in str(path)]
        for path in plugin_paths:
            translation_entries = ""

            # Extract translations from plugin.json
            with open(path, "r", encoding="utf-8") as data_file:
                plugin_dict = json.load(data_file, object_pairs_hook=collections.OrderedDict)

                if "name" not in plugin_dict or (
                        "api" not in plugin_dict and "supported_sdk_versions" not in plugin_dict) or "version" not in plugin_dict:
                    self._conanfile.output.warn(f"The plugin.json is invalid, ignoring it: {path}")
                else:
                    if "description" in plugin_dict:
                        translation_entries += self._create_translation_entry(path, "description",
                                                                              plugin_dict["description"])
                    if "name" in plugin_dict:
                        translation_entries += self._create_translation_entry(path, "name", plugin_dict["name"])

            # Write plugin name & description to output pot file
            if translation_entries:
                self._conanfile.output.info(f"Extracting plugin strings from {path}...")
                save(self._conanfile, self._all_strings_pot_path, translation_entries, append=True)

    def _extract_settings(self) -> None:
        """ Extract strings from settings json files to pot file with a matching name """
        setting_json_paths = [path for path in self._conanfile.source_path.rglob("*.json") if "test" not in str(path)]
        for path in setting_json_paths:
            self._write_setting_text(path, self._translations_root_path)

    def _write_setting_text(self, json_path: Path, destination_path: Path) -> bool:
        """ Writes settings text from json file to pot file. Returns true if a file was written. """
        translation_entries = ""
        with open(json_path, "r", encoding="utf-8") as data_file:
            setting_dict = json.load(data_file, object_pairs_hook=collections.OrderedDict)

            if "settings" not in setting_dict:
                self._conanfile.output.info(f"Nothing to translate in file: {json_path}")
            else:
                translation_entries = self._process_settings(json_path.name, setting_dict["settings"])

        if translation_entries:
            self._conanfile.output.info(f"Extracting setting strings from {json_path}...")
            output_pot_path = Path(destination_path).joinpath(
                json_path.name + ".pot")  # Create a pot with a matching filename in the destination path
            content = self._create_pot_header() + translation_entries
            save(self._conanfile, output_pot_path, content)
            return True
        return False

    def _process_settings(self, file, settings) -> str:
        translation_entries = ""
        for name, value in settings.items():
            if "label" in value:
                translation_entries += self._create_setting_translation_entry(file, name, "label", value["label"])
            if "description" in value:
                translation_entries += self._create_setting_translation_entry(file, name, "description", value["description"])
            if "warning_description" in value:
                translation_entries += self._create_setting_translation_entry(file, name, "warning_description",
                                                                      value["warning_description"])
            if "error_description" in value:
                translation_entries += self._create_setting_translation_entry(file, name, "error_description",
                                                                      value["error_description"])
            if "options" in value:
                for item, description in value["options"].items():
                    translation_entries += self._create_setting_translation_entry(file, name, "option {0}".format(item),
                                                                          description)
            if "children" in value:
                translation_entries += self._process_settings(file, value["children"])

        return translation_entries

    def _create_setting_translation_entry(self, filename: str, setting: str, field: str, value: str) -> str:
        return "#: {0}\nmsgctxt \"{1} {2}\"\nmsgid \"{3}\"\nmsgstr \"\"\n\n".format(filename, setting, field, value.replace("\n", "\\n").replace("\"", "\\\""))

    def _create_translation_entry(self, filename: str, field: str, value: str) -> str:
        return "#: {0}\nmsgctxt \"{1}\"\nmsgid \"{2}\"\nmsgstr \"\"\n\n".format(filename, field, value.replace("\n", "\\n").replace("\"", "\\\""))

    def _create_pot_header(self) -> str:
        """ Creates a pot file header """
        header = "#, fuzzy\n"
        header += "msgid \"\"\n"
        header += "msgstr \"\"\n"
        header += "\"Project-Id-Version: Uranium json setting files\\n\"\n"
        header += "\"Report-Msgid-Bugs-To: plugins@ultimaker.com\\n\"\n"
        header += "\"POT-Creation-Date: %s+0000\\n\"\n" % time.strftime("%Y-%m-%d %H:%M")
        header += "\"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n\"\n"
        header += "\"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n\"\n"
        header += "\"Language-Team: LANGUAGE\\n\"\n"
        header += "\"MIME-Version: 1.0\\n\"\n"
        header += "\"Content-Type: text/plain; charset=UTF-8\\n\"\n"
        header += "\"Content-Transfer-Encoding: 8bit\\n\"\n"
        header += "\n"
        return header

    def _sanitize_pot_files(self) -> None:
        """ Sanitize all pot files """
        for path in self._translations_root_path.rglob("*.pot"):
            save(self._conanfile, path, load(self._conanfile, path).replace(f"#: {self._conanfile.source_path}/", "#: ").replace("charset=CHARSET", "charset=UTF-8"))

    def generate(self):
        self._extract_strings_to_pot_files()
        self._sanitize_pot_files()
        self._update_po_files_all_languages()


class Pkg(ConanFile):
    name = "translationextractor"
    version = "2.0.0"
    default_user = "ultimaker"
    default_channel = "stable"

    def package(self):
        self.copy("*", ".")

    def package_info(self):
        self.cpp_info.set_property("name", "translationextractor")
