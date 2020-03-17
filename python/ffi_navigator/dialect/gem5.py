"""GEM5 FFI convention"""
import os
import re
from .. import pattern
from .base_provider import BaseProvider


class GEM5Provider(BaseProvider):
    """Provider for GEM5 FFI.

    Parameters
    ----------
    resolver : PyImportResolver
        Resolver for orginial definition.

    logger : Logger object
    """
    def __init__(self, resolver, logger):
        super().__init__(resolver, logger, "gem5")
        
        # TODO: fix all range in the regexr capture
        self.py_cc_ident = pattern.re_findaller(
            r"(?P<key>[A-Za-z0-9_]+)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key"), path=path, range=rg)
        )
        self.py_sim_object = pattern.re_matcher(
            r"\s*class\s*(?P<key>[A-Za-z0-9_]+)\((?P<base>[A-Za-z0-9_,\s]+)\)",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)

        self.py_scons_def_func = pattern.re_matcher(
            r"\s*def\s*(?P<key>[A-Za-z][A-Za-z0-9_]+)\(",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)

        # A hack of avoiding too many invalid references counted in
        self.py_init_sim_object = pattern.re_matcher(
            r"(?P<key>[A-Za-z0-9_]+)\s*\(",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key"), path=path, range=rg),
            use_search=True)

        self.py_inherit_sim_object = pattern.re_matcher(
            r"\((?P<key>[A-Za-z0-9_]+)\s*\)",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key"), path=path, range=rg),
            use_search=True)

        self.py_dot_sim_object = pattern.re_matcher(
            r"(?P<key>[A-Za-z0-9_]+)\.",
            lambda match, path, rg:
            pattern.Ref(key=match.group("key"), path=path, range=rg),
            use_search=True)


        self.cc_header = pattern.re_matcher(
            r"\s*(class|struct)\s*(?P<key>[A-Za-z0-9_]+)(?!;)",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)
        
        self.cc_source = pattern.re_matcher(
            r"\s*(?<![A-Za-z0-9_:])(?P<key>[A-Za-z0-9_]+)\s*::\s*(?P=key)",
            lambda match, path, rg:
            pattern.Def(key=match.group("key"), path=path, range=rg),
            use_search=True)
        

    def get_additional_scan_dirs(self, root_path):
        return [
            os.path.join(root_path, "configs"),
            os.path.join(root_path, "src"),
            # os.path.join(root_path, "build"),
        ]

    def _cc_extract(self, path, source, begin, end):
        results = self.cc_header(path, source, begin, end)
        results += self.cc_source(path, source, begin, end)
        return results

    def _py_extract(self, path, source, begin, end):
        results = self.py_sim_object(path, source, begin, end)
        results += self.py_init_sim_object(path, source, begin, end)
        results += self.py_inherit_sim_object(path, source, begin, end)
        results += self.py_dot_sim_object(path, source, begin, end)
        results += self.py_scons_def_func(path, source, begin, end)
        return results

    def extract_symbol(self, path, source, pos):
        begin = max(pos.line - 1, 0)
        end = min(pos.line + 2, len(source))
        for res in self.py_cc_ident(path, source, begin, end):
            if (isinstance(res, (pattern.Ref, pattern.Def)) and
                res.range.start.line <= pos.line and
                res.range.end.line >= pos.line and
                res.range.start.character <= pos.character and
                res.range.end.character >= pos.character):
                return res
        return None
