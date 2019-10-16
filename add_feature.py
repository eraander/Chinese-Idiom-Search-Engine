"""
add_feature.py
Jin Zhao, Xiaojing Yan, Kun Li, Erik Andersen
"""

import json
import pandas as pd
import re
import nltk
import thulac
import unicodedata
import zhon


class AddFeature():
    def __init__(self):
        with open("chengyu_index_r.json", "r") as json_file:
            data = json_file.read()
            self.data_dict = json.loads(data)
            # for Chinese segmentation
            self.thu = thulac.thulac(user_dict=None,
                                model_path=None,
                                T2S=False,  # 繁体到简体
                                seg_only=True,  # 只分词
                                filt=True,  # 过滤没有意义的词
                                deli='_')  # 分隔词和词性的分割符

    def remove_accents(self, input_str):
        """
        takes any input string and
        flattens characters with diacritics into ascii
        """
        # input_str = replace_polish_l_stroke(input_str)
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = nfkd_form.encode('ASCII', 'ignore')
        ascii_str = only_ascii.decode('ascii')
        return ascii_str.lower()

    def add_difficulty(self):
        difficulty_dict_HSK = dict()
        with open("HSK.txt", "r") as f:
            data = f.readlines()
            for line in data:
                freq = int(line.split()[2])
                word = line.split()[1]
                if freq > 100:
                    difficulty_dict_HSK[word] = "Easy"
                elif freq > 50 and freq < 99:
                    difficulty_dict_HSK[word] = "Medium"
                else:
                    difficulty_dict_HSK[word] = "Hard"

        hsk_vocab = list()
        for key in difficulty_dict_HSK:
            hsk_vocab.append(key)

        for i in range(1, len(self.data_dict) + 1):
            sub_dict = self.data_dict[str(i)]
            if sub_dict["Name"] in hsk_vocab:
                sub_dict["Difficulty"] = difficulty_dict_HSK[sub_dict["Name"]]
            else:
                sub_dict["Difficulty"] = "Hard"


    def add_animal_field(self):
        """
        this added the animal key and character number key and
        create a key that is segmented pinyin and remove the tones in pinyin
        create a key that is sentiment for the words that has the sentiment information in usage
        """
        zodiac_animals = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']
        zodiac_animals_english = ['Mouse', 'Ox', 'Tiger', 'Rabbit', 'Dragon', 'Snake', 'Horse', 'Goat', 'Monkey', 'Rooster', 'Dog', 'Pig']
        zodiac_animals_translation = dict(zip(zodiac_animals, zodiac_animals_english))


        for i in range(1, len(self.data_dict) + 1):
            sub_dict = self.data_dict[str(i)]
            # adding the sentiment information comes from usage and description
            matches = re.findall('[褒|贬]义', sub_dict['Usage'])
            matches.extend(re.findall('[褒|贬]义', sub_dict['Description']))
            if matches:
                if matches[0] == '褒义':
                    sub_dict['Sentiment'] = 'Positive'
                else:
                    sub_dict['Sentiment'] = 'Negative'
            else:
                sub_dict['Sentiment'] = ''
            # segment the pinyin
            pinyin_a_re = re.compile(zhon.pinyin.RE_ACCENT, re.I | re.X)
            sub_dict['Pinyin_segmented'] = pinyin_a_re.findall(sub_dict['Pinyin'])
            # remove the tones
            # for i in range(len(sub_dict['Pinyin_segmented'])):
            #    sub_dict['Pinyin_segmented'][i] = self.remove_accents(sub_dict['Pinyin_segmented'][i])
            # sub_dict["Pinyin"] = self.remove_accents(sub_dict["Pinyin"])
            animal_list = list()
            # sub_dict: {'Name': '釜中之鱼', 'Pinyin': 'fǔzhōngzhīyú', 'Description': '在锅里游着的鱼。比喻不能久活出处:《元史·王荣祖传》：“彼小国负险自守，釜中之鱼，非久自死。”近义词:风中之烛用法:偏正式；作宾语；比喻处在绝境中的人', 'Animal': []}
            for zodiac_animal in zodiac_animals:
                if zodiac_animal in sub_dict['Name'] or zodiac_animal in sub_dict['Description'].split('。')[0]:
                    animal_list.append(zodiac_animals_translation[zodiac_animal])
            sub_dict['Animal'] = animal_list
            # add the char_num key
            if '，' in sub_dict['Name']:
                sub_dict['Char_num'] = len(sub_dict['Name'])-1
            else:
                sub_dict['Char_num'] = len(sub_dict['Name'])

    def add_sentiment(self,classifier):
        self.run_classifier(classifier)

    def seg_char(self, sent):
        """
        split Chinese string into Chinese characters
        """
        pattern = re.compile(r'([\u4e00-\u9fa5])')
        chars = pattern.split(sent)
        chars = [w for w in chars if len(w.strip()) > 0]
        return chars

    def seg_word(self, sent):
        """
        split into Chinese words
        :param sent:
        :return:
        """
        text = self.thu.cut(sent, text=True)
        return text.split()

    def create_feature_sets(self):
        df = pd.read_excel("sentiment_vocab.xlsx")
        labeled_data = df.values.tolist()
        # [['先天下之忧而忧，后天下之乐而乐', 15, 'idiom', 1.0, 1.0, 'PH', 9, 1, 'PD', 7.0, 1.0, nan, nan], ['打掉牙往肚子里吞－有苦显不出来', 15, 'idiom', 1.0, 1.0, 'NE', 7, 2, nan, nan, nan, nan, nan], ...]
        feature_set = list()
        for idiom_data in labeled_data:
            # generate first element feature dict
            feature_dict = dict()
            feature_dict[idiom_data[0]] = True
            char_list = self.seg_char(idiom_data[0])
            for char in char_list:
                feature_dict[char] = True
            # print(feature_dict)
            # generate second element tag
            tag = idiom_data[5][0]
            if tag == "P":
                tag = "Positive"
            elif tag == "N":
                tag = "Negative"
            feature_tuple = (feature_dict, tag)
            # print(feature_tuple)
            feature_set.append(feature_tuple)
        return feature_set

    def train_classifier(self, training_set):
        """
        :param training_set: feat_set
        :return: well-trained classifier
        """
        # create the classifier
        classifier = nltk.NaiveBayesClassifier.train(training_set)
        return classifier

    def evaluate_classifier(self, classifier, test_set):
        # get the accuracy and print it
        return nltk.classify.accuracy(classifier, test_set)

    def run_classifier(self, classifier):
        for i in range(1, len(self.data_dict) + 1):
            sub_dict = self.data_dict[str(i)]
            if sub_dict['Sentiment'] == '':
                feature_dict = dict()
                feature_dict[sub_dict["Name"]] = True
                description = sub_dict["Description"].split("。")[0]
                description_list = self.seg_word(description)
                for des in description_list:
                    feature_dict[des] = True
                tag = classifier.classify(feature_dict)
                sub_dict["Sentiment"] = tag

if __name__ == '__main__':
    add_feature = AddFeature()
    # train classifier
    feature_set = add_feature.create_feature_sets()
    classifier = add_feature.train_classifier(feature_set)

    # accu = add_feature.evaluate_classifier(classifier, feature_set)
    # print(accu)

    # classifier.show_most_informative_features(n=50)

    add_feature.add_animal_field()
    add_feature.add_difficulty()
    add_feature.add_sentiment(classifier)

    with open('chengyu_addedfeatures.json', 'w') as json_f:
        json.dump(add_feature.data_dict, json_f, ensure_ascii=False, indent=3)

