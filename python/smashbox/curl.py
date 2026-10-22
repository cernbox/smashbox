from smashbox.utilities import *

import smashbox.utilities.structures
from collections.abc import Mapping
from typing import Any, cast
from xml.etree.ElementTree import Element

# one entry of a parsed PROPFIND response: [href, {status: {property: value}}]
PropfindEntry = list[Any]

class Response:
    # set depending on the request type
    response_body: bytes
    body_stream: 'io.BytesIO'
    propfind_response: list[PropfindEntry]

    def __init__(self) -> None:
        # rc and headers are always set by Client._perform_request() before the response is returned
        self.rc: int = None # type: ignore[assignment]
        self.headers: smashbox.utilities.structures.CaseInsensitiveDict[str] = [] # type: ignore[assignment]
        self.body: bytes | None = None

import pycurl, io

class Client:
    
    extra_headers: dict[str, object] = {}

    verbose: bool
    c: pycurl.Curl
    
    def __init__(self,verbose: bool | None = None) -> None:
        c = pycurl.Curl()

        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0) # allow self-signed or invalid certs etc.
        c.setopt(pycurl.CONNECTTIMEOUT, 60)
        c.setopt(pycurl.TIMEOUT, 60)
        c.setopt(pycurl.COOKIEFILE, '')
        c.setopt(pycurl.FOLLOWLOCATION, 0) # by default owncloud sync client does not follow redirects

        if config.get('pycurl_USERAGENT',None):
            c.setopt(pycurl.USERAGENT, config.pycurl_USERAGENT)

        if verbose is None:
            if config.get('pycurl_VERBOSE',None) is not None:
                self.verbose = config.pycurl_VERBOSE
            else:
                from logging import DEBUG
                self.verbose = config._loglevel <= DEBUG
        else:
            self.verbose=verbose


        c.setopt(pycurl.VERBOSE, self.verbose) 

        self.c = c

    def PROPFIND(self,url: str,query: str | bytes,depth: int | str,parse_check: bool = True,headers: dict[str, object] = {}) -> Response:
        logger.info("PROPFIND %s depth=%s %s query=%s",url,depth,headers,query)

        c = self.c

        c.setopt(pycurl.CUSTOMREQUEST, "PROPFIND")
        headers['Depth']=depth
        c.setopt(pycurl.UPLOAD,1) 

        if isinstance(query, str):
            query = query.encode('utf-8')
        c.setopt(pycurl.READFUNCTION,io.BytesIO(query).read)
        c.setopt(pycurl.INFILESIZE,len(query))

        r = Response()

        r.body_stream = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION,r.body_stream.write)

        self._perform_request(url,headers,response_obj=r)

        r.response_body=r.body_stream.getvalue()

        if self.verbose:
            logger.info('PROPFIND response body: %s',r.body_stream.getvalue().decode('utf-8','replace'))

        if parse_check:
            if 200 <= r.rc and r.rc < 300: # only parse the reponse type for positive responses 
                #TODO: multiple Content-Type response headers will confuse the client as well
                fatal_check('application/xml; charset=utf-8' in r.headers['Content-Type'],'Wrong response header "Content-Type:%s"'%r.headers['Content-Type']) # as of client 1.7 and 1.8
                r.propfind_response=_parse_propfind_response(r.response_body,depth=depth)
      
        return r


    def PUT(self,fn: str,url: str,headers: Mapping[str, object] = {},offset: int = 0,size: int = 0) -> Response:
        logger.debug('PUT %s %s %s',fn,url,headers)

        c = self.c

        c.setopt(pycurl.CUSTOMREQUEST, "PUT")
        c.setopt(pycurl.UPLOAD,1) 

        f = open(fn,'rb')

        if offset:
            f.seek(offset)

        if not size:
            size = os.path.getsize(fn) - offset

        c.setopt(pycurl.INFILE,f)
        c.setopt(pycurl.INFILESIZE,size)

        r = Response()

        r.body_stream = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION,r.body_stream.write)

        x = self._perform_request(url,headers)

        if self.verbose:
            logger.info('PUT response body: %s',r.body_stream.getvalue().decode('utf-8','replace'))

        return x

    def GET(self,url: str,fn: str | None,headers: Mapping[str, object] = {}) -> Response:
        logger.debug('GET %s %s %s',url,fn,headers)

        c = self.c

        if fn:
            f = open(fn,'wb')
            c.setopt(pycurl.WRITEFUNCTION,f.write)
        else:
            body_stream =  io.BytesIO()
            c.setopt(pycurl.WRITEFUNCTION,body_stream.write)

        r = self._perform_request(url,headers)

        if fn:
            f.close()
        else:
            r.response_body=body_stream.getvalue()

        return r

    def MKCOL(self,url: str) -> Response:
        logger.debug('MKCOL %s',url)
        
        c = self.c
        
        c.setopt(pycurl.CUSTOMREQUEST, "MKCOL")

        r = self._perform_request(url,{})

        return r        


    def DELETE(self,url: str) -> Response:

        logger.debug('DELETE %s',url)
        
        c = self.c
        
        c.setopt(pycurl.CUSTOMREQUEST, "DELETE")

        # we are usually not interested in response body of this kind of request
        # if present, we capture it to a variable, otherwise it gets printed to stdout by pycurl
        body_stream = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION, body_stream.write)

        r = self._perform_request(url,{})
        r.response_body=body_stream.getvalue()
        return r        

    def MOVE(self,url: str,destination: str,overwrite: str | None = None) -> Response:
        logger.debug
        
        print('MOVE %s %s %s'%(url,destination,overwrite))
        c = self.c
        
        c.setopt(pycurl.CUSTOMREQUEST, "MOVE")
        headers: dict[str, object] = {}
        headers['Destination']=destination
        if overwrite:
            headers['Overwrite']=overwrite

        r = self._perform_request(url,headers)

        return r


    def _perform_request(self,url: str,headers: Mapping[str, object],response_obj: Response | None = None) -> Response:
        c = self.c

        _headers = self.extra_headers.copy()
        _headers.update(headers)
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.HTTPHEADER,[str(x)+':'+str(y) for x,y in zip(_headers.keys(),_headers.values())])

        ret_headers: list[bytes] = []
        c.setopt(pycurl.HEADERFUNCTION, ret_headers.append)

        c.perform()

        if response_obj is None:
            response_obj = Response()
        
        response_obj.rc=c.getinfo(pycurl.HTTP_CODE)

        response_obj.headers = smashbox.utilities.structures.CaseInsensitiveDict()
        for h in ret_headers:
            h = h.decode('iso-8859-1').strip() # HTTP header encoding as per RFC 7230
            if not h:
                continue
            fields = h.split(':',1)
            assert(len(fields) <= 2)
            if len(fields)==2:
                response_obj.headers[fields[0]] = fields[1]

        logger.debug('_perform_request url=%s header=%s rc=%s reply_headers=%s',url,headers,response_obj.rc,response_obj.headers)

        return response_obj


def _parse_propfind_response(text: str | bytes,depth: int | str | None = None) -> list[PropfindEntry]:
    """ Basic parsing and validation of PROPFIND responses.

    If depth is defined add validation according to the depth.
    """

    def allowed_children_tags(e: Element,tags: list[str]) -> None:
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
        href = cast(Element, child.find('{DAV:}href')) # exactly one (checked above)

        r: PropfindEntry = [href.text,{}]

        for propstat in child.findall('{DAV:}propstat'):

            logger.debug('xml.etree.ElementTree parsing: %s',propstat.tag)
            
            allowed_children_tags(propstat,['{DAV:}prop','{DAV:}status'])
            fatal_check(len(propstat.findall('{DAV:}prop'))==1) # exactly one
            fatal_check(len(propstat.findall('{DAV:}status'))==1) # exactly one

            status = cast(Element, propstat.find('{DAV:}status')) # exactly one (checked above)
            prop = cast(Element, propstat.find('{DAV:}prop')) # exactly one (checked above)

            rp: dict[str, str | None] = {}

            for p in prop:
                logger.debug('xml.etree.ElementTree parsing: %s',p.tag)
                fatal_check(p.tag not in rp,p.tag) # duplicate elements are not allowed
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

