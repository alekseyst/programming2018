import builtins
import io
import pickle
import nltk
import collections
import os
import argparse
import json
import re

nltk.download('punkt')


safe_builtins = {
    'range',
    'complex',
    'set',
    'frozenset',
    'slice',
    'int',
}

safe_other = {
    'nltk.tokenize.punkt.PunktSentenceTokenizer': nltk.tokenize.punkt.PunktSentenceTokenizer,
    'nltk.tokenize.punkt.PunktParameters': nltk.tokenize.punkt.PunktParameters,
    'nltk.tokenize.punkt.PunktLanguageVars': nltk.tokenize.punkt.PunktLanguageVars,
    'nltk.tokenize.punkt.PunktToken': nltk.tokenize.punkt.PunktToken,
    'collections.defaultdict': collections.defaultdict,
}


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "builtins" and name in safe_builtins:
            return getattr(builtins, name)

        obj = safe_other.get('%s.%s' % (module, name))
        if obj is not None:
            return obj

        raise pickle.UnpicklingError("global '%s.%s' is forbidden" %
                                     (module, name))

def restricted_loads(s):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(s).load()


def get_tokenizer():
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'etc/nltk/russian.pickle')
    with open(path, 'rb') as rus_punct:
        return restricted_loads(rus_punct)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='input file path', required=True)
    parser.add_argument('-o', '--output', help='output file path', required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    tokenizer = get_tokenizer()

    with open(args.input) as input_file:
        text = input_file.read()

    sentences = tokenizer.tokenize(text)
    sentences = [re.sub('\s+', ' ', sent) for sent in sentences]    
    with open(args.output, 'w') as output_file:
        output_file.write(json.dumps(sentences, sort_keys=True, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
