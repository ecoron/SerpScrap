#!/usr/bin/python3
# -*- coding: utf-8 -*-
import markovify

class Markovi():

    def __init__(self, config=None):
        self.config = config

    def generate(self, text, chars=140):
        # Build the model.
        text_model = markovify.Text(text)
        
        # Print five randomly-generated sentences
        for _ in range(5):
            print(text_model.make_sentence())
        
        # Print three randomly-generated sentences of no more than 140 characters
        for _ in range(3):
            print(text_model.make_short_sentence(chars))
