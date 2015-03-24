import unittest
import re
from .ticketrenderer import TicketRenderer


class TestTicketRenderer(unittest.TestCase):

    def setUp(self):
        installation = '1'
        html = '{{snapshot}} {{code}} {{datetime | datetimeformat}} {{variable_1}} {{variable_2}} {{image_1}}'
        self.chiefs = ['Titi', 'Vicky', 'Benni']
        text_variables = [{'id': '1', 'items': self.chiefs}]
        self.paths = ['/path/to/variable/image1', '/path/to/variable/image2']
        image_variables = [{'id': '2', 'items': self.paths}]
        images = [{'id': '1', 'media_url': 'path/to/image'}]
        self.ticket_renderer = TicketRenderer(installation, html, text_variables, image_variables, images)

    def test_random_selection(self):
        random_selection = self.ticket_renderer.random_selection()
        self.assertTrue(random_selection['variable_1'] in self.chiefs)
        self.assertTrue(random_selection['variable_2'] in self.paths)

    def test_code(self):
        generics = self.ticket_renderer.generics()
        self.assertTrue(len(generics['code']) == 8)
        self.assertTrue(generics['code'].isupper())

    def test_render(self):
        rendered = self.ticket_renderer.render('/path/to/snapshot')
        expected = re.compile("/path/to/snapshot \w{8} \d{4}-\d{2}-\d{2} (Titi|Vicky|Benni) /path/to/variable/image(1|2) path/to/image")
        self.assertRegexpMatches(rendered, expected)

    def test_set_date_format(self):
        html = '{{datetime | datetimeformat("%Y")}}'
        self.ticket_renderer.html = html
        rendered = self.ticket_renderer.render('/path/to/snapshot')
        self.assertRegexpMatches(rendered, re.compile("\d{4}"))


if __name__ == '__main__':
    unittest.main()

