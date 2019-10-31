#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.


from __future__ import print_function, division, absolute_import, unicode_literals

import sys

from tatsu.buffering import Buffer
from tatsu.parsing import Parser
from tatsu.parsing import tatsumasu, leftrec, nomemo
from tatsu.parsing import leftrec, nomemo  # noqa
from tatsu.util import re, generic_main  # noqa


KEYWORDS = {}  # type: ignore


class TextGrammarBuffer(Buffer):
    def __init__(
        self,
        text,
        whitespace=re.compile('[\\t ]+'),
        nameguard=None,
        comments_re=None,
        eol_comments_re='^(#.*|\\s*)\\n',
        ignorecase=None,
        namechars='',
        **kwargs
    ):
        super(TextGrammarBuffer, self).__init__(
            text,
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            namechars=namechars,
            **kwargs
        )


class TextGrammarParser(Parser):
    def __init__(
        self,
        whitespace=re.compile('[\\t ]+'),
        nameguard=None,
        comments_re=None,
        eol_comments_re='^(#.*|\\s*)\\n',
        ignorecase=None,
        left_recursion=True,
        parseinfo=True,
        keywords=None,
        namechars='',
        buffer_class=TextGrammarBuffer,
        **kwargs
    ):
        if keywords is None:
            keywords = KEYWORDS
        super(TextGrammarParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            parseinfo=parseinfo,
            keywords=keywords,
            namechars=namechars,
            buffer_class=buffer_class,
            **kwargs
        )

    @tatsumasu()
    def _symbol_(self):  # noqa
        self._pattern('[\\w()/!<>-]+')

    @tatsumasu()
    def _literal_(self):  # noqa
        self._pattern('(([^;|<>\\n\\[\\]()]|\\[[^\\[\\]]*\\]|\\([^()]*\\))+(?<!\\s))?')

    @tatsumasu('AdjectiveNoun')
    def _adjectiveNoun_(self):  # noqa
        self._literal_()
        self.name_last_node('adjective')
        self._token('|')
        self._literal_()
        self.name_last_node('noun')
        self.ast._define(
            ['adjective', 'noun'],
            []
        )

    @tatsumasu('Match')
    def _match_(self):  # noqa
        self._adjectiveNoun_()
        self.name_last_node('lhs')
        self._token('<->')
        self._adjectiveNoun_()
        self.name_last_node('rhs')
        self.ast._define(
            ['lhs', 'rhs'],
            []
        )

    @tatsumasu()
    def _alternative_(self):  # noqa
        with self._choice():
            with self._option():
                self._match_()
            with self._option():
                self._adjectiveNoun_()
            with self._option():
                self._literal_()
            self._error('no available options')

    @tatsumasu()
    def _alternatives_(self):  # noqa

        def sep0():
            self._token(';')

        def block0():
            self._alternative_()
        self._positive_gather(block0, sep0)

    @tatsumasu('ProductionRule')
    def _productionRule_(self):  # noqa
        self._symbol_()
        self.name_last_node('symbol')
        self._token(':')
        self._alternatives_()
        self.name_last_node('alternatives')
        with self._group():
            with self._choice():
                with self._option():
                    self._token('\n')
                with self._option():
                    self._check_eof()
                self._error('no available options')
        self.ast._define(
            ['alternatives', 'symbol'],
            []
        )

    @tatsumasu('TextGrammar')
    def _grammar_(self):  # noqa

        def block1():
            self._productionRule_()
        self._closure(block1)
        self.name_last_node('rules')
        self._check_eof()
        self.ast._define(
            ['rules'],
            []
        )

    @tatsumasu()
    def _start_(self):  # noqa
        self._grammar_()


class TextGrammarSemantics(object):
    def symbol(self, ast):  # noqa
        return ast

    def literal(self, ast):  # noqa
        return ast

    def adjectiveNoun(self, ast):  # noqa
        return ast

    def match(self, ast):  # noqa
        return ast

    def alternative(self, ast):  # noqa
        return ast

    def alternatives(self, ast):  # noqa
        return ast

    def productionRule(self, ast):  # noqa
        return ast

    def grammar(self, ast):  # noqa
        return ast

    def start(self, ast):  # noqa
        return ast


def main(filename, start=None, **kwargs):
    if start is None:
        start = 'symbol'
    if not filename or filename == '-':
        text = sys.stdin.read()
    else:
        with open(filename) as f:
            text = f.read()
    parser = TextGrammarParser()
    return parser.parse(text, rule_name=start, filename=filename, **kwargs)


if __name__ == '__main__':
    import json
    from tatsu.util import asjson

    ast = generic_main(main, TextGrammarParser, name='TextGrammar')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(asjson(ast), indent=2))
    print()
