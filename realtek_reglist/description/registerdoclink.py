from flask import request, url_for
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree

class RegisterDocLinkProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        elem = etree.Element('a')
        page_type = m.group(1)
        page_name = m.group(2)
        elem.text = page_name
        if hasattr(self.md, 'Meta') and 'regdoc_platform' in self.md.Meta:
            page_platform = self.md.Meta['regdoc_platform'][0]
        else:
            return (None, None, None)

        if page_type == 'register':
            elem.set('href', url_for('realtek.regfieldlist', platform=page_platform, register=page_name).lower())
        elif page_type == 'table':
            elem.set('href', url_for('realtek.tablefieldlist', platform=page_platform, table=page_name).lower())
        else:
            return (None, None, None)
        return (elem, m.start(0), m.end(0))

class RegisterDocLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
                RegisterDocLinkProcessor(r'\[\[(table|register):([a-zA-Z0-9_]+)\]\]', md),
                'regdoclink', 175
            )
