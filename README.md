# Chinese-Idiom-Search-Engine

### Overview ###
This project is a search engine for Chinese idioms and proverbs (mainly including the 4-character 成语 [chéngyǔ], the vernacular 俗语 [súyǔ] and the longer, allegorical 歇后语 [xiēhòuyǔ]).

### Authors ###
This project was created by Jin Zhao, Kun Li, Xiaojing Yan, and Erik Andersen.

### Search Engine ###
The index to the search engine contains 13,279 entries and makes use of both structured and unstructured data. For structured data, we used three fields: name, 
pinyin (with diacritical marks flattened), and description. For unstructured 
data, we used a regular expression to grab important elements found in the description, such as 
usage and source. Our search mechanism also contains features to filter based on aspects important to Chinese culture 
(such as a specific animal, or positive/negative connotation), as selecting a correct idiom to use is very important to Chinese people. 
We also included English translation for Chinese learners. Specifically, a query in English will return Chinese words as results, but only if the translation to the word(s) contains that English word. 
A pop-up menu showing the English translation is shown when the user hovers over a segmented word.

### Build Instructions ###
Before running, the module *flask* needs to be installed. The process can be 
done as follows. 
1. pip3 install Flask 
 
Some sources also suggest installing the virtual environment, which can be done as follows. 
1. pip3 install virtualenv 
 
Also, please make sure that nltk is installed. nltk can be installed as follows. 
sudo pip3 install -U nltk
 
Next, the CoreNLP and ElasticSearch servers both need to be started. First download coreNLP 
version 3.9.2 from the Stanford website: <u>https://stanfordnlp.github.io/CoreNLP/</u>
 
Then, run the coreNLP server with the following command (make sure to be in the directory 
corresponding to the coreNLP package you downloaded):  
java -mx3g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP -props StanfordCoreNLP-chinese.properties -file chinese.txt -outputFormat text 
 
java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -serverProperties StanfordCoreNLP-chinese.properties -preload tokenize,ssplit,pos,lemma,ner,parse -status_port 9001  -port 9001 -timeout 15000 
 
Then, run the elasticsearch server, making sure to be in the directory where you downloaded 
elasticsearch to: 
./bin/elasticsearch

### Notes ###
Please see the file chinese_idioms_readme.pdf for more information.
