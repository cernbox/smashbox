from smashbox.utilities import *
from smashbox.utilities.hash_files import *
from smashbox.protocol import *

import smashbox.utilities.reflection
import smashbox.curl

import re
from collections.abc import Callable
from typing import cast

""" Test docstrings in protocol.md
"""

@add_worker
def main(step: Step) -> None:

    d = make_workdir()
    reset_owncloud_account()

    # grab the protocol.md file sitting in the same directory as this source file
    docfile = os.path.join(os.path.dirname(smashbox.utilities.reflection.getTestcaseFilename()),'protocol.md')

    blocks = parse_docfile(docfile)

    block_ok=0

    for (block_check, block_header, block_body, lineno) in blocks:
        logger.info('checking doc block: %s %s line %d: %s',block_check.__name__,block_header,lineno,block_body)
        try:
            block_check(block_header,block_body)
            block_ok += 1
        except Exception as x:
            logger.error('while checking %s %s line %d: %s %s',block_check.__name__,block_header,lineno,block_body,x)

    logger.info('checked %d ok out of %d',block_ok,len(blocks))

def check_propfind_request(header: list[str],body: str) -> None:
    # as a bare minimum check if XML syntax is correct
    
    from xml.etree import ElementTree
    ElementTree.fromstring(body)

def check_propfind_response(header: list[str],body: str) -> None:
    smashbox.curl._parse_propfind_response(body)

def parse_docfile(docfile: str) -> list[tuple[Callable[[list[str], str], None], list[str], str, int]]:

    propfind_request = re.compile(r"(?P<indent>\s+)> PROPFIND")
    propfind_response = re.compile(r"(?P<indent>\s+)< PROPFIND")

    blocks: list[tuple[Callable[[list[str], str], None], list[str], str, int]]=[]

    block_re: re.Pattern[str] | None=None

    block_indent: int | None=0
    block_check: Callable[[list[str], str], None] | None=None
    block_header: list[str]=[]
    block_body=''
    in_header=False
    block_lineno=0

    lineno=0

    def DEBUG(*x: object) -> None:
        print('DEBUG:',lineno,x)

    for line in open(docfile, encoding='utf-8'):

        lineno+=1

        r1 = propfind_request.match(line)
        r2 = propfind_response.match(line)

        if r1 or r2: 
            if r1:
                block_check = check_propfind_request
                r=r1
            else:
                block_check = check_propfind_response
                r=cast(re.Match[str], r2) # r1 is None here, so r2 matched
            block_indent=len(r.group('indent'))
            block_re=re.compile(r.group('indent')+"(?P<text>.*)")
            in_header=True
            block_lineno=lineno
            DEBUG('start_of_block',block_check,block_indent)
            continue

        if block_re:
            r = block_re.match(line)

            #print r,line
            if r:
                text=r.group('text')

                if in_header:
                    if text == '':
                        in_header=False
                        DEBUG('end_of_header')
                        continue
                    block_header.append(text)
                    DEBUG('block_header',line)
                else:
                    block_body += text+'\n'
                    DEBUG('block_body',line)
            else:
                blocks.append((cast(Callable[[list[str], str], None], block_check),block_header,block_body,block_lineno)) # block_check is set whenever block_re is
                block_check=None
                block_header=[]
                block_body=''
                block_re=None
                block_indent=None
                DEBUG('end_of_block')


    return blocks
