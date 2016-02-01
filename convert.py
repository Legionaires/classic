#!/usr/bin/python

import re

class Converter:
	def __init__(self, text, bbcode_uid):
		self.raw_text = text
		self.bbcode_uid = bbcode_uid
		self.text = self.raw_text

	def convert(self):
		self.basic_substitution("/b")	
		self.basic_substitution("b")
		self.basic_substitution("i")
		self.basic_substitution("/i")
		self.basic_substitution("u")
		self.basic_substitution("/u")
		self.sub_with_param("color", "font color")
		self.simple("/color", "/font")
		self.text = self.text.replace('\n', "<br>")	
	
	def process(self):
		self.convert()	
		return self.text


	def basic_substitution(self, bbtag):
		self.text = self.text.replace("["+bbtag+":"+self.bbcode_uid+"]","<"+bbtag+">")

	def simple(self, bbtag, htag):
		self.text = self.text.replace("["+bbtag+":"+self.bbcode_uid+"]","<"+htag+">")

	def sub_with_param(self, bbtag, htag):
		self.text = re.sub(r"\["+bbtag+"=([a-zA-Z0-9_]+):"+self.bbcode_uid+"\]", r"<"+htag+r"=\1>", self.text)



