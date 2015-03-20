from smashbox.utilities import *

class Response:
    def __init__(self):
        self.rc = None
        self.headers = []
        self.body = None

import pycurl, cStringIO

class Client:
    
    def __init__(self):
        c = pycurl.Curl()

        c.setopt(c.SSL_VERIFYPEER, 0)
        c.setopt(c.CONNECTTIMEOUT, 60)
        c.setopt(c.TIMEOUT, 60)
        c.setopt(c.COOKIEFILE, '')
        c.setopt(c.FOLLOWLOCATION, 0) # by default owncloud sync client does not follow redirects

        if config.get('pycurl_USERAGENT',None):
            c.setopt(c.USERAGENT, config.pycurl_USERAGENT)

        if config.get('pycurl_VERBOSE',None) is not None:
            self.verbose = config.pycurl_VERBOSE
        else:
            from logging import DEBUG
            self.verbose = config._loglevel <= DEBUG

        c.setopt(c.VERBOSE, self.verbose) 

        self.c = c

    def PUT(self,fn,url,headers={},offset=0,size=0):
        logger.debug('PUT %s %s %s',fn,url,headers)

        c = self.c

        c.setopt(c.CUSTOMREQUEST, "PUT")
        c.setopt(c.UPLOAD,1) 

        f = open(fn,'rb')

        if offset:
            f.seek(offset)

        if not size:
            size = os.path.getsize(fn) - offset

        c.setopt(c.INFILE,f)
        c.setopt(c.INFILESIZE,size)

        r = Response()

        r.body_stream = cStringIO.StringIO()
        c.setopt(c.WRITEFUNCTION,r.body_stream.write)

        x = self._perform_request(url,headers)

        if self.verbose:
            logger.info('PUT response body: %s',r.body_stream.getvalue())

        return x

    def GET(self,url,fn,headers={}):
        logger.debug('GET %s %s %s',url,fn,headers)

        c = self.c

        f = open(fn,'w')
        c.setopt(c.WRITEFUNCTION,f.write)
        return self._perform_request(url,headers)


    def _perform_request(self,url,headers,response_obj=None):
        c = self.c

        c.setopt(c.URL, url)
        c.setopt(pycurl.HTTPHEADER,[str(x)+':'+str(y) for x,y in zip(headers.keys(),headers.values())])

        ret_headers=[]
        c.setopt(pycurl.HEADERFUNCTION, ret_headers.append)

        c.perform()

        if response_obj is None:
            response_obj = Response()
        
        response_obj.rc=c.getinfo(c.HTTP_CODE)

        response_obj.headers = {}
        for h in ret_headers:
            h = h.strip()
            if not h:
                continue
            fields = h.split(':',1)
            assert(len(fields) <= 2)
            if len(fields)==2:
                response_obj.headers[fields[0]] = fields[1]

        logger.debug('_perform_request url=%s header=%s rc=%s reply_headers=%s',url,headers,response_obj.rc,response_obj.headers)

        return response_obj
