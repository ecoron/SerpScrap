from sklearn.feature_extraction.text import TfidfVectorizer


class TfIdf:

    stopwords = []  # https://solariz.de/de/downloads/6/german-enhanced-stopwords.htm

    def get_tfidf(self, text_list, keywords=[]):
#         with open('stopwords.txt') as f:
#             self.stopwords = f.read().splitlines()
        vectorizer = self.fit_tfidf('\n'.join(text_list))
        return self.learn_tfidf(vectorizer, '\n'.join(text_list), keywords)

    def fit_tfidf(self, txt):
        tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 1), min_df=0, stop_words=self.stopwords, use_idf=True, smooth_idf=True)
        return tf.fit([txt])

    def learn_tfidf(self, vectorizer, txt, keywords):
        """
        http://www.markhneedham.com/blog/2015/02/15/pythonscikit-learn-calculating-tfidf-on-how-i-met-your-mother-transcripts/
        http://scikit-learn.org/stable/auto_examples/applications/topics_extraction_with_nmf_lda.html#example-applications-topics-extraction-with-nmf-lda-py
        """
        result = []

        tfidf_matrix = vectorizer.transform([txt])
        feature_names = vectorizer.get_feature_names()
        dense = tfidf_matrix.todense()
        phrases = dense[0].tolist()[0]
        phrase_scores = [pair for pair in zip(range(0, len(phrases)), phrases) if pair[1] > 0]
        sorted_phrase_scores = sorted(phrase_scores, key=lambda t: t[1] * -1)
        for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores]:
            if len(keywords)<1:
                result.append({'word': phrase, 'tfidf': score})
            elif len(keywords)>=1 and phrase.lower() in keywords:
                result.append({'word': phrase, 'tfidf': score})
        return result
