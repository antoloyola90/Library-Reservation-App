import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import datetime
import time
import logging

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Reservations(ndb.Model):
    reservedBy = ndb.StringProperty(indexed=False)
    startTime = ndb.TimeProperty(indexed=False)
    endTime = ndb.TimeProperty(indexed=False)

class Resource(ndb.Model):
    user = ndb.UserProperty()
    name = ndb.StringProperty(indexed=False)
    startTime = ndb.StringProperty(indexed=False)
    endTime = ndb.StringProperty(indexed=False)
    tags = ndb.StringProperty(indexed=False)
    reservations = ndb.StructuredProperty(Reservations, repeated = True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        resourceNameGet = self.request.get('resourceNameGet')
        startTimeGet = self.request.get('startTimeGet')
        endTimeGet = self.request.get('endTimeGet')
        tagsGet = self.request.get('tagsGet')
        sizeGet = self.request.get('sizeGet')

        if not( sizeGet == "" ):
            sizeInt = int(sizeGet)
            logging.info('sizeInt = ' + str(sizeInt))

        resources_for_user = Resource.gql("WHERE user = :1", user)
        index_list = list(resources_for_user)
        
        logging.info('len(index_list) = ' + str(len(index_list)))

        if not( resourceNameGet == "" ) and sizeInt == len(index_list):
            index_list.append(Resource(user=user, name=resourceNameGet, startTime=startTimeGet, endTime=endTimeGet, tags=tagsGet))

        index_list.sort(key=lambda x: x.name)
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resources_for_user': index_list,
        }
        
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class AddResource(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        template = JINJA_ENVIRONMENT.get_template('addResource.html')
        template_values = {}
        self.response.write(template.render(template_values))
    def post(self):
        resourceNameGet = self.request.get('resourceName')
        startTimeGet = self.request.get('startTime')
        endTimeGet = self.request.get('endTime')
        tagsGet = self.request.get('tags')
        userGet = users.get_current_user()

        repeatedResource = False
        resources_for_user = Resource.gql("WHERE user = :1", userGet)
        for e in resources_for_user:
            if e.name == resourceNameGet:
                repeatedResource = True
                break
        
        index_list = list(resources_for_user)
        if repeatedResource:
            template = JINJA_ENVIRONMENT.get_template('addResource.html')
            template_values = {
                'repeatedResource': repeatedResource,
            }
            self.response.write(template.render(template_values))
        else:
            resource = Resource(user=userGet, name=resourceNameGet, startTime=startTimeGet, endTime=endTimeGet, tags=tagsGet)
            resource.put()
            self.redirect('/?resourceNameGet='+resourceNameGet+'&startTimeGet='+startTimeGet+'&endTimeGet='+endTimeGet+'&tagsGet='+tagsGet+'&sizeGet='+str(len(index_list)))

class ViewResource(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        resourceID = self.request.get('id')
        resource_by_id = Resource.gql("WHERE ID = :1", resourceID)

        for e in resource_by_id:
            logging.info('e.name = ' + e.name)



app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/addResource', AddResource),
    ('/resource', ViewResource)
], debug=True)