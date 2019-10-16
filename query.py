"""
query.py
Jin Zhao, Xiaojing Yan, Kun Li, Erik Andersen

handles the query for elasticsearch
"""

import os, json, re

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

from index import Idiom
from elasticsearch_dsl import Q
from elasticsearch_dsl import connections
from elasticsearch_dsl.utils import AttrList
from elasticsearch_dsl import Search

app = Flask(__name__)
Bootstrap(app)

zodiac = {"":"", '鼠':'Mouse', '牛':'Ox', '虎':'Tiger', '兔':'Rabbit', '龙':'Dragon', '蛇':'Snake', '马':'Horse', '羊':'Goat', '猴':'Monkey', '鸡':'Rooster', '狗':'Dog', '猪':'Pig'}
difficulty = {"":"", 'Easy':'简单', 'Medium':'中等', 'Hard':'困难'}
sentiment = {'': '', 'Positive':'褒义词', 'Negative':'贬义词'}
char_num = ['', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '14']

tmp_name = ""
tmp_pinyin = ""
tmp_zodiac = ""
tmp_difficulty = ""
tmp_sentiment = ""
tmp_char_num = ""
tmp_english = ""
tmp_afterword = ""
tmp_riddle = ""
tmp_source = ""
tmp_story = ""
tmp_synonym = ""
tmp_antonym = ""
tmp_usage = ""
tmp_translation = ""
tmp_description = ""
gresults = {}

def find_translations(translation_hits, sent_code):
    index = 0
    translation_index_hits = []
    for t in translation_hits:
        for x, y in sent_code.items():
            if t in y:
                translation_index_hits.append(x)
    return translation_index_hits

def make_sgmt_dict(sgmt, sgmt_dict):
    index = 0
    for s in sgmt:
        sgmt_dict[str(index)] = s
        index += 1


@app.route("/")
def query():
    """For top level route ("/"), simply present a query page."""
    return render_template('query_page.html', zodiac=zodiac, difficulty=difficulty, sentiment=sentiment, char_num=char_num)


