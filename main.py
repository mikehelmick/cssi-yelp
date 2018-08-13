import jinja2
import webapp2
import os
import json
import urllib
import urllib2
from google.appengine.ext import ndb

jinja_environment = jinja2.Environment(
    loader = jinja2.FileSystemLoader(
        os.path.dirname(__file__) + '/templates'))

class UserSearch(ndb.Model):
    term = ndb.StringProperty(required=True)
    count = ndb.IntegerProperty(required=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def increment(self):
        self.count = self.count + 1

    def encode_term(self):
        return urllib.urlencode({'q': self.term})


@ndb.transactional
def updateSearchCount(term):
    lterm = term.lower()
    # create key
    key = ndb.Key('UserSearch', lterm)
    # Read database
    search = key.get()
    if not search:
        # Create if not there
        search = UserSearch(key=key, count=0, term=term)
    # Update count
    search.increment()
    # Save
    search.put()

def getRecentSearches():
    return UserSearch.query().order(-UserSearch.created_at).fetch(limit=10)

def getPopularSearches():
    return UserSearch.query().order(-UserSearch.count).fetch(limit=10)

class RecentPage(webapp2.RequestHandler):
    def get(self):
        searches = getRecentSearches()

        template = jinja_environment.get_template('recent.html')
        variables = {'searches': searches}
        self.response.write(template.render(variables))

class PopularPage(webapp2.RequestHandler):
    def get(self):
        searches = getPopularSearches()

        template = jinja_environment.get_template('popular.html')
        variables = {'searches': searches}
        self.response.write(template.render(variables))


class MainPage(webapp2.RequestHandler):
    def get(self):
        search_term = self.request.get('q')
        if search_term:
            lterm = search_term.lower()
            # create key
            key = ndb.Key('UserSearch', lterm)
            # Read database
            search = key.get()
            if not search:
                # Create if not there
                search = UserSearch(
                    key=key, count=0,
                    term=search_term)
            # Update count
            search.increment()
            # Save
            search.put()
        else:
            search_term = "coffee"
        params = {'term': search_term,
                  'location': 'San Marcos, California'}
        form_data = urllib.urlencode(params)
        api_url = 'https://api.yelp.com/v3/businesses/search?' + form_data

        # Add your own API key
        request = urllib2.Request(api_url, headers={"Authorization" : "Bearer API_KEY"})
        response = urllib2.urlopen(request).read()
        content = json.loads(response)

        template = jinja_environment.get_template('main.html')
        variables = {'content': content,
                     'q': search_term}
        self.response.write(template.render(variables))

app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/recent', RecentPage),
  ('/popular', PopularPage),
])
