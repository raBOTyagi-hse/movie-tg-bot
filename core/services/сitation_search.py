from collections import Counter
from nltk.text import TextCollection
import numpy as np
import re
import pymorphy2
from scipy.spatial.distance import cosine
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

stopwords_eng = set(stopwords.words('english'))
stopwords_ru = set(stopwords.words('russian'))
stemmer = SnowballStemmer("english")
morph = pymorphy2.MorphAnalyzer()
words_eng = r'[A-Za-z]+'
words_ru = r'[А-Яа-я]+'


class CitationSearch:
    def __init__(self, pairs, mode='eng', stopwords_flag=True):
        self.pair_dict = {}
        self.ids = [pair[0] for pair in pairs]
        self.tfidfs = []
        self.mode = mode
        self.stopwords_flag = stopwords_flag
        docs = [pair[1] for pair in pairs]
        self.docs = [self.preprocess(doc) for doc in docs]
        for id, text in zip (self.ids, self.docs):
            self.pair_dict[id] = text
        self.corpus = TextCollection(self.docs)
        self.query = []

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
                doc_tfs[term] = self.get_tf(term, doc) * self.get_idf(term)
            doc_vector = self.normalize_cosine(doc, list(doc_tfs.values()))
            doc_tfidfs = {}
            for term, vec in zip(doc_tfs, doc_vector):
                doc_tfidfs[term] = vec
            doc_vectors.append(doc_tfidfs)
        self.tfidfs = doc_vectors

    def tfidf_queries(self, query):
        self.query = self.preprocess(query)
        query_tfsidfs = {}
        for term in self.query:
           query_tfsidfs[term] = self.get_tf(term, self.query) * self.get_idf(term)
        return query_tfsidfs

    def query_relevance(self, query):
        tfidf = self.tfidf_queries(query)
        query_vec = list(tfidf.values())
        doc_vecs = []
        for doc in self.tfidfs:
            doc_vec = []
            for term_query in tfidf:
                if term_query in doc:
                    doc_vec.append(doc[term_query])
                else:
                    doc_vec.append(0)
            doc_vecs.append(doc_vec)
        cosines = []
        for vec in doc_vecs:
            if np.any(vec):
                cosines.append(1 - cosine(vec, query_vec))
            else:
                cosines.append(0)
        relevance_ids = [text_id for _, text_id in sorted(zip(cosines, self.ids), key=(lambda x: x[0]), reverse=True)]
        cosines.sort(reverse=True)
        most_relevant = relevance_ids[0]
        relevant_candidates = [relevance_ids[0]]
        for cos in range(1,len(cosines)):
            if cosines[0] - cosines[cos] <= 0.000001:
                relevant_candidates.append(relevance_ids[cos])
        if len(relevant_candidates) > 1:
            tiebreaker = []
            for id in relevant_candidates:
                rel_text = self.pair_dict[id]
                absent_words = 0
                for word in rel_text:
                    if word not in self.query:
                        absent_words += 1
                tiebreaker.append(absent_words)
            relevant_candidates = [text_id for _, text_id in sorted(zip(tiebreaker, relevant_candidates),
                                                                    key=(lambda x: x[0]))]
            most_relevant = relevant_candidates[0]
        return most_relevant, cosines[0]
