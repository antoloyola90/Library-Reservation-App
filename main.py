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
    
class Reservation(ndb.Model):
    uniqueID = ndb.StringProperty(indexed=True)
    user = ndb.UserProperty()
    resourceUniqueID = ndb.StringProperty(indexed=True)
    startHour = ndb.IntegerProperty(indexed=False)
    startMinute = ndb.IntegerProperty(indexed=False)
    startAMorPM = ndb.StringProperty(indexed=False)
    endHour = ndb.IntegerProperty(indexed=False)
    endMinute = ndb.IntegerProperty(indexed=False)
    endAMorPM = ndb.StringProperty(indexed=False)
    dateDay = ndb.IntegerProperty()
    dateMonth = ndb.IntegerProperty()
    dateYear = ndb.IntegerProperty()
    name = ndb.StringProperty(indexed=False)

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

        resources_for_user = Resource.gql("")
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

        reservations = list(Reservation.gql("WHERE user = :1", user))

        reservationsToDelete = list()
        for e in reservations:
            endHour = e.endHour
            if e.endAMorPM == 'PM':
                endHour = e.endHour + 12
            
            todaysDate = datetime.datetime.now()
            delta = datetime.timedelta(hours = 5)
            todaysDate = todaysDate - delta
            reservationDateTime = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, endHour, e.endMinute)
            if todaysDate > reservationDateTime:
                reservationsToDelete.append(e)

        for x in reservationsToDelete:
            reservations = [e for e in reservations if e.uniqueID != x.uniqueID]

        for e in reservations:
            res = list(Resource.gql("WHERE uniqueID = :1", e.resourceUniqueID))[0]
            e.name = res.name

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resources_for_user': index_list,
            'reservations': reservations,
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

class AddReservation(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        template = JINJA_ENVIRONMENT.get_template('addReservation.html')
        resourceUniqueID = self.request.get('resourceUniqueID')
        year = int(time.strftime("%Y"))
        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]
        template_values = {
            'resourceUniqueID': resourceUniqueID,
            'resource': resource,
            'todaysYear':year,
        }
        self.response.write(template.render(template_values))

    def post(self):
        year = int(time.strftime("%Y"))
        startHourGet = int(self.request.get('startHour'))
        startMinuteGet = int(self.request.get('startMinute'))
        startAMorPMGet = self.request.get('startAMorPM')
        endHourGet = int(self.request.get('endHour'))
        endMinuteGet = int(self.request.get('endMinute'))
        endAMorPMGet = self.request.get('endAMorPM')
        dateYearGet = int(self.request.get('dateYear'))
        dateMonthGet = int(self.request.get('dateMonth'))
        dateDayGet = int(self.request.get('dateDay'))
        userGet = users.get_current_user()
        resourceUniqueID = self.request.get('resourceUniqueID')

        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]

        if ( startAMorPMGet == 'PM' and endAMorPMGet == 'AM') or (startAMorPMGet == endAMorPMGet and (startHourGet > endHourGet or ( startHourGet == endHourGet and startMinuteGet >= endMinuteGet))):
            template_values = {
              'error': 'End Time must be after the Start Time',
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'startAMorPM': startAMorPMGet,
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'endAMorPM': endAMorPMGet,
              'dateYear': dateYearGet,
              'dateMonth': dateMonthGet,
              'dateDay': dateDayGet,
              'resourceUniqueID': resourceUniqueID,
              'resource': resource,
              'todaysYear':year,
            }
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            self.response.write(template.render(template_values))
            return

        try:
            changeBy12 = startHourGet
            if startAMorPMGet == 'PM':
                changeBy12 = startHourGet + 12
            requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, changeBy12, startMinuteGet)

            changeBy12 = endHourGet
            if endAMorPMGet == 'PM':
                changeBy12 = endHourGet + 12
            requestReservationEndTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, changeBy12, endMinuteGet)

        except ValueError:
            template_values = {
              'error': 'Date is incorrect! :)',
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'startAMorPM': startAMorPMGet,
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'endAMorPM': endAMorPMGet,
              'dateYear': dateYearGet,
              'dateMonth': dateMonthGet,
              'dateDay': dateDayGet,
              'resourceUniqueID': resourceUniqueID,
              'resource': resource,
              'todaysYear':year,
            }
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            self.response.write(template.render(template_values))
            return

        changeBy12 = startHourGet
        if startAMorPMGet == 'PM':
            changeBy12 = startHourGet + 12
        requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, changeBy12, startMinuteGet)

        todaysDate = datetime.datetime.now()
        delta = datetime.timedelta(hours = 5)
        todaysDate = todaysDate - delta

        if todaysDate > requestReservationStartTime:
            template_values = {
              'error': 'Choose a time after the NOW! :)',
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'startAMorPM': startAMorPMGet,
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'endAMorPM': endAMorPMGet,
              'dateYear': dateYearGet,
              'dateMonth': dateMonthGet,
              'dateDay': dateDayGet,
              'resourceUniqueID': resourceUniqueID,
              'resource': resource,
              'todaysYear':year,
            }
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            self.response.write(template.render(template_values))
            return

        overlapReservation = False
        reservations_for_resource = Reservation.gql("WHERE resourceUniqueID = :1 AND dateYear = :2 AND dateMonth = :3 AND dateDay = :4", resourceUniqueID, dateYearGet, dateMonthGet, dateDayGet)
        for e in reservations_for_resource:
            changeBy12 = e.startHour
            if e.startAMorPM == 'PM':
                changeBy12 = e.startHour + 12
            reservationStart = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, changeBy12, e.startMinute)
            
            changeBy12 = e.endHour
            if e.endAMorPM == 'PM':
                changeBy12 = e.endHour + 12
            reservationEnd = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, changeBy12, e.endMinute)

            changeBy12 = startHourGet
            if startAMorPMGet == 'PM':
                changeBy12 = startHourGet + 12
            requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, changeBy12, startMinuteGet)

            changeBy12 = endHourGet
            if endAMorPMGet == 'PM':
                changeBy12 = endHourGet + 12
            requestReservationEndTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, changeBy12, endMinuteGet)
            
            overlap = reservationStart <= requestReservationEndTime and reservationEnd >= requestReservationStartTime
            
            if overlap:
                overlapReservation = True
                break
        
        index_list = list(reservations_for_resource)
        if overlapReservation:
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            template_values = {
                'error': 'This Reservation is not available for that time range.',
                'startHour': startHourGet,
                'startMinute': startMinuteGet,
                'startAMorPM': startAMorPMGet,
                'endHour': endHourGet,
                'endMinute': endMinuteGet,
                'endAMorPM': endAMorPMGet,
                'dateYear': dateYearGet,
                'dateMonth': dateMonthGet,
                'dateDay': dateDayGet,
                'resourceUniqueID': resourceUniqueID,
                'resource': resource,
                'todaysYear':year,
            }

            self.response.write(template.render(template_values))
        else:
            uniqueID = str(uuid.uuid4())
            reservation = Reservation(uniqueID=uniqueID, user=userGet, resourceUniqueID=resourceUniqueID, startHour=startHourGet, startMinute=startMinuteGet, startAMorPM=startAMorPMGet, endHour=endHourGet, endMinute=endMinuteGet, endAMorPM=endAMorPMGet, dateDay=dateDayGet, dateMonth=dateMonthGet, dateYear=dateYearGet)
            reservation.put()
            self.redirect('/resource?reservationUniqueID='+uniqueID+'&resourceUniqueID='+resourceUniqueID+'&startHour='+str(startHourGet)+'&startMinute='+str(startMinuteGet)+'&startAMorPM='+startAMorPMGet+'&endHour='+str(endHourGet)+'&endMinute='+str(endMinuteGet)+'&endAMorPM='+endAMorPMGet+'&dateDay='+str(dateDayGet)+'&dateMonth='+str(dateMonthGet)+'&dateYear='+str(dateYearGet)+'&sizeGet='+str(len(index_list)))

