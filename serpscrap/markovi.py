#!/usr/bin/python3
# -*- coding: utf-8 -*-
import markovify

class Markovi():

    def __init__(self, config=None):
        self.config = config

    def generate(self, text, state_size=3, chars=140):
        # Build the model.
        text_model = markovify.Text(text, state_size)
        
        # Print five randomly-generated sentences
        for _ in range(5):
            print(text_model.make_sentence(tries=100, max_overlap_ratio=0.7, max_overlap_total=15))
            print()
        
        # Print three randomly-generated sentences of no more than 140 characters
        for _ in range(3):
            print(text_model.make_short_sentence(chars))
            print()