@app.route("/results", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route("/results/<page>", methods=['GET', 'POST'])
def results(page):
    global tmp_name
    global tmp_pinyin
    global tmp_zodiac
    global tmp_difficulty
    global tmp_sentiment
    global tmp_char_num
    global gresults

    # convert the <page> parameter in url to integer.
    if type(page) is not int:
        page = int(page.encode('utf-8'))
    # if the method of request is post (for initial query), store query in local global variables
    if request.method == 'POST':
        name_query = request.form['name']
        pinyin_query = request.form['pinyin']
        zodiac_query = request.form['zodiac']
        difficulty_query = request.form['difficulty']
        sentiment_query = request.form['sentiment']
        char_num_query = request.form['char_num']

        tmp_name = name_query
        tmp_pinyin = pinyin_query
        tmp_zodiac = zodiac_query
        tmp_difficulty = difficulty_query
        tmp_sentiment = sentiment_query
        tmp_char_num = char_num_query

    else:
        name_query = tmp_name
        pinyin_query = tmp_pinyin
        zodiac_query = tmp_zodiac
        difficulty_query = tmp_difficulty
        sentiment_query = tmp_sentiment
        char_num_query = tmp_char_num

    shows = {}
    shows['name'] = name_query
    shows['pinyin'] = pinyin_query
    shows['zodiac'] = zodiac_query
    shows['difficulty'] = difficulty_query
    shows['sentiment'] = sentiment_query
    shows['char_num'] = char_num_query


    s = Search(index='idioms_search')

    if len(name_query) > 0:
        s = s.query('multi_match', query=name_query, type='cross_fields', fields=['name^4', 'english^4', 'desc_segmentation', 'desc_translation',
                                                                                  'synonym^2', 'source_translation',
                                                                                  'source_segmentation^2', 'story_translation',
                                                                                  'story_segmentation', 'usage_translation',
                                                                                  'usage_segmentation'], operator='and')
    if len(pinyin_query) > 0:
        q = Q('match', pinyin={'query': pinyin_query, 'operator': 'and'})
        s = s.query(q)

    if len(zodiac_query) > 0:
        q = Q('match', zodiac=zodiac_query)
        s = s.query(q)

    if len(difficulty_query) > 0:
        q = Q('match', difficulty=difficulty_query)
        s = s.query(q)

    if len(sentiment_query) > 0:
        q = Q('match', sentiment=sentiment_query)
        s = s.query(q)

    if len(char_num_query) > 0:
        q = Q('match', char_num=char_num_query)
        s = s.query(q)


    s = s.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    s = s.highlight('name', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('pinyin', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('english', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('zodiac', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('desc_segmentation', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('desc_translation', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('source_segmentation', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('source_translation', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('story_segmentation', fragment_size=999999999, number_of_fragments=20)
    s = s.highlight('story_translation', fragment_size=999999999, number_of_fragments=20)
    s = s.highlight('usage_segmentation', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('usage_translation', fragment_size=999999999, number_of_fragments=5)
    s = s.highlight('difficulty', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('sentiment', fragment_size=999999999, number_of_fragments=1)

    # determine the subset of results to display (based on current <page> value)
    start = 0 + (page - 1) * 10
    end = 10 + (page - 1) * 10

    response = s[start:end].execute()

    # if response.hits.total == 0:
    #     # if conjunction failed, make the query disjunctive for text field
    #     search = Search(index='idioms_search')

    resultList = {}
    translation_hits = []
    source_translation_hits = []
    story_translation_hits = []
    usage_translation_hits = []
    for hit in response.hits:
        result = dict()
        result['score'] = hit.meta.score

        if 'highlight' in hit.meta:
            if 'name' in hit.meta.highlight:
                result['name'] = hit.meta.highlight.name[0]
            else:
                result['name'] = hit.name
            if 'english' in hit.meta.highlight:
                result['english'] = hit.meta.highlight.english[0]
            else:
                result['english'] = hit.english
            if 'pinyin' in hit.meta.highlight:
                result['pinyin'] = hit.meta.highlight.pinyin[0]
            else:
                result['pinyin'] = hit.pinyin
            if 'zodiac' in hit.meta.highlight:
                result['zodiac'] = hit.meta.highlight.zodiac
            else:
                result['zodiac'] = hit.zodiac
            if 'difficulty' in hit.meta.highlight:
                result['difficulty'] = hit.meta.highlight.difficulty[0]
            else:
                result['difficulty'] = hit.difficulty
            if 'sentiment' in hit.meta.highlight:
                result['sentiment'] = hit.meta.highlight.sentiment[0]
            else:
                result['sentiment'] = hit.sentiment
            if 'desc_translation' in hit.meta.highlight:
                result['desc_translation'] = hit.meta.highlight.desc_translation[0]
                translation_hits = [re.sub(r'</?mark>', '', t) for t in hit.meta.highlight.desc_translation]
            if 'source_translation' in hit.meta.highlight:
                result['source_translation'] = hit.meta.highlight.source_translation[0]
                source_translation_hits = [re.sub(r'</?mark>', '', t) for t in hit.meta.highlight.source_translation]
            if 'story_translation' in hit.meta.highlight:
                result['story_translation'] = hit.meta.highlight.story_translation[0]
                story_translation_hits = [re.sub(r'</?mark>', '', t) for t in hit.meta.highlight.story_translation]
            if 'usage_translation' in hit.meta.highlight:
                result['usage_translation'] = hit.meta.highlight.usage_translation[0]
                usage_translation_hits = [re.sub(r'</?mark>', '', t) for t in hit.meta.highlight.usage_translation]
        else:
            result['name'] = hit.name
            result['pinyin'] = hit.pinyin
            result['english'] = hit.english
            # result['description'] = hit.description
            result['zodiac'] = hit.zodiac
            result['difficulty'] = hit.difficulty
            result['sentiment'] = hit.sentiment
        sgmt = json_data[hit.meta.id]['Description_Segmentation']
        sent_code = json_data[hit.meta.id]['Description_Sentence_Code']
        sgmt_dict = dict()
        src_sgmt = json_data[hit.meta.id]['Source_Segmentation']
        src_sent_code = json_data[hit.meta.id]['Source_Sentence_Code']
        src_sgmt_dict = dict()
        story_sgmt = json_data[hit.meta.id]['Story_Segmentation']
        story_sent_code = json_data[hit.meta.id]['Story_Sentence_Code']
        story_sgmt_dict = dict()
        usage_sgmt = json_data[hit.meta.id]['Usage_Segmentation']
        usage_sent_code = json_data[hit.meta.id]['Usage_Sentence_Code']
        usage_sgmt_dict = dict()
        translation_index_hits = find_translations(translation_hits, sent_code)
        translation_src_hits = find_translations(source_translation_hits, src_sent_code)
        translation_story_hits = find_translations(story_translation_hits, story_sent_code)
        translation_usage_hits = find_translations(usage_translation_hits, usage_sent_code)
        make_sgmt_dict(sgmt, sgmt_dict)
        make_sgmt_dict(src_sgmt, src_sgmt_dict)
        make_sgmt_dict(story_sgmt, story_sgmt_dict)
        make_sgmt_dict(usage_sgmt, usage_sgmt_dict)



        result['desc_segmentation'] = sgmt_dict
        result['desc_sentence_code'] = sent_code
        result['translation_hits'] = translation_index_hits
        result['source_segmentation'] = src_sgmt_dict
        result['source_sentence_code'] = src_sent_code
        result['source_translation_hits'] = translation_src_hits
        result['story_segmentation'] = story_sgmt_dict
        result['story_sentence_code'] = story_sent_code
        result['story_translation_hits'] = translation_story_hits
        result['usage_segmentation'] = usage_sgmt_dict
        result['usage_sentence_code'] = usage_sent_code
        result['usage_translation_hits'] = translation_usage_hits
        resultList[hit.meta.id] = result

    # make the result list available globally
    gresults = resultList

    # total number of matching results
    result_num = response.hits.total

    # if results are found, extract title and text information from doc_data, else do nothing
    message = []
    if result_num > 0:
        if result_num > 500:
            message.append('Over 500 search results! We recommend you narrow your search.')
        return render_template('page_SERP.html', results=resultList, res_num=result_num, page_num=page, queries=shows,
                               zodiac=zodiac, sentiment=sentiment, difficulty=difficulty, char_num=char_num, warning=message,
                               json_data=json_data)
    else:
        warning = None
        message.append(['One of the field you typed in cannot be found.'])
        return render_template('page_SERP.html', results=message, res_num=result_num, page_num=page, queries=shows,
                               warning=warning, zodiac=zodiac, sentiment=sentiment, difficulty=difficulty, char_num=char_num,
                               json_data=json_data)

@app.route("/documents/<res>", methods=['GET'])
def documents(res):
    """
    displays the information for a document (film) - loads page_targetArticle.html
    """
    keys = ['description', 'source', 'usage']
    global gresults
    desc_translations = gresults[res]['desc_sentence_code']
    translation = {k:v for k, v in gresults[res].items() if 'segmentation' in k or 'sentence' in k or 'translation' in k}
    idiom = {k:v for k, v in gresults[res].items() if k not in translation.keys()}
    idiomtitle = idiom['name']
    for term in idiom:
        if type(idiom[term]) is AttrList:
            s = "\n"
            for item in idiom[term]:
                s += item + ",\n "
            idiom[term] = s
    # fetch the movie from the elasticsearch index using its id
    chengyu = Idiom.get(id=res, index='idioms_search')
    chengyudic = chengyu.to_dict()
    index = 0
    description_dict = dict()
    for key, value in chengyudic.items():
        if 'translation' in key:
            translation[key] = value
        else:
            idiom[key] = value
    '''
        if key == 'description':
            print(value)
            for v in value:
                description_dict[str(index)] = v
                index += 1
    idiom = {k: v for k, v in idiom.items() if k not in translation.keys()}
    
    print(description_dict)
    '''
    # idiom['runtime'] = str(chengyudic['runtime']) + " min" if filmdic['runtime'] > -1 else "Unknown"
    return render_template('page_targetArticle.html', idiom=idiom, name=idiomtitle, keys=keys, translation=translation)

if __name__ == "__main__":
    json_file = os.path.join(os.path.curdir, 'translations.json')
    with open(json_file) as f:
        json_data = json.load(f)
    app.run(debug=True)