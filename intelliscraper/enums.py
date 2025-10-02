from enum import Enum


class HTMLParserType(str, Enum):
    """
    Enum representing supported HTML parsers for HTMLParser.
    """

    HTML5LIB = "html5lib"
    BUILTIN = "html.parser"
