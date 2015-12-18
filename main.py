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
from google.appengine.api import mail

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
    endHour = ndb.IntegerProperty(indexed=False)
    endMinute = ndb.IntegerProperty(indexed=False)
    dateDay = ndb.IntegerProperty()
    dateMonth = ndb.IntegerProperty()
    dateYear = ndb.IntegerProperty()
    name = ndb.StringProperty(indexed=False)
    duration = ndb.IntegerProperty(indexed=False)

class Resource(ndb.Model):
    uniqueID = ndb.StringProperty(indexed=True)
    user = ndb.UserProperty()
    name = ndb.StringProperty(indexed=False)
    startHour = ndb.IntegerProperty(indexed=False)
    startMinute = ndb.IntegerProperty(indexed=False)
    endHour = ndb.IntegerProperty(indexed=False)
    endMinute = ndb.IntegerProperty(indexed=False)
    tags = ndb.StringProperty(repeated=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        showUsers = self.request.get('showUsers')
        resourceNameGet = self.request.get('resourceName')
        if not( resourceNameGet == "" ):
            startMinuteGet = int(self.request.get('startMinute'))
            endHourGet = int(self.request.get('endHour'))
            endMinuteGet = int(self.request.get('endMinute'))
            tagsGet = self.request.get('tags')
            sizeInt = int(self.request.get('sizeGet'))
            uniqueID = self.request.get('uniqueID')
            editResource = self.request.get('editResource')
            startHourGet = int(self.request.get('startHour'))

        resources_for_user = Resource.gql("WHERE user = :1", user)
        index_list = list(resources_for_user)
        
        index_list.sort(key=lambda x: x.name)

        reservations = list(Reservation.gql("WHERE user = :1", user))

        reservationsToDelete = list()
        for e in reservations:
            todaysDate = datetime.datetime.now()
            delta = datetime.timedelta(hours = 5)
            todaysDate = todaysDate - delta
            reservationDateTime = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, e.endHour, e.endMinute)
            if todaysDate > reservationDateTime:
                reservationsToDelete.append(e)

        for x in reservationsToDelete:
            reservations = [e for e in reservations if e.uniqueID != x.uniqueID]

        for e in reservations:
            results = list(Resource.gql("WHERE uniqueID = :1", e.resourceUniqueID))
            if len(results) > 0:
                res = results[0]
                e.name = res.name

        reservations.sort(key = lambda x: (x.dateYear, x.dateMonth, x.dateDay, x.endHour, x.endMinute, x.name))

        allReservations = list(Reservation.gql(""))
        allResources = list(Resource.gql(""))

        allReservations.sort(key = lambda x: (x.dateYear, x.dateMonth, x.dateDay, x.endHour, x.endMinute, x.name), reverse=True)

        resourcesDone = list()
        for e in allReservations:
            for x in allResources:
                if x.uniqueID == e.resourceUniqueID and x not in resourcesDone:
                    resourcesDone.append(x)

        for x in allResources:
            if x not in resourcesDone:
                resourcesDone.append(x)

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resources_for_user': index_list,
            'reservations': reservations,
            'allResources': resourcesDone,
            'showUsers': str(showUsers),
        }
        
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class AddResource(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        resourceNameGet = self.request.get('resourceName')
        if resourceNameGet:
            startHourGet = int(self.request.get('startHour'))
            startMinuteGet = int(self.request.get('startMinute'))
            endHourGet = int(self.request.get('endHour'))
            endMinuteGet = int(self.request.get('endMinute'))
            tagsGet = self.request.get('tags')
            userGet = users.get_current_user()
            editResource = self.request.get('editResource')
            uniqueID = self.request.get('uniqueID')

            resource = list(Resource.gql("WHERE uniqueID = :1", uniqueID))[0]
            tagsList = resource.tags

            tagsList = ','.join(map(str, tagsList)) 
        
            template_values = {
                'resourceName': resourceNameGet,
                'startHour': startHourGet,
                'startMinute': startMinuteGet,
                'endHour': endHourGet,
                'endMinute': endMinuteGet,
                'tags': tagsList,
                'editResource': editResource,
                'uniqueID': uniqueID,
                'url': url,
                'url_linktext': url_linktext,
            }

        else:
            template_values = {
            }

        template = JINJA_ENVIRONMENT.get_template('addResource.html')
        
        self.response.write(template.render(template_values))

    def post(self):
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        resourceNameGet = self.request.get('resourceName')
        startHourGet = int(self.request.get('startHour'))
        startMinuteGet = int(self.request.get('startMinute'))
        endHourGet = int(self.request.get('endHour'))
        endMinuteGet = int(self.request.get('endMinute'))
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
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'tags': tagsGet,
              'editResource': editResource,
              'uniqueID': uniqueID,
              'url': url,
              'url_linktext': url_linktext,
            }
            template = JINJA_ENVIRONMENT.get_template('addResource.html')
            self.response.write(template.render(template_values))
            return

        if startHourGet > endHourGet or ( startHourGet == endHourGet and startMinuteGet >= endMinuteGet):
            template_values = {
              'error': 'End Time must be after the Start Time',
              'resourceName': resourceNameGet,
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'endHour': endHourGet,
              'endMinute': endMinuteGet,
              'tags': tagsGet,
              'editResource': editResource,
              'uniqueID': uniqueID,
              'url': url,
              'url_linktext': url_linktext,
            }
            template = JINJA_ENVIRONMENT.get_template('addResource.html')
            self.response.write(template.render(template_values))
            return

        resources_for_user = Resource.gql("WHERE user = :1", userGet)
        
        index_list = list(resources_for_user)

    
        if editResource == "true":
            resource = Resource.query(Resource.uniqueID == uniqueID).get()
            resource.name = resourceNameGet
            resource.startHour = startHourGet
            resource.startMinute = startMinuteGet
            resource.endHour = endHourGet
            resource.endMinute = endMinuteGet
            if len(tagsGet) > 0:
                tokens = tagsGet.split(',')
                tokens = [ s.strip() for s in tokens ]
                resource.tags = tokens
                resource.put()
                self.redirect('/notifyUser?value=resourceModified&url='+url+'&url_linktext='+url_linktext)
            else:
                resource.put()
                self.redirect('/notifyUser?value=resourceModified&url='+url+'&url_linktext='+url_linktext)
        else:    
            uniqueID = str(uuid.uuid4())
            if not(tagsGet is None or tagsGet == ""):
                tokens = tagsGet.split(',')
                tokens = [ s.strip() for s in tokens ]
                resource = Resource(uniqueID=uniqueID, user=userGet, name=resourceNameGet, startHour=startHourGet, startMinute=startMinuteGet, endHour=endHourGet, endMinute=endMinuteGet, tags=tokens)
                resource.put()
                self.redirect('/notifyUser?value=resourceAdded&url='+url+'&url_linktext='+url_linktext)
            else:
                resource = Resource(uniqueID=uniqueID, user=userGet, name=resourceNameGet, startHour=startHourGet, startMinute=startMinuteGet, endHour=endHourGet, endMinute=endMinuteGet)
                resource.put()
                self.redirect('/notifyUser?value=resourceAdded&url='+url+'&url_linktext='+url_linktext)

