"""
Preprocessing script for LC-QUAD data.
"""

import glob
import os

import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split

def make_dirs(dirs):
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)

def dependency_parse(filepath, cp='', tokenize=True):
    print('\nDependency parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    tokpath = os.path.join(dirpath, filepre + '.toks')
    parentpath = os.path.join(dirpath, filepre + '.parents')
    relpath = os.path.join(dirpath, filepre + '.rels')
    pospath = os.path.join(dirpath, filepre + '.pos')
    lenpath = os.path.join(dirpath, filepre + '.len')
    tokenize_flag = '-tokenize - ' if tokenize else ''
    cmd = ('java -cp %s DependencyParse -tokpath %s -parentpath %s -relpath %s -pospath %s -lenpath %s %s < %s'
           % (cp, tokpath, parentpath, relpath, pospath, lenpath, tokenize_flag, filepath))
    print(cmd)
    os.system(cmd)

def build_vocab(filepaths, dst_path, lowercase=False, character_level=False):
    vocab = set()
    for filepath in filepaths:
        with open(filepath) as f:
            for line in f:
                if lowercase:
                    line = line.lower()

                if character_level is True:
                    line = line.replace('\r', '').replace('\t', '')
                    line_split = [c for c in line]
                else:
                    line_split = line.split()
                vocab |= set(line_split)
    with open(dst_path, 'w') as f:
        for w in sorted(vocab):
            f.write(w + '\n')

def split_data(X, y, dst_dir):
    with open(os.path.join(dst_dir, 'id.txt'), 'w') as idfile, \
            open(os.path.join(dst_dir, 'input.txt'), 'w') as inputfile, \
            open(os.path.join(dst_dir, 'output.txt'), 'w') as outputfile:
        y = y.tolist()

        for index in range(len(X)):
            corrected_question = str(X.iloc[index]["corrected_question"]).strip()
            idfile.write(str(X.iloc[index]["_id"]) + "\n")
            inputfile.write(corrected_question + "\n")
            outputfile.write(str(y[index]) + "\n")


def parse(dirpath, cp=''):
    dependency_parse(os.path.join(dirpath, 'input.txt'), cp=cp, tokenize=True)

def generate_master_dataset(cp, lc_quad_dir, master_data_dir):
    df_train = pd.read_json(os.path.join(lc_quad_dir, "train2-data.json"))
    df_test = pd.read_json(os.path.join(lc_quad_dir, "test2-data.json"))
    df = pd.concat([df_train, df_test], ignore_index=True)

    desired_templates = df['sparql_template_id'].value_counts() >= 50
    desired_templates = desired_templates.index[desired_templates == True].tolist()
    df = df[df['sparql_template_id'].isin(desired_templates)]

    X = df.loc[:, df.columns != 'sparql_template_id']
    y = df['sparql_template_id'].tolist()

    for index in range(len(y)):
        id = y[index]
        if id >= 300 and id < 500: # Collapse 3xx or 4xx templates to their corresponding template - 300 id since all that differentiates them is extra rdf:type class triple which can be added as an optional triple to SPARQL Query
            y[index] = id - 300

        if y[index] == 152:  # Effectively Template 152 and Template 151 are the same template or can be converted into single SPARQL Query
            y[index] = 151

    y = pd.Series(y)
    df_combined = X
    df_combined['sparql_template_id'] = y
    df.to_csv(os.path.join(master_data_dir, 'dataset.csv'), index=False)

    split_data(X, y, master_data_dir)
    parse(master_data_dir, cp)

    # Build Vocabulary for input
    build_vocab(
        glob.glob(os.path.join(lc_quad_dir, '*/*.toks')),
        os.path.join(lc_quad_dir, 'vocab_toks.txt'), lowercase=True)

    # Character Level
    build_vocab(
        glob.glob(os.path.join(lc_quad_dir, '*/*.toks')),
        os.path.join(lc_quad_dir, 'vocab_chars.txt'), lowercase=True, character_level=True)

    build_vocab(
        glob.glob(os.path.join(lc_quad_dir, '*/*.pos')),
        os.path.join(lc_quad_dir, 'vocab_pos.txt'))

    build_vocab(
        glob.glob(os.path.join(lc_quad_dir, '*/*.rels')),
        os.path.join(lc_quad_dir, 'vocab_rels.txt'))

    with open(os.path.join(lc_quad_dir, 'vocab_output.txt'), 'w') as f:
        f.write('0\n1\n')

    y = y.tolist()
    with open(os.path.join(master_data_dir, 'similarity_input.txt'), 'w') as inputfile, \
            open(os.path.join(master_data_dir, 'similarity_templates.txt'), 'w') as templatefile, \
            open(os.path.join(master_data_dir, 'similarity_output.txt'), 'w') as outputfile:
        for index1 in tqdm(range(len(y))):
            for index2 in tqdm(range(len(y))):
                inputfile.write(str(index1) + ' ' + str(index2) + '\n')
                templatefile.write(str(y[index1]) + ' ' + str(y[index2]) + '\n')
                outputfile.write('1\n' if y[index1] == y[index2] else '0\n')

def split_train_test_data(X, y, dst_dir):
    with open(os.path.join(dst_dir, 'input.txt'), 'w') as inputfile, \
            open(os.path.join(dst_dir, 'templates.txt'), 'w') as templatefile, \
            open(os.path.join(dst_dir, 'output.txt'), 'w') as outputfile:

        for index in range(len(X)):
            inputfile.write(X.iloc[index]['input'] + "\n")
            templatefile.write(X.iloc[index]['templates'] + "\n")
            outputfile.write(str(y[index]) + "\n")

if __name__ == '__main__':
    print('=' * 80)
    print('Preprocessing LC-QUAD dataset')
    print('=' * 80)

    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    lc_quad_dir = os.path.join(data_dir, 'lc-quad')
    lib_dir = os.path.join(base_dir, 'lib')
    train_dir = os.path.join(lc_quad_dir, 'train')
    test_dir = os.path.join(lc_quad_dir, 'test')
    master_data_dir = os.path.join(lc_quad_dir, 'masterdata')

    make_dirs([master_data_dir, train_dir, test_dir])
    make_dirs([os.path.join(lc_quad_dir, 'pth')])

    # java classpath for calling Stanford parser
    classpath = ':'.join([
        lib_dir,
        os.path.join(lib_dir, 'stanford-parser/stanford-parser.jar'),
        os.path.join(lib_dir, 'stanford-parser/stanford-parser-3.9.1-models.jar')])

    # generate_master_dataset(classpath, lc_quad_dir, master_data_dir)

    # Generating Train and Test Data
    with open(os.path.join(master_data_dir, 'similarity_input.txt'), 'r') as inputfile, \
        open(os.path.join(master_data_dir, 'similarity_templates.txt'), 'r') as templatefile, \
        open(os.path.join(master_data_dir, 'similarity_output.txt'), 'r') as outputfile:
        input_file = inputfile.read().split('\n')[:-1]
        template_file = templatefile.read().split('\n')[:-1]
        output_file = outputfile.read().split()

    df = pd.DataFrame({'input': input_file, 'templates': template_file, 'output': output_file})
    print('comes here')

    X = df.loc[:, df.columns != 'output']
    y = df['output'].tolist()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.00044, random_state=42)
    print(len(X_train), len(X_test))

    X_train, X_test, y_train, y_test = train_test_split(X_test, y_test, test_size=0.2, random_state=42)
    print(len(X_train), len(X_test))

    split_train_test_data(X_train, y_train, train_dir)
    split_train_test_data(X_test, y_test, test_dir)