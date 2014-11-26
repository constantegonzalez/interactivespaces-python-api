#!/usr/bin/env python
# -*- coding: utf-8 -*-

from exception import PathException
from misc import Logger
import requests
import urllib2
import urlparse
import json
import os

class APICallException(Exception):
    pass

class APICall:
    def __init__(self, url):
        self.url = url
        self.log = Logger().get_logger()

    def getUrl(self):
        return "%s%s" % (self.uri, self.url)

    def setUri(self,uri):
        self.uri = uri

    def canCall(self):
        try:
            if not self.uri:
                raise APICallException("URI must be set (use setUri() method) before calling this APICall object")
        except AttributeError, e:
            raise APICallException("URI must be set (use setUri() method) before calling this APICall object")
        return True

    def call(self):
        # Poor man's abstract class
        raise Exception("Instantiate some APICall subclass; don't call it directly.")

    def parameterize(self, params):
        if self.url.find("%s"):
            self.url = self.url % params

    def getUrl(self):
        return "%s%s" % (self.uri, self.url)

class RESTCall(APICall):
    def call(self, params=None, file_handler=False, cookies=False):
        if not self.canCall():
            return

        if file_handler:
            head, tail = os.path.split(file_handler.name)
            file_name = tail
            file_content_type = "application/zip"
            files = {"activityFile" : (file_name , file_handler, file_content_type)}
        else:
            files = None

        self.log.info("Trying url %s" % self.getUrl())

        if cookies == False and params == None:
            response = urllib2.urlopen(self.getUrl())
            response_str = response.read()

            try:
                data = json.loads(response_str)
                out_data = data['data']
                if data['result'] != 'success':
                    self.log.info("Could not retrieve data for URL=%s" % url)
                    return False
            except Exception:
                out_data = None

            return out_data
        else:
            session = requests.session()
            get_response = session.get(self.getUrl())
            query = urlparse.urlparse(get_response.url).query
            cookies = {"JSESSIONID" : session.cookies['JSESSIONID']}
            url = self.getUrl() + "?" + query
            post_response = session.post(url=url, cookies=cookies, data=params, files=files) 
            if post_response.status_code == 200:
                self.log.info("_api_post_json returned 200 with post_response.url=%s" % post_response.url)
                return post_response
            else:
                self.log.info("_api_post_json returned post_response.status_code %s" % post_response.status_code)
                return False

class WebSocketCall(APICall):
    def call(self):
        if not self.canCall():
            return
        raise Exception("WebSocketCall.call() isn't yet implemented")

class Path(object):
    '''
    Should be responsible for static translation of routes
    '''
    def __init__(self):
        self.routes = {
                       'Master': {
                            'get_activities' : '/activity/all.json',
                            'get_live_activities' : '/liveactivity/all.json',
                            'get_live_activity_groups' : '/liveactivitygroup/all.json',
                            'get_spaces' : '/space/all.json',
                            'get_space_controllers' : '/spacecontroller/all.json',
                            'get_named_scripts' : '/admin/namedscript/all.json',
                            'new_live_activity_group' : '/liveactivitygroup/new',
                            'new_space' : '/space/new.json',
                            'new_controller' : '/spacecontroller/new.json',
                            'new_named_script' : '/admin/namedscript/new.json'
                            },
                       'Activity' : {
                            'view' : '/activity/%s/view.json',
                            'upload' : '/activity/upload',
                            'delete' : '/activity/%s/delete.html'
                            },
                       'LiveActivity' : {
                            'status' : '/liveactivity/%s/status.json',
                            'view' : '/liveactivity/%s/view.json',
                            'new' : '/liveactivity/new',
                            'delete' : '/liveactivity/%s/delete.html',
                            'shutdown' : '/liveactivity/%s/shutdown.json',
                            'startup' : '/liveactivity/%s/startup.json',
                            'activate' : '/liveactivity/%s/activate.json',
                            'deactivate' : '/liveactivity/%s/deactivate.json',
                            'deploy' : '/liveactivity/%s/deploy.json',
                            'configure' : '/liveactivity/%s/configure.json',
                            'clean_tmp' : '/liveactivity/%s/cleantmpdata.json',
                            'clean_permanent' : '/liveactivity/%s/cleanpermanentdata.json',
                            'metadata' : '/liveactivity/%s/metadata/edit'
                            },
                       'LiveActivityGroup' : {
                            'view' : '/liveactivitygroup/%s/view.json',
                            'new' : '/liveactivitygroup/new',
                            'status' : '/liveactivitygroup/%s/liveactivitystatus.json',
                            'delete' : '/liveactivitygroup/%s/delete.html',
                            'shutdown' : '/liveactivitygroup/%s/shutdown.json',
                            'startup' : '/liveactivitygroup/%s/startup.json',
                            'activate' : '/liveactivitygroup/%s/activate.json',
                            'deactivate' : '/liveactivitygroup/%s/deactivate.json',
                            'deploy' : '/liveactivitygroup/%s/deploy.json',
                            'configure' : '/liveactivitygroup/%s/configure.json',
                            'metadata' : '/liveactivitygroup/%s/metadata/edit',
                            'edit' : '/liveactivitygroup/%s/edit.json'
                            },
                       'Space' : {
                            'new' : '/space/new',
                            'view' : '/space/%s/view.json',
                            'status' : '/space/%s/status.json',
                            'delete' : '/space/%s/delete.html',
                            'shutdown' : '/space/%s/shutdown.json',
                            'startup' : '/space/%s/startup.json',
                            'activate' : '/space/%s/activate.json',
                            'deactivate' : '/space/%s/deactivate.json',
                            'deploy' : '/space/%s/deploy.json',
                            'configure' : '/space/%s/configure.json',
                            'metadata' : '/space/%s/metadata/edit'
                            },
                       'SpaceController' :{
                            'new' : '/spacecontroller/new',
                            'view' : '/spacecontroller/%s/view.json',
                            'status': '/spacecontroller/%s/status.json',
                            'delete': '/spacecontroller/%s/delete.html',
                            'shutdown': '/spacecontroller/%s/shutdown.json',
                            'deploy': '/spacecontroller/%s/deploy.json',
                            'connect' : '/spacecontroller/%s/connect.json',
                            'disconnect' : '/spacecontroller/%s/disconnect.json'
                            }
                        }

        self.log = Logger().get_logger()

    def get_route_for(self, class_name, method_name, param=None):
        """
        Should receive caller class name and caller method in order
        to return a proper route in the master API
            
        :rtype: string
        """
        try:
            r = self.routes[class_name][method_name]
            if not isinstance(r, APICall):
                # Default to RESTCall, not WebSocketCall
                r = RESTCall(r)

            if param != None:
                r.parameterize(param)

            return r
        except PathException, e:
            self.log.info("Could not return route for class_name %s and method %s because %s" % (class_name, method_name, e))
