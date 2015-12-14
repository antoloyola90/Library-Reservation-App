import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import datetime
import time
import logging
import uuid

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
    
class Reservations(ndb.Model):
    reservedBy = ndb.StringProperty(indexed=False)
    startTime = ndb.TimeProperty(indexed=False)
    endTime = ndb.TimeProperty(indexed=False)

class Resource(ndb.Model):
    uniqueID = ndb.StringProperty(indexed=True)
    user = ndb.UserProperty()
    name = ndb.StringProperty(indexed=False)
    startHour = ndb.IntegerProperty(indexed=False)
    startMinute = ndb.IntegerProperty(indexed=False)
    startAMorPM = ndb.StringProperty(indexed=False)
    endHour = ndb.IntegerProperty(indexed=False)
    endMinute = ndb.IntegerProperty(indexed=False)
    endAMorPM = ndb.StringProperty(indexed=False)
    tags = ndb.StringProperty(repeated=True)
    reservations = ndb.StructuredProperty(Reservations, repeated = True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        resourceNameGet = self.request.get('resourceName')
        if not( resourceNameGet == "" ):
            startHourGet = int(self.request.get('startHour'))
            startMinuteGet = int(self.request.get('startMinute'))
            startAMorPMGet = self.request.get('startAMorPM')
            endHourGet = int(self.request.get('endHour'))
            endMinuteGet = int(self.request.get('endMinute'))
            endAMorPMGet = self.request.get('endAMorPM')
            tagsGet = self.request.get('tags')
            sizeInt = int(self.request.get('sizeGet'))
            uniqueID = self.request.get('uniqueID')
            editResource = self.request.get('editResource')

        resources_for_user = Resource.gql("WHERE user = :1", user)
        index_list = list(resources_for_user)
        
        if not( resourceNameGet == "" ) and sizeInt == len(index_list):
            if(editResource == "true"):
                numToDelete = 0;
                for x in index_list:
                    if x.uniqueID == uniqueID:
                        break
                    numToDelete = numToDelete + 1
                index_list.pop(numToDelete)
            tokens = tagsGet.split(',')
            tokens = [ s.strip() for s in tokens ]
            index_list.append(Resource(uniqueID=uniqueID, user=user, name=resourceNameGet, startHour=startHourGet, startMinute=startMinuteGet, startAMorPM=startAMorPMGet, endHour=endHourGet, endMinute=endMinuteGet, endAMorPM=endAMorPMGet, tags=tokens))

        index_list.sort(key=lambda x: x.name)
        logging.info(str(index_list))
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
        startHourGet = int(self.request.get('startHour'))
        startMinuteGet = int(self.request.get('startMinute'))
        startAMorPMGet = self.request.get('startAMorPM')
        endHourGet = int(self.request.get('endHour'))
        endMinuteGet = int(self.request.get('endMinute'))
        endAMorPMGet = self.request.get('endAMorPM')
        tagsGet = self.request.get('tags')
        userGet = users.get_current_user()
        editResource = self.request.get('editResource')
        uniqueID = self.request.get('uniqueID')

        if resourceNameGet is None or len(resourceNameGet) == 0:
            template_values = {
              'error': 'Resource Name cannot be empty',
              'resourceName': resourceNameGet,
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'startAMorPM': startAMorPMGet,
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'endAMorPM': endAMorPMGet,
              'tags': tagsGet,
              'editResource': editResource,
              'uniqueID': uniqueID,
            }
            template = JINJA_ENVIRONMENT.get_template('addResource.html')
            self.response.write(template.render(template_values))
            return

        if ( startAMorPMGet == 'PM' and endAMorPMGet == 'AM') or (startAMorPMGet == endAMorPMGet and (startHourGet > endHourGet or ( startHourGet == endHourGet and startMinuteGet >= endMinuteGet))):
            template_values = {
              'error': 'End Time must be after the Start Time',
              'resourceName': resourceNameGet,
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'startAMorPM': startAMorPMGet,
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'endAMorPM': endAMorPMGet,
              'tags': tagsGet,
              'editResource': editResource,
              'uniqueID': uniqueID,
            }
            template = JINJA_ENVIRONMENT.get_template('addResource.html')
            self.response.write(template.render(template_values))
            return

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
                'error': 'This Resource is already defined for this User. If You wish to increase the Capacity then delete the resource and create a new one with more capacity',
                'resourceName': resourceNameGet,
                'startHour': startHourGet,
                'startMinute': startMinuteGet,
                'startAMorPM': startAMorPMGet,
                'endHour': endHourGet,
                'endMinute': endMinuteGet,
                'endAMorPM': endAMorPMGet,
                'tags': tagsGet,
                'editResource': editResource,
                'uniqueID': uniqueID,
            }

            self.response.write(template.render(template_values))
        else:
            if editResource == "true":
                logging.info('uniqueID = ' + uniqueID)
                resource = Resource.query(Resource.uniqueID == uniqueID).get()
                resource.name = resourceNameGet
                resource.startHour = startHourGet
                resource.startMinute = startMinuteGet
                resource.startAMorPM = startAMorPMGet
                resource.endHour = endHourGet
                resource.endMinute = endMinuteGet
                resource.endAMorPM = endAMorPMGet
                tokens = tagsGet.split(',')
                tokens = [ s.strip() for s in tokens ]
                resource.tags = tokens
                resource.put()
                self.redirect('/?editResource=true&uniqueID='+uniqueID+'&resourceName='+resourceNameGet+'&startHour='+str(startHourGet)+'&startMinute='+str(startMinuteGet)+'&startAMorPM='+startAMorPMGet+'&endHour='+str(endHourGet)+'&endMinute='+str(endMinuteGet)+'&endAMorPM='+endAMorPMGet+'&tags='+tagsGet+'&sizeGet='+str(len(index_list)))
            else:    
                uniqueID = str(uuid.uuid4())
                tokens = tagsGet.split(',')
                tokens = [ s.strip() for s in tokens ]
                resource = Resource(uniqueID=uniqueID, user=userGet, name=resourceNameGet, startHour=startHourGet, startMinute=startMinuteGet, startAMorPM=startAMorPMGet, endHour=endHourGet, endMinute=endMinuteGet, endAMorPM=endAMorPMGet, tags=tokens)
                resource.put()
                self.redirect('/?uniqueID='+uniqueID+'&resourceName='+resourceNameGet+'&startHour='+str(startHourGet)+'&startMinute='+str(startMinuteGet)+'&startAMorPM='+startAMorPMGet+'&endHour='+str(endHourGet)+'&endMinute='+str(endMinuteGet)+'&endAMorPM='+endAMorPMGet+'&tags='+tagsGet+'&sizeGet='+str(len(index_list)))


class ViewResource(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        resourceID = self.request.get('uniqueID')
        resource = list(Resource.gql("WHERE uniqueID = :1", resourceID))[0]

        template = JINJA_ENVIRONMENT.get_template('resource.html')
        template_values = {
            'resource': resource,
        }
        self.response.write(template.render(template_values))

class ViewByTag(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        tag = self.request.get('tag')
        resourcesByTag = list(Resource.gql(""))

        numToDelete = 0
        for x in resourcesByTag:
            logging.info(str(x))
            logging.info(str(not(tag in x.tags)))
            if not(tag in x.tags):
                resourcesByTag.pop(numToDelete)
            numToDelete = numToDelete + 1

        logging.info(str(resourcesByTag))
        template = JINJA_ENVIRONMENT.get_template('tag.html')
        template_values = {
            'resources': resourcesByTag,
            'tag': tag,
        }
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/addResource', AddResource),
    ('/resource', ViewResource),
    ('/editResource', AddResource),
    ('/tags', ViewByTag)
], debug=True)