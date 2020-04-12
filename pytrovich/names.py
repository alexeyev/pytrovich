# -*- coding: utf-8 -*-
import json

from pytrovich import rules_data
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.models import Root, Name, Rule


class PetrovichDeclinationMaker(object):
    DEFAULT_PATH_TO_RULES_FILE = None
    MODS_KEEP_IT_ALL_SYMBOL = "."
    MODS_REMOVE_LETTER_SYMBOL = "-"

    def __init__(self, path_to_rules_file: str = DEFAULT_PATH_TO_RULES_FILE):

        if path_to_rules_file:
            with open(path_to_rules_file, "r") as fp:
                self._root_rules_bean = Root.parse(json.load(fp=fp))
        else:
            self._root_rules_bean = Root.parse(rules_data.rules())

    def make(self, name_part: NamePart, gender: Gender, case_to_use: Case, original_name: str):

        result = original_name

        if name_part == NamePart.FIRSTNAME:
            name_bean: Name = self._root_rules_bean.firstname
        elif name_part == NamePart.LASTNAME:
            name_bean: Name = self._root_rules_bean.lastname
        elif name_part == NamePart.MIDDLENAME:
            name_bean: Name = self._root_rules_bean.middlename
        else:
            name_bean: Name = self._root_rules_bean.middlename

        exception_rule_bean: Rule = self.find_in_rule_bean_list(name_bean.exceptions, gender, original_name)
        suffix_rule_bean: Rule = self.find_in_rule_bean_list(name_bean.suffixes, gender, original_name)

        if exception_rule_bean and exception_rule_bean.gender == Gender.names(gender):
            rule_to_use: Rule = exception_rule_bean
        elif suffix_rule_bean and suffix_rule_bean.gender == Gender.names(gender):
            rule_to_use: Rule = suffix_rule_bean
        else:
            rule_to_use: Rule = exception_rule_bean if exception_rule_bean else suffix_rule_bean

        if rule_to_use:
            mod2apply: str = rule_to_use.mods[case_to_use.value]
            result = self.apply_mod2name(mod2apply=mod2apply, name=original_name)

        return result

    def apply_mod2name(self, mod2apply: str, name: str):

        result = name

        # if modification is not needed
        if mod2apply != PetrovichDeclinationMaker.MODS_KEEP_IT_ALL_SYMBOL:
            # if modification is needed according to rules
            if PetrovichDeclinationMaker.MODS_REMOVE_LETTER_SYMBOL in mod2apply:
                for i in range(len(mod2apply)):
                    # if special character "-", removing the last letter
                    if mod2apply[i] == PetrovichDeclinationMaker.MODS_REMOVE_LETTER_SYMBOL:
                        result = result[0:len(result) - 1]
                    # if not a special character "-", adding the rest of the modifier to the result
                    else:
                        result += mod2apply[i:]
                        break
            else:
                result = name + mod2apply

        return result

    def find_in_rule_bean_list(self, rule_bean_list: list, gender: Gender, original_name: str):

        result = None
        done = False

        if rule_bean_list is not None:
            # traversing all rules available
            for rule_bean in rule_bean_list:
                if done:
                    break
                # traversing all available checks for word ends
                for test in rule_bean.test:
                    # if match found
                    if original_name.endswith(test):
                        # if angrogynous OR gender match -- we're done, escaping both loops
                        if rule_bean.gender == Gender.names(Gender.ANDROGYNOUS) or \
                                rule_bean.gender == Gender.names(gender):
                            result = rule_bean
                            done = True
                            break
        return result