class AddReservation(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
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
            'url': url,
            'url_linktext': url_linktext,
        }
        self.response.write(template.render(template_values))

    def post(self):
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        year = int(time.strftime("%Y"))
        startHourGet = int(self.request.get('startHour'))
        startMinuteGet = int(self.request.get('startMinute'))
        dateYearGet = int(self.request.get('dateYear'))
        dateMonthGet = int(self.request.get('dateMonth'))
        dateDayGet = int(self.request.get('dateDay'))
        durationGet = int(self.request.get('duration'))
        userGet = users.get_current_user()
        resourceUniqueID = self.request.get('resourceUniqueID')

        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]

        try:
            requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, startHourGet, startMinuteGet)
            delta = datetime.timedelta(seconds = durationGet * 60)
            requestReservationEndTime = requestReservationStartTime + delta

        except ValueError:
            template_values = {
              'error': 'Date/duration is incorrect! :)',
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'dateYear': dateYearGet,
              'dateMonth': dateMonthGet,
              'dateDay': dateDayGet,
              'resourceUniqueID': resourceUniqueID,
              'resource': resource,
              'todaysYear':year,
              'duration': durationGet,
              'url': url,
              'url_linktext': url_linktext,
            }
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            self.response.write(template.render(template_values))
            return

        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]

        requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, startHourGet, startMinuteGet)
        delta = datetime.timedelta(seconds = durationGet * 60)
        requestReservationEndTime = requestReservationStartTime + delta
        resourceStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, resource.startHour, resource.startMinute)
        resourceEndTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, resource.endHour, resource.endMinute)

        if requestReservationStartTime < resourceStartTime or requestReservationEndTime > resourceEndTime:
            template_values = {
              'error': 'Resource is not available during those times!',
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'dateYear': dateYearGet,
              'dateMonth': dateMonthGet,
              'dateDay': dateDayGet,
              'resourceUniqueID': resourceUniqueID,
              'resource': resource,
              'todaysYear':year,
              'duration': durationGet,
              'url': url,
              'url_linktext': url_linktext,
            }
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            self.response.write(template.render(template_values))
            return

        requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, startHourGet, startMinuteGet)
        todaysDate = datetime.datetime.now()
        delta = datetime.timedelta(hours = 5)
        todaysDate = todaysDate - delta

        if todaysDate > requestReservationStartTime:
            template_values = {
              'error': 'Choose a time after the NOW! :)',
              'startHour': startHourGet,
              'startMinute': startMinuteGet,
              'dateYear': dateYearGet,
              'dateMonth': dateMonthGet,
              'dateDay': dateDayGet,
              'resourceUniqueID': resourceUniqueID,
              'resource': resource,
              'todaysYear':year,
              'duration': durationGet,
              'url': url,
              'url_linktext': url_linktext,
            }
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            self.response.write(template.render(template_values))
            return

        overlapReservation = False
        reservations_for_resource = Reservation.gql("WHERE resourceUniqueID = :1 AND dateYear = :2 AND dateMonth = :3 AND dateDay = :4", resourceUniqueID, dateYearGet, dateMonthGet, dateDayGet)
        for e in reservations_for_resource:
            reservationStart = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, e.startHour, e.startMinute)
            reservationEnd = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, e.endHour, e.endMinute) - datetime.timedelta(seconds = 60)
            requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, startHourGet, startMinuteGet)
            delta = datetime.timedelta(seconds = durationGet * 60)
            requestReservationEndTime = requestReservationStartTime + delta - datetime.timedelta(seconds = 60)

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
                'dateYear': dateYearGet,
                'dateMonth': dateMonthGet,
                'dateDay': dateDayGet,
                'resourceUniqueID': resourceUniqueID,
                'resource': resource,
                'todaysYear':year,
                'duration': durationGet,
                'url': url,
                'url_linktext': url_linktext,
            }

            self.response.write(template.render(template_values))
        else:
            uniqueID = str(uuid.uuid4())
            requestReservationStartTime = datetime.datetime(dateYearGet, dateMonthGet, dateDayGet, startHourGet, startMinuteGet)
            delta = datetime.timedelta(seconds = durationGet * 60)
            requestReservationEndTime = requestReservationStartTime + delta
            endHourGet = int(requestReservationEndTime.hour)
            endMinuteGet = int(requestReservationEndTime.minute)
            reservation = Reservation(uniqueID=uniqueID, user=userGet, resourceUniqueID=resourceUniqueID, startHour=startHourGet, startMinute=startMinuteGet, endHour=endHourGet, endMinute=endMinuteGet, dateDay=dateDayGet, dateMonth=dateMonthGet, dateYear=dateYearGet, duration=durationGet)
            reservation.put()
            sendEmail(reservation, False)
            self.redirect('/notifyUser?value=reservationAdded&url='+url+'&url_linktext='+url_linktext)

