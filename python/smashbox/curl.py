from smashbox.utilities import *

import smashbox.utilities.structures

class Response:
    def __init__(self):
        self.rc = None
        self.headers = []
        self.body = None

import pycurl, cStringIO

class Client:
    
    def __init__(self,verbose=None):
        c = pycurl.Curl()

        c.setopt(c.SSL_VERIFYPEER, 0)
        c.setopt(c.SSL_VERIFYHOST, 0) # allow self-signed or invalid certs etc.
        c.setopt(c.CONNECTTIMEOUT, 60)
        c.setopt(c.TIMEOUT, 60)
        c.setopt(c.COOKIEFILE, '')
        c.setopt(c.FOLLOWLOCATION, 0) # by default owncloud sync client does not follow redirects

        if config.get('pycurl_USERAGENT',None):
            c.setopt(c.USERAGENT, config.pycurl_USERAGENT)

        if verbose is None:
            if config.get('pycurl_VERBOSE',None) is not None:
                self.verbose = config.pycurl_VERBOSE
            else:
                from logging import DEBUG
                self.verbose = config._loglevel <= DEBUG
        else:
            self.verbose=verbose


        c.setopt(c.VERBOSE, self.verbose) 

        self.c = c

    def PROPFIND(self,url,query,depth,parse_check=True,headers={}):
        logger.info("PROPFIND %s depth=%s %s query=%s",url,depth,headers,query)

        c = self.c

        c.setopt(c.CUSTOMREQUEST, "PROPFIND")
        c.setopt(pycurl.HTTPHEADER, ["Depth:%s"%depth,'Expect:'])
        c.setopt(c.UPLOAD,1) 

        import StringIO
        c.setopt(c.READFUNCTION,StringIO.StringIO(query).read)
        c.setopt(c.INFILESIZE,len(query))

        r = Response()

        r.body_stream = cStringIO.StringIO()
        c.setopt(c.WRITEFUNCTION,r.body_stream.write)

        self._perform_request(url,headers,response_obj=r)

        r.response_body=r.body_stream.getvalue()

        if self.verbose:
            logger.info('PROPFIND response body: %s',r.body_stream.getvalue())

        if parse_check:
            if 200 <= r.rc and r.rc < 300: # only parse the reponse type for positive responses 
                #TODO: multiple Content-Type response headers will confuse the client as well
                fatal_check('application/xml; charset=utf-8' in r.headers['Content-Type'],'Wrong response header "Content-Type:%s"'%r.headers['Content-Type']) # as of client 1.7 and 1.8
                r.propfind_response=_parse_propfind_response(r.response_body,depth=depth)
      
        return r


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

        if fn:
            f = open(fn,'w')
            c.setopt(c.WRITEFUNCTION,f.write)
        else:
            body_stream =  cStringIO.StringIO()
            c.setopt(c.WRITEFUNCTION,body_stream.write)

        r = self._perform_request(url,headers)

        if fn:
            f.close()
        else:
            r.response_body=body_stream.getvalue()

        return r

    def MKCOL(self,url):
        logger.debug('MKCOL %s',url)
        
        c = self.c
        
        c.setopt(c.CUSTOMREQUEST, "MKCOL")

        r = self._perform_request(url,{})

        return r        


    def DELETE(self,url):

        logger.debug('DELETE %s',url)
        
        c = self.c
        
        c.setopt(c.CUSTOMREQUEST, "DELETE")

        # we are usually not interested in response body of this kind of request
        # if present, we capture it to a variable, otherwise it gets printed to stdout by pycurl
        body_stream = cStringIO.StringIO()
        c.setopt(c.WRITEFUNCTION, body_stream.write)

        r = self._perform_request(url,{})
        r.response_body=body_stream.getvalue()
        return r        

    def MOVE(self,url,destination,overwrite=None):
        logger.debug
        
        print 'MOVE %s %s %s'%(url,destination,overwrite)
        c = self.c
        
        c.setopt(c.CUSTOMREQUEST, "MOVE")
        c.setopt(pycurl.HTTPHEADER, ["Destination:%s"%destination])
        if overwrite:
            c.setopt(pycurl.HTTPHEADER, ['Overwrite:%s'%overwrite])

        r = self._perform_request(url,{})

        return r


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

        response_obj.headers = smashbox.utilities.structures.CaseInsensitiveDict()
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


def _parse_propfind_response(text,depth=None):
    """ Basic parsing and validation of PROPFIND responses.

    If depth is defined add validation according to the depth.
    """

    def allowed_children_tags(e,tags):
        for c in e:
            fatal_check(c.tag in tags)

    from xml.etree import ElementTree

    logger.debug('xml.etree.ElementTree parsing: %s',text)
    root = ElementTree.fromstring(text)

    fatal_check(root.tag == '{DAV:}multistatus')

    num_responses = len(root.findall('{DAV:}response'))

    fatal_check(num_responses>0)

    if depth is not None:
        if str(depth)=='0':
            fatal_check(num_responses==1)
        else:
            fatal_check(num_responses>=1)

    allowed_children_tags(root,['{DAV:}response']) # only this element is allowed

    responses = []

    for child in root:

        allowed_children_tags(child,['{DAV:}href','{DAV:}propstat']) # only these elements are allowed
        
        fatal_check(len(child.findall('{DAV:}href'))==1) # exactly one href per response
        href = child.find('{DAV:}href')

        r = [href.text,{}]

        for propstat in child.findall('{DAV:}propstat'):

            logger.debug('xml.etree.ElementTree parsing: %s',propstat.tag)
            
            allowed_children_tags(propstat,['{DAV:}prop','{DAV:}status'])
            fatal_check(len(propstat.findall('{DAV:}prop'))==1) # exactly one
            fatal_check(len(propstat.findall('{DAV:}status'))==1) # exactly one

            status = propstat.find('{DAV:}status')
            prop = propstat.find('{DAV:}prop')

            rp = {}

            for p in prop:
                logger.debug('xml.etree.ElementTree parsing: %s',p.tag)
                fatal_check(not rp.has_key(p.tag),p.tag) # duplicate elements are not allowed
                if p.tag == '{DAV:}resourcetype':
                    fatal_check(len(list(p)) in [0,1]) # either empty or exactly one element
                    try:
                        resource_type=list(p)[0]
                        # For convenience we include some owncloud-specific input validation here. It should be removed in the future.
                        # In the response body the value of resourcetype property MUST NOT contain whitespaces (implementation as of owncloud client 1.5):
                        #<d:resourcetype><d:collection/></d:resourcetype>
                        fatal_check(resource_type.tag == '{DAV:}collection')
                        fatal_check(len(list(resource_type)) == 0) # <collection> must have no children 
                        fatal_check(not p.text) # there must not be text in front of <collection>, FIXME: this may be relaxed later to allow whitespaces
                        fatal_check(not resource_type.text) # there must not be text inside <collection>
                        fatal_check(not resource_type.tail) # there must not be text behind <collection>, FIXME: this may be relaxed later to allow whitespaces
                        rp[p.tag]='{DAV:}collection'
                    except IndexError:
                        rp[p.tag] = None
                else:
                    rp[p.tag] = p.text

            r[1][status.text] = rp

        responses.append(r)

    return responses

