from pathlib import Path
import json
import time
import collections
from typing import List, Any, Set

from conan import ConanFile
from conan.tools.files import save, load, rm


# Part of this script generates a POT file from a JSON settings file. It
# has been adapted from createjsoncontext.py of KDE's translation
# scripts. It extracts the "label" and "description" values of
# the JSON file using the structure as used by Uranium settings files.
# Copyright 2014  Burkhard Lück <lueck@hube-lueck.de>


class ExtractTranslations(object):
    def __init__(self, conanfile: ConanFile):
        self._conanfile = conanfile
        self._translations_root_path = Path(self._conanfile.source_folder).joinpath("resources", "i18n")
        self._all_strings_pot_path = self._translations_root_path.joinpath(
            self._conanfile.name + ".pot")  # pot file containing all strings untranslated
        self._pot_content = {}
        self._pot_are_updated = False

    def _update_po_files_all_languages(self) -> None:
        """ Updates all po files in translation_root_path with new strings mapped to blank translations."""
        for pot_file in Path(self._translations_root_path).rglob("*.pot"):
            for lang_folder in [d for d in self._translations_root_path.iterdir() if d.is_dir()]:
                po_file = lang_folder / pot_file.with_suffix('.po').name
                self._conanfile.output.info(f"Updating {po_file}")
                if lang_folder.is_dir() and not po_file.exists():
                    po_file.touch()
                    self._conanfile.run(
                        f"msginit --no-translator -i {pot_file} -o {po_file} --locale=en", env="conanbuild")
                self._conanfile.run(
                    f"msgmerge --add-location=never --no-wrap --no-fuzzy-matching --sort-output -o {po_file} {po_file} {pot_file}",
                    env="conanbuild")

    def _remove_pot_header(self, content: str) -> str:
        return "".join(content.splitlines(keepends=True)[20:])

    def _remove_comments(self, content: str) -> str:
        return "".join([line for line in content.splitlines(keepends=True) if not line.startswith("#")])

    def _load_pot_content(self) -> None:
        for pot_file in Path(self._translations_root_path).rglob("*.pot"):
            # only store the content of the pot file, not the header
            self._pot_content[str(pot_file)] = load(self._conanfile, str(pot_file))

    def _is_pot_content_changed(self, pot_file: str) -> bool:
        if pot_file not in self._pot_content:
            return False
        return self._remove_comments(self._remove_pot_header(self._pot_content[pot_file])) != self._remove_comments(
            self._remove_pot_header(load(self._conanfile, pot_file)))

    def _only_update_pot_files_when_changed(self) -> None:
        """restore the previous content of the pot files if the content hasn't changed"""
        for pot_file in Path(self._translations_root_path).rglob("*.pot"):
            if self._is_pot_content_changed(str(pot_file)):
                self._pot_are_updated = True
            elif str(pot_file) in self._pot_content:
                save(self._conanfile, str(pot_file), self._pot_content[str(pot_file)])

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

    def _extract_source_files(self, prefix, extension_wildcard):
        source_files = []

        key = f"{prefix}_translation_source_folders"
        if self._conanfile.conan_data is not None and key in self._conanfile.conan_data:
            for translation_folder in self._conanfile.conan_data[key]:
                source_files += Path(self._conanfile.source_folder, translation_folder).rglob(extension_wildcard)

        return source_files

    def _extract_python(self) -> None:
        """ Extract i18n strings from all .py files"""
        for path in self._extract_source_files("python", "*.py"):
            self._conanfile.run(
                f"xgettext --from-code=UTF-8 --join-existing --add-location=never --sort-output --language=python --no-wrap -ki18n:1 -ki18nc:1c,2 -ki18np:1,2 -ki18ncp:1c,2,3 -o {self._all_strings_pot_path} {path}",
                env="conanbuild")

    def _extract_qml(self) -> None:
        """ Extract all i18n strings from qml files"""
        for path in self._extract_source_files("qml", "*.qml"):
            self._conanfile.run(
                f"xgettext --from-code=UTF-8 --join-existing --add-location=never --sort-output --language=javascript --no-wrap -ki18n:1 -ki18nc:1c,2 -ki18np:1,2 -ki18ncp:1c,2,3 -o {self._all_strings_pot_path} {path}",
                env="conanbuild")

    def _extract_plugin(self) -> None:
        """ Extract the name and description from all plugins """
        plugin_paths = [path for path in Path(self._conanfile.source_folder).rglob("plugin.json") if "test" not in str(path)]
        for path in plugin_paths:
            translation_entries = ""

            # Extract translations from plugin.json
            plugin_dict = json.loads(load(self._conanfile, path), object_pairs_hook=collections.OrderedDict)
            if "name" not in plugin_dict or (
                    "api" not in plugin_dict and "supported_sdk_versions" not in plugin_dict) or "version" not in plugin_dict:
                self._conanfile.output.warn(f"The plugin.json is invalid, ignoring it: {path}")
            else:
                if "description" in plugin_dict:
                    translation_entries += self._create_translation_entry("description", plugin_dict["description"])
                if "name" in plugin_dict:
                    translation_entries += self._create_translation_entry("name", plugin_dict["name"])

            # Write plugin name & description to output pot file
            if translation_entries:
                save(self._conanfile, self._all_strings_pot_path, translation_entries, append=True)

    def _extract_settings(self) -> None:
        """ Extract strings from settings json files to pot file with a matching name """
        setting_json_paths = [path for path in self._conanfile.source_path.rglob("*.def.json") if "test" not in str(path)]
        setting_json_data = []
        for json_path in setting_json_paths:
            setting_dict = json.loads(load(self._conanfile, json_path), object_pairs_hook = collections.OrderedDict)
            setting_json_data.append((json_path, setting_dict))

        variants_names = self._extract_variants_names(setting_json_data)
        for json_path, setting_dict in setting_json_data:
            self._write_setting_text(json_path, setting_dict, self._translations_root_path, variants_names)

    def _extract_variants_names(self, setting_json_data: List[tuple[Path, dict[str, Any]]]) -> Set[str]:
        """ Extract all existing variants from settings json files """
        variants_names = set()

        for _, setting_dict in setting_json_data:
            if "metadata" in setting_dict:
                setting_metadata = setting_dict["metadata"]

                variants_name = None
                if "variants_name" in setting_metadata:
                    variants_name = setting_metadata["variants_name"]

                variants_name_has_translation = None
                if "variants_name_has_translation" in setting_metadata:
                    variants_name_has_translation = setting_metadata["variants_name_has_translation"]

                if variants_name is not None and variants_name_has_translation == True:
                    variants_names.add(variants_name)

        return variants_names

    def _write_setting_text(self, json_path: Path, setting_dict: dict[str, Any], destination_path: Path, variants_names: Set[str]) -> bool:
        """ Writes settings text from json file to pot file. Returns true if a file was written. """
        if "inherits" not in setting_dict:
            if "settings" in setting_dict:
                settings = setting_dict["settings"]
            else:
                settings = setting_dict

            translation_entries = self._process_settings(settings)

            if json_path.name == "fdmprinter.def.json":
                translation_entries += self._process_variants_names(variants_names)

            output_pot_path = Path(destination_path).joinpath(
                json_path.name + ".pot")  # Create a pot with a matching filename in the destination path
            content = self._create_pot_header() + translation_entries
            save(self._conanfile, output_pot_path, content)
            return True
        return False

    def _process_variants_names(self, variants_names: Set[str]) -> str:
        translation_entries = ""

        for variant_name in variants_names:
            translation_entries += self._create_translation_entry("variant_name", variant_name)

        return translation_entries

    def _process_settings(self, settings) -> str:
        translation_entries = ""

        for name, value in settings.items():
            if "label" in value:
                translation_entries += self._create_setting_translation_entry(name, "label", value["label"])
            if "description" in value:
                translation_entries += self._create_setting_translation_entry(name, "description", value["description"])
            if "warning_description" in value:
                translation_entries += self._create_setting_translation_entry(name, "warning_description", value["warning_description"])
            if "error_description" in value:
                translation_entries += self._create_setting_translation_entry(name, "error_description", value["error_description"])
            if "options" in value:
                for item, description in value["options"].items():
                    translation_entries += self._create_setting_translation_entry(name, "option {0}".format(item), description)
            if "children" in value:
                translation_entries += self._process_settings(value["children"])

        return translation_entries

    def _create_setting_translation_entry(self, setting: str, field: str, value: str) -> str:
        return "msgctxt \"{0} {1}\"\nmsgid \"{2}\"\nmsgstr \"\"\n\n".format(setting, field, value.replace("\n", "\\n").replace("\"", "\\\""))

    def _create_translation_entry(self, field: str, value: str) -> str:
        return "\nmsgctxt \"{0}\"\nmsgid \"{1}\"\nmsgstr \"\"\n".format(field, value.replace("\n", "\\n").replace("\"", "\\\""))

    def _create_pot_header(self) -> str:
        """ Creates a pot file header """
        header = "#\n"
        header += "msgid \"\"\n"
        header += "msgstr \"\"\n"
        header += "\"Project-Id-Version: Uranium json setting files\\n\"\n"
        header += "\"Report-Msgid-Bugs-To: it@lulzbot.com\\n\"\n"
        header += "\"POT-Creation-Date: {}+0000\\n\"\n".format(time.strftime("%Y-%m-%d %H:%M"))
        header += "\"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n\"\n"
        header += "\"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n\"\n"
        header += "\"Language-Team: LANGUAGE\\n\"\n"
        header += "\"MIME-Version: 1.0\\n\"\n"
        header += "\"Content-Type: text/plain; charset=UTF-8\\n\"\n"
        header += "\"Content-Transfer-Encoding: 8bit\\n\"\n"
        header += "\n"
        header += "\n"
        header += "\n"
        header += "\n"
        header += "\n"
        header += "\n"
        return header

    def _sanitize_pot_files(self) -> None:
        """ Sanitize all pot files """
        for path in self._translations_root_path.rglob("*.pot"):
            content = load(self._conanfile, path)
            if "msgctxt" not in content:
                self._conanfile.output.warn(f"Removing empty pot file: {path}")
                rm(self._conanfile, path.name, path.parent)
            else:
                save(self._conanfile, path,
                     content.replace(f"#: {self._conanfile.source_folder}/", "#: ").replace("charset=CHARSET", "charset=UTF-8"))

    def generate(self):
        self._load_pot_content()
        self._extract_strings_to_pot_files()
        self._sanitize_pot_files()
        self._only_update_pot_files_when_changed()
        if self._pot_are_updated:
            self._conanfile.output.info("Translation Templates contain new strings. Updating po files...")
            self._update_po_files_all_languages()


class Pkg(ConanFile):
    name = "translationextractor"

    def package_info(self):
        self.cpp_info.set_property("name", "translationextractor")