class NotifyUser(webapp2.RequestHandler):
    def get(self):
        value = self.request.get('value')
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_values = {
            'value': value,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('notifyUser.html')
        self.response.write(template.render(template_values))


class ViewResource(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        reservationUniqueID = self.request.get('reservationUniqueID')
        resourceUniqueID = self.request.get('resourceUniqueID')
        
        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]

        reservationUniqueID = self.request.get('reservationUniqueID')
        reservations_for_resource = list(Reservation.gql("WHERE resourceUniqueID = :1", resourceUniqueID))

        reservationsToDelete = list()
        for e in reservations_for_resource:
            todaysDate = datetime.datetime.now()
            delta = datetime.timedelta(hours = 5)
            todaysDate = todaysDate - delta
            reservationDateTime = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, e.endHour, e.endMinute)
            if todaysDate > reservationDateTime:
                reservationsToDelete.append(e)

        for x in reservationsToDelete:
            reservations_for_resource = [e for e in reservations_for_resource if e.uniqueID != x.uniqueID]

        template = JINJA_ENVIRONMENT.get_template('resource.html')

        tagsWork = True
        if len(resource.tags) == 0:
            tagsWork = False

        editActive = user == resource.user
        template_values = {
            'resource': resource,
            'reservations': reservations_for_resource,
            'tagsWork': tagsWork,
            'editActive': str(editActive),
            'url': url,
            'url_linktext': url_linktext,
        }
        self.response.write(template.render(template_values))

