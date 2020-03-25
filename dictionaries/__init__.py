import os
from .dict_base import DicionarioBase, DicionarioChaves

from .modules.offline import Offline
from .modules.priberam import Priberam
from .modules.dicio import Dicio
from .modules.lexicopt import LexicoPT

default_dicts = [Offline(), Priberam(), LexicoPT(), Dicio()]

known_classes = {'adjetivo', 'pronome', 'substantivo', 'verbo', 'preposição', 'conjunção', 'artigo', 'advérbio'}
known_conversions = {'adjectivo': 'adjetivo', 'numeral': 'adjetivo'}

class DictionaryManager():
    def __init__(self, autoload=True, dicts=None, classes=None, conversions=None):
        self.dicts = dicts or default_dicts
        self.classes = classes or known_classes
        self.conversions = conversions or known_conversions
        self.cache_file = os.path.join(os.path.dirname(__file__), '__pycache__', 'cache.json')
        self.cache = dict()
        if autoload and os.path.isfile(self.cache_file):
            self.load()
    
    def __get_word(self, w):
        return self.cache.get(w, None) or dict()
    
    def __get_key(self, w, key):
        return self.__get_word(w).get(key, None)
    
    @staticmethod
    def __firstNotNoneTupled(*args, invert=False):
        for i, v in reversed(args) if invert else args:
            if not v is None:
                return v, i
        return None, None
    
    @staticmethod
    def __firstNotNone(*args, invert=False):
        return DictionaryManager.__firstNotNoneTupled(enumerate(reversed(args) if invert else args))
    
    def __join_word_dic(self, w, dictcand, invert=False):
        cand = dictcand.get(w, sourceinv=self)
        cach = self.__get_word(w).copy()

        for k in set(cach.keys()).union(cand.keys()):
            if k.endswith('_src'):
                continue
            cands = [(cach.get(k+'_src', None), cach.get(k, None)), (str(dictcand), cand.get(k, None))]
            t0, t1 = DictionaryManager.__firstNotNoneTupled(*cands, invert=invert)
            if not t0 is None and k == 'classe':
                t0 = self.conversions.get(t0, t0)
                if not t0 in self.classes:
                    raise Exception('Classe desconhecida para a palavra \'{}\': {}'.format(w, t0))
            cach[k] = t0
            cach[k+'_src'] = t1
        self.cache[w] = cach
        return cach
    
    def __fetch_word(self, w, k, optional=False):
        for d in self.dicts:
            nc = self.__join_word_dic(w, d)
            if not nc.get(k, None) is None:
                return nc[k]
        self.save()
        if optional:
            return optional
        raise Exception("A procura da '{}' do(a) palavra '{}' falhou mesmo após varrer todos os dicionários.".format(k, w))
    
    def get(self, w, key, optional=False, autolower=True, *args, **kwargs):
        lower = lambda l: l.lower() if autolower else l
        r = self.__get_key(w.lower(), key)
        return lower(r or self.__fetch_word(w.lower(), key, optional=optional))

    def load(self):
        import json
        with open(self.cache_file, 'r') as fh:
            self.cache = json.load(fh)
    
    def save(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        import json
        with open(self.cache_file, 'w') as fh:
            json.dump(self.cache, fh)
    
    def offline_cache_overwrite(self, autosave=True):
        offl = Offline()
        for w in self.cache:
            self.__join_word_dic(w, offl, invert=True)
        if autosave:
            self.save()