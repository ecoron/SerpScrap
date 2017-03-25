#!/usr/bin/python3
# -*- coding: utf-8 -*-
import markovify


class Markovi():

    def __init__(self, config=None):
        self.config = config

    def generate(self, text, state_size=1):
        # Build the model.
        text_model = self.get_model(text, state_size)
        # Print five randomly-generated sentences
        return text_model.make_sentence(
            tries=10,
            max_overlap_ratio=0.7,
            max_overlap_total=15
        )

    def generate_short(self, text, state_size=2, chars=140):
        text_model = self.get_model(text, state_size)
        return text_model.make_short_sentence(chars)

    def get_model(self, text, state_size):
        return markovify.Text(text, state_size)

    def get_combined_model(self, models, weights=None):
        return markovify.combine(models, weights)
