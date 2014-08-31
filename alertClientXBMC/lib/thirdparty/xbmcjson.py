#!/bin/env python

# downloaded from https://github.com/jcsaaddupuy/python-xbmc

import urllib, urllib2
import json
from StringIO import StringIO

PLAYER_VIDEO=1

class XBMCTransport(object):
  """Base class for XBMC transport"""
  def execute(self, method, args):
    pass

class XBMCJsonTransport(XBMCTransport):
  """HTTP Json transport"""
  def __init__(self, url, username='xbmc', password='xbmc'):
    self.url=url
    self.username=username
    self.password=password
    self.id = 0

  def execute(self, method, *args, **kwargs):
    header = {
        'Content-Type' : 'application/json',
        'User-Agent' : 'python-xbmc'
        }
    # Params are given as a dictionnary
    if len(args) == 1:
      args=args[0]
    # Use kwargs for param=value style
    else:
      args = kwargs
    params={}
    params['jsonrpc']='2.0'
    params['id']=self.id
    self.id +=1
    params['method']=method
    params['params']=args

    values=json.dumps(params)
    # HTTP Authentication
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm() 
    password_mgr.add_password(None, self.url, self.username, self.password) 
    auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(auth_handler) 
    urllib2.install_opener(opener)

    data = values
    req = urllib2.Request(self.url, data, header)
    response = urllib2.urlopen(req)
    the_page = response.read()
    if len(the_page) > 0 :
      return json.load(StringIO(the_page))
    else:
      return None # for readability

class XBMC(object):
  """XBMC client"""
  def __init__(self, url, username='xbmc', password='xbmc'):
    self.transport = XBMCJsonTransport(url, username, password)
    # Dynamic namespace class instanciation
    for cl in namespaces:
      s = "self.%s = %s(self.transport)"%(cl,cl)
      exec(s)
    def execute(self, *args, **kwargs):
      self.transport.execute(*args, **kwargs)

class XBMCNamespace(object):
  """Base class for XBMC namespace."""
  def __init__(self, xbmc):
    self.xbmc = xbmc
  def __getattr__(self, name):
    klass= self.__class__.__name__
    method=name
    xbmcmethod = "%s.%s"%(klass, method)
    def hook(*args, **kwargs):
      return self.xbmc.execute(xbmcmethod, *args, **kwargs)
    return hook

# Dynamic namespace class injection
namespaces = ["VideoLibrary", "AudioLibrary", "Application", "Player", "Input", "System", "Playlist", "Addons", "AudioLibrary", "Files", "GUI" , "JSONRPC", "PVR", "xbmc"]
for cl in namespaces:
  s = """class %s(XBMCNamespace):
  \"\"\"XBMC %s namespace. \"\"\"
  pass
  """%(cl,cl)
  exec (s)
