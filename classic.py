#!/usr/bin/env python

import MySQLdb
import tornado.httpserver
import tornado.web
import os.path
import json
import tornado.escape

"""
Ideally each endpoint will work for JSON and HTML.  JSON first
"""

root_url = "undefined"




class Application(tornado.web.Application):
	def __init__(self):
		global root_url		
		config_file = open("config.json").read()
		config_data = json.loads(config_file)
		root_url = config_data["server"]

		handlers = [
			(r"/main", MainHandler),
			(r"/count", CountHandler),
			(r"/", tornado.web.RedirectHandler, dict(url=r"/main")),
			(r"/([a-z]+)", DatabaseHandler),
			(r"/([a-z]+)/([0-9]+)",ForumHandler),
			(r"/([a-z]+)/([0-9]+)/([0-9]+)",ThreadHandler), 
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
			c.execute("SELECT forum_id, forum_name, forum_desc FROM %s_forums" % prefix)
			out = {}
			forum_list = []
			for row in c.fetchall():
				forum_name = row[1].decode('latin1').encode('utf8')
				forum_desc = row[2].decode('latin1').encode('utf8')
				forum_list.append({"name":forum_name, "description":forum_desc,"url":root_url+db+"/"+str(row[0])})
			out["forums"] = forum_list
			self.write(out)	

class ForumHandler(HandlerBase):
	def get(self, db, forum_id):
		prefix = self.prefix(db)
		if prefix:
			out = {}
			thread_list = []
			c = self.application.db.cursor()
			select_table = "SELECT forum_id, topic_title, topic_id, topic_poster FROM %s" % prefix + "_topics"
			select_text = select_table + " WHERE forum_id=%s ORDER BY topic_id"
			c.execute(select_text, (forum_id,))
			for row in c.fetchall():
				title = row[1].decode('latin1').encode('utf8')
				thread_list.append({"title":title, "creator_id":str(row[2]),  "url":root_url+db+"/"+forum_id+"/"+str(row[2])})
			out["threads"] = thread_list
			self.write(out)


#TODO: use a JOIN!
class ThreadHandler(HandlerBase):
	def get(self, db, forum_id, topic_id):
		prefix = self.prefix(db)
		if prefix:
			out = {}
			post_list = []
			c = self.application.db.cursor()
			select_table = "SELECT post_id, poster_id from %s" % prefix + "_posts"
			select_text = select_table + " WHERE topic_id=%s ORDER BY post_id"
			c.execute(select_text, (topic_id,))
			for row in c.fetchall():
				c2 = self.application.db.cursor()
				select_table2 = "SELECT post_subject,post_text from %s" % prefix + "_posts_text"
				select_text2 = select_table2 + " WHERE post_id=%s"
				c2.execute(select_text2, (row[0],))
				row2 = c2.fetchone()
				subject = row2[0].decode('latin1').encode('utf8')
				text = row2[1].decode('latin1').encode('utf8')
				post_list.append({"subject":subject, "text":text,"poster_id":str(row[1]), "url":root_url+db+"/"+forum_id+"/"+topic_id+"/"+str(row[0])})
			out["posts"] = post_list
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


