#! /usr/bin/env python
#
# This little tool takes a username and a list of tags to watch out for,
# then finds all tweets that are newer than the last message of the given
# user matching either the username or the given tags.
#
# Copyright (c) 2011, Jan Schaumann. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL <COPYRIGHT HOLDER> OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Originally written by Jan Schaumann <jschauma@netmeister.org> in
# February 2011.

import getopt
import os
from os.path import basename
import re
import sys
import time
import tweepy
import urllib

###
### Globals
###

EXIT_ERROR = 1
EXIT_SUCCESS = 0

VERSION = "0.1"

# limited to 150 calls / hour = 3600/150 = 24 econds
INTERVAL = 30

###
### Classes
###

class FindTweets(object):
    """A simple Track Bot Retweeter kinda thing."""

    def __init__(self):
        """Construct a Track Bot object with default values."""

        self.__opts = {
                    "user" : "",
                    "tags" : []
                 }
        self.msg = ""
        self.verbosity = 0


    class Usage(Exception):
        """A simple exception that provides a usage statement and a return code."""

        def __init__(self, rval):
            self.err = rval
            self.msg = 'Usage: %s [-hv] [-t tag] [-u user]\n' % os.path.basename(sys.argv[0])
            self.msg += '\t-t tag  monitor given tag\n'
            self.msg += '\t-u user monitor given user\n'
            self.msg += '\t-h      print this message and exit\n'
            self.msg += '\t-v      be more verbose\n'


    def getOpt(self, opt):
        """Retrieve the given configuration option.

        Returns:
            The value for the given option if it exists, None otherwise.
        """

        try:
            r = self.__opts[opt]
        except KeyError:
            r = None

        return r



    def parseOptions(self, inargs):
        """Parse given command-line options and set appropriate attributes.

        Arguments:
            inargs -- arguments to parse

        Returns:
            the list of arguments remaining after all flags have been
            processed

        Raises:
            Usage -- if '-h' or invalid command-line args are given
        """

        try:
            opts, args = getopt.getopt(inargs, "ht:u:v")
        except getopt.GetoptError:
            raise self.Usage(EXIT_ERROR)

        for o, a in opts:
            if o in ("-h"):
                raise self.Usage(EXIT_SUCCESS)
            if o in ("-t"):
                tags = self.getOpt("tags")
                tags.append(a)
                self.setOpt("tags", tags)
            if o in ("-u"):
                self.setOpt("user", a)
            if o in ("-v"):
                self.verbosity = self.verbosity + 1

        return args


    def setOpt(self, opt, val):
        """Set the given option to the provided value"""

        self.__opts[opt] = val


    def verbose(self, msg, level=1):
        """Print given message to STDERR if the object's verbosity is >=
        the given level"""

        if (self.verbosity >= level):
            sys.stderr.write("%s> %s\n" % ('=' * level, msg))


    def findTweets(self):
        """Get the message ids of all tweets of interest.

        Somewhat inspired by:
            http://blog.picloud.com/2010/08/12/making-a-twitter-bot/
        """

        tags = self.getOpt("tags")
        user = self.getOpt("user")
        last = tweepy.api.search(q="from:%s" % user)[0]
        if last:
            created_after = last.created_at
            last_id = last.id
        else:
            # if we've never retweeted before, then we're going to
            # retweet all msgs created after the 20th century, ie. all of them
            created_after = datetime.datetime(year=2000, month=1, day=1)
            last_id = 0

        tweets = []
        for tag in tags:
            # grab all tweets that include our keyword
            taglist = tweepy.api.search(q="#%s" % tag, since_id=last_id, rpp=100)
            self.verbose("Got %d tweets for #%s." % (len(taglist), tag), 2)
            tweets.extend(taglist)

        tweets.extend(tweepy.api.search(q="@%s" % user, since_id=last_id, rpp=100))
        # reverse them to get the oldest first
        tweets.reverse()
        self.verbose("Got %d tweets in total." % len(tweets))
        ids = []
        for tweet in tweets:
            # if the tweet is new, and was not made from our account, retweet it
            if tweet.created_at > created_after and tweet.from_user != user:
                ids.append(str(tweet.id))
        if ids:
            print "\n".join(ids)

###
### Methods
###

###
### "Main"
###

if __name__ == "__main__":
    try:
        ft = FindTweets()
        try:
            args = ft.parseOptions(sys.argv[1:])
            ft.findTweets()

        except ft.Usage, u:
            if (u.err == EXIT_ERROR):
                out = sys.stderr
            else:
                out = sys.stdout
            out.write(u.msg)
            sys.exit(u.err)
	        # NOTREACHED

    except KeyboardInterrupt:
        # catch ^C, so we don't get a "confusing" python trace
        sys.exit(EXIT_ERROR)
