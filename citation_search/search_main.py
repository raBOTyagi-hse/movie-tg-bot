from collections import Counter
from nltk.text import TextCollection
import numpy as np
import re
import pymorphy2
from scipy.spatial.distance import cosine
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

stopwords_eng = set(stopwords.words('english'))
stopwords_ru = set(stopwords.words('russian'))
stemmer = SnowballStemmer("english")
morph = pymorphy2.MorphAnalyzer()
words_eng = r'[A-Za-z]+'
words_ru = r'[А-Яа-я]+'

class MovieSearch:
    def __init__(self, pairs, mode='eng', stopwords_flag=True):
        self.pairs = pairs
        self.ids = [pair[0] for pair in pairs]
        self.tfidfs = []
        self.mode = mode
        self.stopwords_flag = stopwords_flag
        words = []
        docs = [pair[1] for pair in pairs]
        self.docs = [self.preprocess(doc) for doc in docs]
        self.corpus = TextCollection(self.docs)

    def preprocess(self, raw):
        if self.mode == 'eng':
            return self.preprocess_eng(raw)
        if self.mode == 'ru':
            return self.preprocess_ru(raw)
        if self.mode == 'eng+ru':
            return self.preprocess_eng(raw) + self.preprocess_ru(raw)

    def preprocess_eng(self, raw):
        doc = []
        text = re.findall(words_eng, raw)
        for token in text:
            token = token.lower()
            if self.stopwords_flag:
                if token not in stopwords_eng:
                    doc.append(stemmer.stem(token))
            else:
                doc.append(stemmer.stem(token))
        return doc

    def preprocess_ru(self, raw):
        doc = []
        text = re.findall(words_ru, raw)
        for token in text:
            if self.stopwords_flag:
                if token not in stopwords_ru:
                    doc.append(morph.parse(token)[0].normal_form)
            else:
                doc.append(morph.parse(token)[0].normal_form)
        return doc

    def get_tf(self, term, document):
        return self.corpus.tf(term, document)

    def get_logtf(self, term, document):
        return np.log(self.corpus.tf(term, document)) + 1

    def get_idf(self, term):
        return self.corpus.idf(term)

    @staticmethod
    def normalize_cosine(doc, doc_vecs):
        counter = Counter(doc)
        cosine_norm = np.sqrt(np.sum(np.array(list(dict(counter).values())) ** 2))
        doc_vector = np.array(doc_vecs) / cosine_norm
        return doc_vector

    def tfidf_docs(self):
        doc_vectors = []
        for doc in self.docs:
            doc_tfs = {}
            for term in doc:
                doc_tfs[term] = self.get_logtf(term, doc)
            doc_vector = self.normalize_cosine(doc, list(doc_tfs.values()))
            doc_tfidfs = {}
            for term, vec in zip(doc_tfs, doc_vector):
                doc_tfidfs[term] = vec
            doc_vectors.append(doc_tfidfs)
        #print(doc_vectors)
        self.tfidfs = doc_vectors

    def tfidf_queries(self, query):
        query = self.preprocess(query)
        #print(query)
        query_tfsidfs = {}
        for term in query:
           query_tfsidfs[term] = self.get_logtf(term, query) * self.get_idf(term)
        return query_tfsidfs

    def query_relevance(self, query):
        tfidf = self.tfidf_queries(query)
        query_vec = list(tfidf.values())
        doc_vecs = []
        for doc in self.tfidfs:
            #print(doc)
            doc_vec = []
            for term_query in tfidf:
                if term_query in doc:
                    doc_vec.append(doc[term_query])
                else:
                    doc_vec.append(0)
            doc_vecs.append(doc_vec)
            #print(doc_vec)
        cosines = []
        for vec in doc_vecs:
            if np.any(vec):
                cosines.append(1 - cosine(vec, query_vec))
            else:
                cosines.append(0)
        #print(cosines)
        relevance_ids = [text_id for _, text_id in sorted(zip(cosines, self.ids), reverse=True)]
        cosines.sort(reverse=True)
        return relevance_ids[0], cosines[0]


# example
'''
test = [['10563', 'Daddy, people expect me to be there!'], [25, 'Here, you put your hand under the water and I will pump for you']]
testsearch = MovieSearch(test, mode='eng+ru')
testsearch.tfidf_docs()
print(testsearch.query_relevance('В каком фильме говорится: put you hand over the water, Daddy, and I will pump'))
'''