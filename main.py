#!/usr/bin/env python

import logging

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import c2dmutil

import models

def redirectUnlessKlaxon(handler, path):
  """redirects user to login screen, unless user-agent contains klaxon."""
  if(handler.request.headers.has_key("user-agent")):
    logging.info(handler.request.headers["user-agent"].lower())
    if( "klaxon" in handler.request.headers["user-agent"].lower()):
      logging.info("looks like klaxon: %s" %
          handler.request.headers["user-agent"].lower())
      handler.response.set_status(401, "Unauthorized")
      handler.response.out.write("Unauthorized. try logging in.")
  handler.redirect(users.create_login_url(path))

class RegistrationHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      redirectUnlessKlaxon(self, "/register")
      return 
    token = self.request.get('token')
    requested_sender = self.request.get('sender')

    existingUserQuery = models.Person.gql(
      "WHERE user = :1",
      user)
    p = existingUserQuery.get()
    if p:
      # if tokens match, no changes needed.
      if token == p.registration_id:
        logging.info("User already registered. no work needed.")
        self.response.set_status(200, "already registered.")
      else:
        logging.info("Change of token!")
        p.registration_id = token
        p.put()
        self.response.set_status(200, "Token updated.")

    else:
      logging.info("New user!")
      p = models.Person()
      p.user = user
      p.registration_id = token
      p.enabled = True
      p.put()
      self.response.set_status(200, "Registered new user.")

  def unregister(self):
    """Remove the registration token for the current user."""
    user = users.get_current_user()
    if not user:
      redirectUnlessKlaxon(self, "/unregister")
      return
    existingUserQuery = models.Person.gql(
      "WHERE user = :1",
      user)
    p = existingUserQuery.get()
    if p:
      # Clear the registration_id for this user.
      p.registration_id = None
      p.put()
      self.response.set_status(200, "Token removed.")
      self.response.out.write("Token removed. Unregistered.")


class MainHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('Hello world!')

class PushTestHandler(webapp.RequestHandler):
  """test by sending a stock push message."""
  def get(self):
    user = users.get_current_user()
    if not user:
      redirectUnlessKlaxon(self, "/test")
      return;
    #send a test push message.
    c = c2dmutil.C2dmUtil()
    me = models.Person.gql('WHERE user = :1', user).get()
    logging.info("Sending test message to: %s" % user)
    c.sendMessage(me)
    self.response.set_status(200, "C2dm Message Sent.")
    self.response.out.write("A test message has been sent to you. If you do not recieve it, check your settings, and re-register.")


def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
     ('/register', RegistrationHandler),
     ('/test', PushTestHandler),
    ], debug=True)

  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
