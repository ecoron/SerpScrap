#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
SerpScrap.Tfidf
"""
from sklearn.feature_extraction.text import TfidfVectorizer


class TfIdf:
    """
    Tfidf modul inspired by
        http://www.markhneedham.com/blog/2015/02/15/pythonscikit-learn-calculating-tfidf-on-how-i-met-your-mother-transcripts/
        http://scikit-learn.org/stable/auto_examples/applications/topics_extraction_with_nmf_lda.html#example-applications-topics-extraction-with-nmf-lda-py

    Attributes:
        stopwords (list): list of stopwords
        get_tfidf (list, list): generate and return word, tfidf values
        fit_tfidf (string): create and return a vectorizer
        learn_tfidf (vectorizer, string, list): generate the word, tfidf values
    """
    stopwords = 'english'
    # https://solariz.de/de/downloads/6/german-enhanced-stopwords.htm

    def get_tfidf(self, text_list, keywords=[]):
        """generate a list of dicts of words and tfidf values
        Args:
            text_list (list): list of text strings
            keywords (list): optional list of strings
        Returns:
            list: a list of dicts
        """
#         with open('stopwords.txt') as f:
#             self.stopwords = f.read().splitlines()
        vectorizer = self.fit_tfidf('\n'.join(text_list))
        return self.learn_tfidf(vectorizer, '\n'.join(text_list), keywords)

    def fit_tfidf(self, txt):
        """fit the TfidfVectorizer
        Args:
            txt (string): text to train
        Returtns:
            vectorizer
        """
        tf = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 1),
            min_df=0,
            stop_words=self.stopwords,
            use_idf=True,
            smooth_idf=True
        )
        return tf.fit([txt])

    def learn_tfidf(self, vectorizer, txt, keywords):
        """lern tfidf
        Args:
            vectorizer: the created vectorizer
            txt (string): the text to learn
            keywords (list). optional list to filter the results
        Returns:
            list: dicts of word and tfidf value
        """
        result = []

        tfidf_matrix = vectorizer.transform([txt])
        feature_names = vectorizer.get_feature_names()
        dense = tfidf_matrix.todense()
        phrases = dense[0].tolist()[0]
        phrase_scores = [pair for pair in zip(range(0, len(phrases)), phrases) if pair[1] > 0]
        sorted_phrase_scores = sorted(phrase_scores, key=lambda t: t[1] * -1)
        for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores]:
            if len(keywords) < 1:
                result.append({'word': phrase, 'tfidf': score})
            elif len(keywords) >= 1 and phrase.lower() in keywords:
                result.append({'word': phrase, 'tfidf': score})
        return result
