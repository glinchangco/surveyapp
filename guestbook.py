import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'


# We set a parent key on the 'Surveys' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)

class QuestionResponse(ndb.Model):
    question = ndb.StringProperty(indexed=False)
    response = ndb.StringProperty(indexed=False)


class SurveyResponse(ndb.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    question_responses = ndb.StructuredProperty(QuestionResponse, repeated=True)    


class ResultsPage(webapp2.RequestHandler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        surveys_query = SurveyResponse.query(
            ancestor=guestbook_key(guestbook_name)).order(-SurveyResponse.date)
        survey_responses = surveys_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        QUESTION_NAME = 'Best dog question'
        result_summary = {
          QUESTION_NAME: {}
        }
        for survey_response in survey_responses:
            # get this person's response to question 0
            favorite_resp = survey_response.question_responses[0].response
            # initialize our counter for this response if we have to
            if favorite_resp not in result_summary[QUESTION_NAME]:
                result_summary[QUESTION_NAME][favorite_resp] = 0
            # increment the counter for this response
            result_summary[QUESTION_NAME][favorite_resp] += 1
        # end for

        total_responses = len(survey_responses)
        template_values = {
            'total_responses': total_responses,
            'result_summary': result_summary,
            'survey_responses': survey_responses,
            'url': url,
            'url_linktext': url_linktext,
            'Frank':"woof"
        }

        template = JINJA_ENVIRONMENT.get_template('results.html')
        self.response.write(template.render(template_values))

class MainPage(webapp2.RequestHandler):

    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        surveys_query = SurveyResponse.query(
            ancestor=guestbook_key(guestbook_name)).order(-SurveyResponse.date)
        survey_responses = surveys_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'survey_responses': survey_responses,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class SurveyResponseHandler(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Survey' to ensure each Survey
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        survey_response = SurveyResponse(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            survey_response.author = users.get_current_user()

        survey_response.question_responses = [
          QuestionResponse(
            question='Best Dogs Response',
            response=self.request.get('comment')),
          QuestionResponse(
            question='sex response',
            response=self.request.get('sex'))]


        # to add a second question
        # you need to add the question to the UI (index.html)
        # then save it to the database here

    
        survey_response.put()
        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/results', ResultsPage),
    ('/sign', SurveyResponseHandler),
], debug=True)
