from unittest import TestCase
from stylist.provider.sentry import SentryProject


class CreateProjTest(TestCase):

    def setUp(self):
        self.sentry_proj = SentryProject('threads-styling-ltd', 'threads-styling-ltd')

    def test_sentry_project_setup(self):
        self.assertTrue(self.sentry_proj)

    def test_can_create_nonexistent_project(self):
        self.sentry_proj.create('test_proj')
        self.assertTrue(self.sentry_proj.project)

    def tearDown(self):
        self.sentry_proj.delete()