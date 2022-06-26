from typing import Literal, Optional
from xml.etree import ElementTree

import httpx

from smashbox.utilities import *
from smashbox.script import getLogger


logger = getLogger()
RequestType = Literal["MOVE", "PROPFIND", "PUT", "GET", "MKCOL", "DELTETE"]
PropfindDepth = Literal["1", "0", "infinity"]
OverwriteType = Literal["T", "F"]


class Client:
    
    extra_headers = {}
    
    def __init__(self, verbose: Optional[bool] = None) -> None:
        self._client = httpx.Client(timeout=60)
        self.verbose = bool(verbose)
    
        if config.get('pycurl_USERAGENT',None):
            self._client.headers.update({"User-Agent": config.pycurl_USERAGENT})

    def PROPFIND(self, url: str, query: str, depth: PropfindDepth, parse_check: bool = True, headers: Optional[dict] = None) -> httpx.Response:
        logger.info("PROPFIND %s depth=%s %s query=%s", url,depth,headers,query)

        if headers is None:
            headers = {}
        headers['Depth'] = depth

        r = self._perform_request("PROPFIND", url, content=query, headers=headers)

        if self.verbose:
            logger.info('PROPFIND response body: %s', r.text)

        if parse_check:
            if 200 <= r.status_code and r.status_code < 300: # only parse the reponse type for positive responses 
                # TODO: multiple Content-Type response headers will confuse the client as well
                fatal_check('application/xml; charset=utf-8' in r.headers['Content-Type'],'Wrong response header "Content-Type:%s"'%r.headers['Content-Type']) # as of client 1.7 and 1.8
                r.propfind_response=_parse_propfind_response(r.response_body,depth=depth)
      
        return r


    def PUT(self, fn: str, url: str, headers: Optional[dict] = None, offset: int = 0) -> httpx.Response:
        logger.debug('PUT %s %s %s', fn, url, headers)

        with open(fn, 'rb') as f:
            if offset:
                f.seek(offset)
            r = self._perform_request("PUT", url, files={"upload-file": f})

        if self.verbose:
            logger.info('PUT response body: %s', r.text)

        return r

    def GET(self,url: str,fn: Optional[str] = None,headers: Optional[dict] = None) -> httpx.Response:
        logger.debug('GET %s %s %s',url,fn,headers)

        if fn:
            f = open(fn,'wb')

        r = self._perform_request("GET", url, headers=headers)

        if fn:
            f.write(r.read())
            f.close()
        else:
            r.response_body = r.read()

        return r

    def MKCOL(self,url: str) -> httpx.Response:
        logger.debug('MKCOL %s',url)
        return self._perform_request("MKCOL", url)

    def DELETE(self,url: str) -> httpx.Response:
        logger.debug('DELETE %s',url)
        return self._perform_request("DELETE", url)

    def MOVE(self,url: str,destination: str,overwrite: Optional[OverwriteType] = None) -> httpx.Response:
        logger.debug('MOVE %s %s %s', url,destination,overwrite)
        headers={}
        headers['Destination'] = destination
        if overwrite:
            headers['Overwrite'] = overwrite
        return self._perform_request("MOVE", url,headers=headers)


    def _perform_request(self, method: RequestType, url: str, content: Optional[str] = None, files: Optional[dict] = None, headers: Optional[httpx._types.HeaderTypes] = None) -> httpx.Response:
        _headers = self.extra_headers.copy()
        _headers.update(headers)

        res = self._client.request(method, url, content=content, headers=_headers, files=files)
        logger.debug('_perform_request url=%s header=%s rc=%s reply_headers=%s',url, headers, res.status_code, res.headers)

        return res


def _parse_propfind_response(text: str, depth: Optional[PropfindDepth] = None) -> list:
    """Basic parsing and validation of PROPFIND responses.

    If depth is defined add validation according to the depth.
    """

    def allowed_children_tags(e: ElementTree.Element, tags: list[str]) -> None:
        for c in e:
            fatal_check(c.tag in tags)

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