class DeleteReservation(webapp2.RequestHandler):
    def get(self):
        reservationUniqueID = self.request.get('reservationUniqueID')
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))

        reservation = Reservation.query(Reservation.uniqueID == reservationUniqueID).get()

        if user != reservation.user:
            self.redirect('/notifyUser?value=reservationNotUser&url='+url+'&url_linktext='+url_linktext)
            return

        reservation.key.delete()
        self.redirect('/notifyUser?value=reservationDeleted&url='+url+'&url_linktext='+url_linktext)

class ViewByTag(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
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
            'url': url,
            'url_linktext': url_linktext,
        }
        self.response.write(template.render(template_values))

def sendEmail(reservation, timeToStart):
    resource = list(Resource.gql("WHERE uniqueID = :1", reservation.resourceUniqueID))[0]

    if timeToStart:
        mail.send_mail(sender="al4251@nyu.edu",
                        to=str(reservation.user),
                        subject="Your reservation for "+resource.name+" is coming up!!",
                        body = "Hi Your reservation for " + resource.name + " is in 5 minutes. Thank you for using the OST Reservation System. ")
    else:
         mail.send_mail(sender="al4251@nyu.edu",
                        to=str(reservation.user),
                        subject="Your reservation for "+resource.name+" is confirmed!!",
                        body = "Hi Your reservation for " + resource.name + " is confirmed. Thank you for using the OST Reservation System. ")

class CronTasker(webapp2.RequestHandler):
    def get(self):
        reservations = list(Reservation.gql(""))
        todaysDate = datetime.datetime.now()
        delta = datetime.timedelta(hours = 5)
        todaysDate = todaysDate - delta
        delta = datetime.timedelta(seconds = 300)
        todaysDate = todaysDate + delta

        for e in reservations:
            reservationDateTime = datetime.datetime(e.dateYear, e.dateMonth, e.dateDay, e.startHour, e.startMinute)
        
            if todaysDate.year == reservationDateTime.year and todaysDate.month == reservationDateTime.month and todaysDate.day == reservationDateTime.day and todaysDate.hour == reservationDateTime.hour and todaysDate.minute == reservationDateTime.minute:
                sendEmail(e, True)

class GenerateRSS(webapp2.RequestHandler):
    def get(self):
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        resourceUniqueID = self.request.get('resourceUniqueID')
        resource = list(Resource.gql("WHERE uniqueID = :1", resourceUniqueID))[0]
        reservations_for_resource = list(Reservation.gql("WHERE resourceUniqueID = :1", resourceUniqueID))

        template = JINJA_ENVIRONMENT.get_template('rssGenerator.html')
        template_values = {
            'resource': resource,
            'reservations_for_resource': reservations_for_resource,
            'url': url,
            'url_linktext': url_linktext,
        }  
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/addResource', AddResource),
    ('/addReservation', AddReservation),
    ('/resource', ViewResource),
    ('/editResource', AddResource),
    ('/tags', ViewByTag),
    ('/crontask', CronTasker),
    ('/notifyUser', NotifyUser),
    ('/generateRSS', GenerateRSS),
    ('/deleteReservation', DeleteReservation),
], debug=True)