class ViewResource(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        resourceUniqueID = self.request.get('resourceUniqueID')
        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]

        reservationUniqueID = self.request.get('reservationUniqueID')
        reservations_for_resource = list(Reservation.gql("WHERE resourceUniqueID = :1", resourceUniqueID))

        reservationsToDelete = list()
        for e in reservations_for_resource:
            endHour = e.endHour
            if e.endAMorPM == 'PM':
                endHour = e.endHour + 12
            
            todaysDate = datetime.datetime.now()
            delta = datetime.timedelta(hours = 5)
            todaysDate = todaysDate - delta
            reservationDateTime = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, endHour, e.endMinute)
            if todaysDate > reservationDateTime:
                reservationsToDelete.append(e)

        for x in reservationsToDelete:
            reservations_for_resource = [e for e in reservations_for_resource if e.uniqueID != x.uniqueID]

        template = JINJA_ENVIRONMENT.get_template('resource.html')
        template_values = {
            'resource': resource,
            'reservations': reservations_for_resource,
        }
        self.response.write(template.render(template_values))

class ViewByTag(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        tag = self.request.get('tag')
        resourcesByTag = list(Resource.gql(""))

        resourcesToDelete = list()
        for x in resourcesByTag:
            if not(tag in x.tags):
                resourcesToDelete.append(x)

        for x in resourcesToDelete:
            resourcesByTag = [e for e in resourcesByTag if e.uniqueID != x.uniqueID]

        template = JINJA_ENVIRONMENT.get_template('tag.html')
        template_values = {
            'resources': resourcesByTag,
            'tag': tag,
        }
        self.response.write(template.render(template_values))

class JunkStuff(ndb.Model):
    value = ndb.StringProperty(indexed=True)

class CronTasker(webapp2.RequestHandler):
    def get(self):
        val = 1

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/addResource', AddResource),
    ('/addReservation', AddReservation),
    ('/resource', ViewResource),
    ('/editResource', AddResource),
    ('/tags', ViewByTag),
    ('/crontask', CronTasker),
], debug=True)