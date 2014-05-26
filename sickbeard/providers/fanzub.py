# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import urllib

import sickbeard
import generic

from sickbeard import classes, show_name_helpers, helpers

from sickbeard import exceptions, logger
from sickbeard.common import *
from sickbeard import tvcache
from lib.dateutil.parser import parse as parseDate

class Fanzub(generic.NZBProvider):

    def __init__(self):

        generic.NZBProvider.__init__(self, "Fanzub")

        self.supportsBacklog = False
        self.supportsAbsoluteNumbering = True

        self.enabled = False

        self.cache = FanzubCache(self)

        self.url = 'http://fanzub.com/'

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'fanzub.gif'

    def _checkAuth(self):
        return True

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _doSearch(self, search_string, epcount=0, age=0):
        if self.show and not self.show.is_anime:
            logger.log(u"" + str(self.show.name) + " is not an anime skiping ...")
            return []

        params = {
            "cat": "anime",
            "q": search_string.encode('utf-8'),
            "max": "100"
        }

        search_url = self.url + "rss?" + urllib.urlencode(params)

        logger.log(u"Search url: " + search_url, logger.DEBUG)

        data = self.cache.getRSSFeed(search_url)
        if not data:
            return []

        if 'entries' in data:

            items = data.entries
            results = []

            for curItem in items:
                (title, url) = self._get_title_and_url(curItem)

                if title and url:
                    results.append(curItem)
                else:
                    logger.log(
                        u"The data returned from the " + self.name + " is incomplete, this result is unusable",
                        logger.DEBUG)

            return results

        return []

    def findPropers(self, date=None):

        results = []

        for i in [2, 3, 4]: # we will look for a version 2, 3 and 4
            """
            because of this the proper search failed !!
            well more precisly because _doSearch does not accept a dict rather then a string
            params = {
                "q":"v"+str(i).encode('utf-8')
                  }
            """
            for curResult in self._doSearch("v" + str(i)):

                match = re.search('(\w{3}, \d{1,2} \w{3} \d{4} \d\d:\d\d:\d\d) [\+\-]\d{4}', curResult.findtext('pubDate'))
                if not match:
                    continue

                dateString = match.group(1)
                resultDate = parseDate(dateString).replace(tzinfo=None)

                if date == None or resultDate > date:
                    results.append(classes.Proper(curResult.findtext('title'), curResult.findtext('link'), resultDate))

        return results

class FanzubCache(tvcache.TVCache):

    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll Fanzub every 20 minutes max
        # we get 100 post each call !
        self.minTime = 20


    def _getRSSData(self):

        params = {"cat": "anime".encode('utf-8'),
                 "max": "100".encode('utf-8')
        }

        rss_url = self.provider.url + 'rss?' + urllib.urlencode(params)

        logger.log(self.provider.name + u" cache update URL: " + rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url)

    def _checkAuth(self, data):
        return self.provider._checkAuthFromData(data)

provider = Fanzub()