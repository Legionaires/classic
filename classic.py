#!/usr/bin/env python

import MySQLdb
import tornado.httpserver
import tornado.web
import os.path
import json

"""
Ideally each endpoint will work for JSON and HTML.  JSON first
"""

root_url = "undefined"




class Application(tornado.web.Application):
	def __init__(self):
		
		config_file = open("config.json").read()
		config_data = json.loads(config_file)
		root_url = config_data["server"]

		handlers = [
			(r"/main", MainHandler),
			(r"/count", CountHandler),
			(r"/", tornado.web.RedirectHandler, dict(url=r"/main")),
			(r"/([a-z]+)", DatabaseHandler), 
		]
		settings = dict(
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
		)
		super(Application, self).__init__(handlers, **settings)
		self.db = MySQLdb.connect(db=config_data["database"], 
						user=config_data["user"],
						passwd=config_data["passwd"])

		self.databases = [
			{ "name":"Classic M&R", "data_prefix":"classic", "url":"mr"},
			{ "name":"Lacy", "data_prefix":"lacy", "url":"lacy"},
			{ "name":"Old M&R", "data_prefix":"pn_phpbb","url":"old"},
			{ "name":"OOC", "data_prefix":"phpbb","url":"ooc"},
		]

	
"""  Ideally, we should be able to have each give direct json or wrap in html"""
class HandlerBase(tornado.web.RequestHandler):
	
	def prefix(self, name):
		for d in self.application.databases:
			if d["url"] == name:
				return d["data_prefix"]
		self.set_status(404)	
		return ""
	
class MainHandler(HandlerBase):
	def get(self):
		out = dict()
		dbs = []
		for d in self.application.databases:
			dbs.append({"name":d["name"], "url":root_url + d["url"]})
		out["databases"] = dbs
		self.write(out)


class DatabaseHandler(HandlerBase):
	def get(self, db):
		prefix = self.prefix(db)
		if prefix:
			c = self.application.db.cursor()
			c.execute("SELECT * FROM %s_forums" % prefix)
			out = {}
			forum_list = []
			for row in c.fetchall():
				forum_list.append(row)
			out["forums"] = forum_list
			self.write(out)	


class CountHandler(tornado.web.RequestHandler):
	def get(self):
		c = self.application.db.cursor()
		c.execute("SELECT COUNT(*) FROM classic_posts")
		self.render("count.html", count=c.fetchone())


def main():
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(8080)
	tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
	main()


