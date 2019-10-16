"""
index.py
Jin Zhao, Xiaojing Yan, Kun Li, Erik Andersen

builds the elasticsearch index
"""


import json
import re
import string
import time
import shelve
import os

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, Document, Text, Keyword, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import tokenizer, analyzer, token_filter, char_filter
from elasticsearch_dsl.query import MultiMatch, Match

# Connect to local host server
connections.create_connection(hosts=['127.0.0.1'])

# Create elasticsearch object
es = Elasticsearch()

# chn_analyzer = analyzer()
list_analyzer = analyzer(name_or_instance='custom', tokenizer='standard')
translate_analyzer = analyzer('translate_analyzer', tokenizer='standard', filter=['stop', 'stemmer', 'lowercase'])
english_analyzer = analyzer('english_analyzer', tokenizer='standard', filter=['stemmer', 'lowercase'])
pinyin_analyzer = analyzer('pinyin_analyzer', tokenizer='standard', filter=['asciifolding', 'lowercase'])


class Idiom(Document):
    name = Text()
    english = Text(analyzer=english_analyzer)
    afterword = Text()
    riddle = Text()
    source = Text()
    story = Text()
    synonym = Text()
    antonym = Text()
    desc_translation = Text(analyzer=translate_analyzer)
    source_translation = Text(analyzer=translate_analyzer)
    story_translation = Text(analyzer=translate_analyzer)
    usage_translation = Text(analyzer=translate_analyzer)
    # description = Text()
    desc_segmentation = Text()
    story_segmentation = Text()
    source_segmentation = Text()
    usage_segmentation = Text()
    pinyin = Text(analyzer=pinyin_analyzer)
    zodiac = Text()
    difficulty = Text()
    sentiment = Text()
    char_num = Integer()
    # synonym = Text(analyzer=list_analyzer)

    # override the Document save method to include subclass field definitions
    def save(self, *args, **kwargs):
        return super(Idiom, self).save(*args, **kwargs)

# Populate the index
def buildIndex():
    idiom_index = Index('idioms_search')

    if idiom_index.exists():
        idiom_index.delete()
    idiom_index.document(Idiom)
    idiom_index.create()

    # get json object movies
    with open('chengyu_addedfeatures.json', 'r', encoding='utf-8') as data_file:
        idioms = json.load(data_file)
        size = len(idioms)
    with open('translations.json', 'r', encoding='utf-8') as translation_file:
        translations = json.load(translation_file)

    def actions():
        for mid in range(1, size + 1):
            pinyin_segmentation = idioms[str(mid)]['Pinyin_segmented']
            segmentation_string = " ".join(pinyin_segmentation)
            animal = idioms[str(mid)]['Animal']
            zodiac = ", ".join(animal)
            english = idioms[str(mid)]['English']
            idioms[str(mid)]['English'] = english.rstrip("\"")
            # print(segmentation_string)
            yield {

                "_index": "idioms_search",
                "_type": 'doc',
                "_id": mid,
                "name": idioms[str(mid)]['Name'],
                "english": idioms[str(mid)]['English'],
                "afterword": idioms[str(mid)]['Afterword'],
                "riddle": idioms[str(mid)]['Riddle'],
                "source": idioms[str(mid)]['Source'],
                "story": idioms[str(mid)]['Story'],
                "synonym": idioms[str(mid)]['Synonym'],
                "antonym": idioms[str(mid)]['Antonym'],
                "desc_translation": idioms[str(mid)]['Description_Translations'],
                "source_translation": idioms[str(mid)]['Source_Translations'],
                "story_translation": idioms[str(mid)]['Story_Translations'],
                "usage_translation": idioms[str(mid)]['Usage_Translations'],
                "desc_segmentation": translations[str(mid)]['Description_Segmentation'],
                "source_segmentation": translations[str(mid)]['Source_Segmentation'],
                "story_segmentation": translations[str(mid)]['Story_Segmentation'],
                "usage_segmentation": translations[str(mid)]['Usage_Segmentation'],
                "pinyin": segmentation_string,
                "zodiac": zodiac,
                "sentiment": idioms[str(mid)]['Sentiment'],
                "difficulty": idioms[str(mid)]['Difficulty'],
                "char_num": idioms[str(mid)]['Char_num'],
                # "synonym": idioms[str(mid)]['Synonym']
            }
    helpers.bulk(es, actions())


def main():
    start_time = time.time()
    buildIndex()
    print("=*=*= Built index in {} seconds =*=*=".format(time.time() - start_time))


if __name__ == '__main__':
    main()
    print(connections.get_connection().cluster.health())
