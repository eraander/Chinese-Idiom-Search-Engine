'''
What this file does:
chengyu_index.py
reads in the 13279 chengyu in the file
Indexes name, pinyin, and does more detailed analysis on
description, puts all recognized categories into a dictionary - creates json file,
Also segments some sentences using Stanford CoreNLP, and then provides possible translations to be used later on

Jin Zhao, Xiaojing Yan, Kun Li, Erik Andersen
"""
'''

import os, re, json
from nltk.parse import CoreNLPParser
from nltk.corpus import stopwords

chinese_stopwords = set('的了很不没有我你他')
punctuation = set('，《》。？/、【】；：！（）»“”«＜＞＊－．＋＇＆＂＃＄％｣｢～＾［］[]()\'*$#%&‧‧•—~﹏﹁﹂\"…＠｀＿＼＝')
to_translate = ['Description', 'Source', 'Story', 'Usage']

def lookup(sentence, dictionary):
    """
    looks up all the words in a segmented sentence in the given dictionary
    """
    sent_dict = dict()
    translations = []
    index = 0
    for word in sentence:
        word_dict = dict()
        if word in dictionary.keys():
            word_translations = dictionary[word]
            translations.extend(word_translations)
            word_dict[word] = word_translations
            sent_dict[str(index)] = word_translations
        else:
            translations.append(word)
            sent_dict[str(index)] = word
        index += 1
    return translations, sent_dict

def corpus_from_dict(dictionary, filename):
    """

    turns a dictionary into a json file
    """
    with open(filename, 'w') as file:
        json.dump(dictionary, file, ensure_ascii=False, indent=3)

if __name__ == '__main__':
    filename = os.path.join(os.path.curdir, '13279_chengyu.txt')
    dict_file = os.path.join(os.path.curdir, 'cedict_1_0_ts_utf-8_mdbg.txt')
    f = open(filename)

    chengyu_index = dict()
    chengyu_english = dict()
    # files for index, translations, and dictionary
    chengyu_json_file = os.path.join(os.path.curdir, 'chengyu_index_r.json')
    translation_json_file = os.path.join(os.path.curdir, 'translations.json')
    zh_en_trad_json_file = os.path.join(os.path.curdir, 'zh_en_trad.json')
    zh_en_simp_json_file = os.path.join(os.path.curdir, 'zh_en_simp.json')
    shelf_file = os.path.join(os.path.curdir, 'chengyu_shelf')
    file_content = f.read().split('\n')
    all_chengyu = []
    chengyu_number = 1
    # build index
    # start CoreNLP server
    chengyu_segmenter = CoreNLPParser('http://localhost:9001')
    words = []

    dict_f = open(dict_file)
    dict_file_content = dict_f.read().split('\n')
    all_chinese = []
    zh_en_trad_dict = dict()
    zh_en_simp_dict = dict()
    # go through chinese-english dictionary and extract translations
    for line in dict_file_content:
        if line.startswith('#') or not line:
            continue
        # grab necessary parts of the chinese dictionary using regexes
        chinese_chars = re.sub(r'\s\[.+', '', line)
        trad_simplified = chinese_chars.split()
        pinyin = re.sub(r'^[^\[]+\[', '', line)
        pinyin = re.sub(r'\].+', '', pinyin)
        pinyin = pinyin.strip('\[')
        meaning = re.sub(r'^[^/]+/', '', line)
        meaning = meaning.strip('/')
        definitions = meaning.split('/')
        definitions = [d for d in definitions if not d.startswith('variant') and not d.startswith('CL') and not
                       d.startswith('see ')]
        zh_en_trad_dict[trad_simplified[0]] = definitions
        if trad_simplified[1] in zh_en_simp_dict.keys():
            previous = zh_en_simp_dict[trad_simplified[1]]
            previous.extend(definitions)
            all_definitions = list(set(previous))
            zh_en_simp_dict[trad_simplified[1]] = all_definitions
        else:
            zh_en_simp_dict[trad_simplified[1]] = definitions
        all_chinese.extend(trad_simplified)
    # categories that are followed by :
    categories = ['歇后语', '灯迷会', '英语', '反义词', '近义词', '用法', '故事', '出处', '拼音']
    category_english = ['Afterword', 'Riddle', 'English', 'Antonym', 'Synonym', 'Usage', 'Story', 'Source', 'Pinyin']
    category_dict = dict(zip(categories, category_english))
    # go through chengyu file
    for line in file_content:
        if line.startswith('//') or not line:
            continue
        chengyu_data = dict()
        chengyu = line.split('\t')
        all_chengyu.append(chengyu[0])
        # start with structured data - name, pinyin, description
        chengyu_data['Name'] = chengyu[0]
        chengyu_data['Pinyin'] = chengyu[1]
        # split on : to find range of each category above
        split_description = chengyu[2].split(':')
        next_category = ""
        for s in split_description:
            s = s.strip('】')
            last_three = s[-3:]
            last_two = s[-2:]
            if last_two in categories:
                s = s.rstrip(last_two)
            elif last_three in categories:
                s = s.rstrip(last_three)
            if next_category:
                eng_category = category_dict[next_category]
                chengyu_data[eng_category] = s
            else:
                chengyu_data['Description'] = s
            if last_two in categories:
                next_category = last_two
            elif last_three in categories:
                next_category = last_three
        # make sure all entries have each of the categories above as keys
        for c in category_english:
            if c not in chengyu_data:
                chengyu_data[c] = ""
        translation_help = dict()
        # fields that support translation
        for field in to_translate:
            to_segment = chengyu_data[field]
            # substitute out · to help with segmentation
            to_segment = re.sub(r'·', ' ', to_segment)
            if to_segment:
                new_words = list(chengyu_segmenter.tokenize(to_segment))
            else:
                new_words = []
            # add extra fields
            translation_help[field + '_Segmentation'] = new_words

            translations, sent_dict = lookup(new_words, zh_en_simp_dict)
            chengyu_data[field + '_Translations'] = translations
            translation_help[field + '_Sentence_Code'] = sent_dict
        chengyu_english[chengyu_number] = translation_help
        chengyu_index[chengyu_number] = chengyu_data
        chengyu_number += 1

    # make necessary json files (chengyu index, translation, simplified chinese dictionary)
    corpus_from_dict(chengyu_index, chengyu_json_file)
    corpus_from_dict(chengyu_english, translation_json_file)
    corpus_from_dict(zh_en_simp_dict, zh_en_simp_json_file)
