import argparse
import collections
import json
import os
import subprocess
import logging
import time

from pathlib import Path
from settingspot import write_setting_text


logger = logging.Logger("ExtractStrings")

class TranslationExtractor:
    def __init__(self, root_path: Path, translations_root_path: Path, all_strings_pot_name: str, gettext_path: str = ""):
        """ Extracts all strings into a pot file with empty translations then merges that pot file with all po files.

        @param root_path: The root path of the project. All files in this folder will be searched for strings.
        @param translations_root_path: The root of the translations folder (resources/i18n).
        @param all_strings_pot_name: The name of the pot file where all strings will be outputted (cura.pot).
        """
        self.root_path = root_path
        self.translations_root_path = translations_root_path
        self.all_strings_pot_path = Path(translations_root_path).joinpath(all_strings_pot_name)  # pot file containing all strings untranslated
        self.gettext_path = gettext_path

        if self.gettext_path:
            self.gettext_path = self.gettext_path + os.path.sep

        # Clear output file
        open(self.all_strings_pot_path, "w", encoding ="utf-8").close()

    def extract_strings_to_pot_files(self) -> None:
        """
        Extracts all strings into a pot file with empty translations. Strings are extracted everywhere that i18n is
        used in python and qml in the project. It also checks the project for JSON files with 'settings' in the root node
        and extracts these for translation as well.
        """

        self.extract_python()
        self.extract_qml()
        self.extract_plugin()
        self.extract_settings()

    def update_po_files_all_languages(self) -> None:
        """ Updates all po files in translation_root_path with new strings mapped to blank translations."""
        for pot_file in Path(self.translations_root_path).rglob("*.pot"):
            for po_file in Path(self.translations_root_path).rglob(str(pot_file.with_suffix(".po").name)):
                print(f"Updating {po_file} with {pot_file}...")
                merge_files_arguments = [
                    self.gettext_path + "msgmerge",
                    "--no-wrap",
                    "--no-fuzzy-matching",
                    "--update",
                    "--sort-by-file",  # Sort by file location, this is better than pure sorting for translators
                    po_file,  # po file that will be updated
                    pot_file  # source of new strings
                ]

                if logger.level != logging.DEBUG:
                    merge_files_arguments.append("-q")

                subprocess.run(merge_files_arguments)

    def extract_python(self) -> None:
        """ Extract i18n strings from all .py files in root_path"""
        for path in self.root_path.rglob("*.py"):
            if "venv" in path.parts:
                continue
            logger.debug(f"Extracting strings from python file: {path}")

            extract_python_strings_arguments = [
                self.gettext_path + "xgettext",
                "--from-code=UTF-8",
                "--join-existing",
                "--sort-by-file",
                "--language=python",
                "--no-wrap",
                "-ki18n:1", "-ki18nc:1c,2", "-ki18np:1,2", "-ki18ncp:1c,2,3",
                "-o", self.all_strings_pot_path,
                path
            ]

            subprocess.run(extract_python_strings_arguments)


    def extract_qml(self) -> None:
        """ Extract all i18n strings from qml files inside the root path """
        for path in self.root_path.rglob("*.qml"):
            logger.debug(f"Extracting strings from qml file: {path}")

            extract_python_strings_arguments = [
                self.gettext_path + "xgettext",
                "--from-code=UTF-8",
                "--join-existing",
                "--sort-by-file",
                "--language=javascript",
                "--no-wrap",
                "-ki18n:1", "-ki18nc:1c,2", "-ki18np:1,2", "-ki18ncp:1c,2,3",
                "-o", self.all_strings_pot_path,
                path
            ]

            subprocess.run(extract_python_strings_arguments)

    def extract_settings(self) -> None:
        """ Extract strings from settings json files to pot file with a matching name """
        setting_json_paths = [path for path in self.root_path.rglob("*.json") if "test" not in str(path)]
        for path in setting_json_paths:
            write_setting_text(path, self.translations_root_path)

    def extract_plugin(self) -> None:
        """ Extract the name and description from all plugins """
        plugin_paths = [path for path in self.root_path.rglob("plugin.json") if "test" not in str(path)]
        for path in plugin_paths:
            translation_entries = ""

            # Extract translations from plugin.json
            with open(path, "r", encoding="utf-8") as data_file:
                plugin_dict = json.load(data_file, object_pairs_hook=collections.OrderedDict)

                if "name" not in plugin_dict or ("api" not in plugin_dict and "supported_sdk_versions" not in plugin_dict) or "version" not in plugin_dict:
                    logger.debug(f"The plugin.json is invalid, ignoring it: {path}")
                else:
                    if "description" in plugin_dict:
                        translation_entries += self.create_translation_entry(path.name, "description", plugin_dict["description"])
                    if "name" in plugin_dict:
                        translation_entries += self.create_translation_entry(path.name, "name", plugin_dict["name"])

            # Write plugin name & description to output pot file
            if translation_entries:
                with open(self.all_strings_pot_path, "a", encoding="utf-8") as output_file:
                    logger.debug(f"Writing plugin strings for file: {path}")
                    output_file.write(translation_entries)

    def create_translation_entry(self, filename: str, field: str, value: str) -> str:
        return "#: {0}\nmsgctxt \"{1}\"\nmsgid \"{2}\"\nmsgstr \"\"\n\n".format(filename, field, value.replace("\n", "\\n").replace("\"", "\\\""))

    def sanitize_pot_files(self) -> None:
        """ Sanitize the pot file """
        for pot_file in Path(self.translations_root_path).rglob("*.pot"):
            content = ""
            with open(pot_file, "r", encoding="utf-8") as input_file:
                content = input_file.read()

            content = content.replace(f"#: {self.root_path}/", "#: ").replace("charset=CHARSET", "charset=UTF-8")
            with open(pot_file, "w", encoding="utf-8") as output_file:
                output_file.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract strings from project into .po files")
    parser.add_argument("root_path", type=str, help="The root of the project to extract translatable strings from")
    parser.add_argument("translations_root_path", type=str, help="The path containing folders labeled by lang code (resoures/i18n)")
    parser.add_argument("translation_template_name", type=str, help="The .pot file that all extracted strings will be inserted into")
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG)

    extractor = TranslationExtractor(Path(args.root_path), Path(args.translations_root_path), args.translation_template_name)
    extractor.extract_strings_to_pot_files()
    extractor.sanitize_pot_files()
    extractor.update_po_files_all_languages()
