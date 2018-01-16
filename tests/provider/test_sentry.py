from unittest import TestCase
from nose.plugins.attrib import attr
from stylist.provider.sentry import SentryProject


class CreateProjTest(TestCase):

    def setUp(self):
        self.sentry_proj1 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')
        self.sentry_proj2 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')

    def test_sentry_project_setup(self):
        self.assertTrue(self.sentry_proj1)

    @attr('clutter')
    def test_can_create_project(self):
        self.sentry_proj1._create_new('test_proj')
        self.assertTrue(self.sentry_proj1.project)

    @attr('clutter')
    def test_can_create_two_projects_same_name(self):
        self.sentry_proj1._create_new('test_proj')
        self.sentry_proj2._create_new('test_proj')
        self.assertNotEqual(self.sentry_proj1.project['slug'],
                            self.sentry_proj2.project['slug'])

    @attr('clutter')
    def test_can_create_only_one_project_same_name(self):
        self.sentry_proj1.create('test_proj')
        self.sentry_proj2.create('test_proj')
        self.assertEqual(self.sentry_proj1.project['slug'],
                         self.sentry_proj2.project['slug'])

    def tearDown(self):
        self.sentry_proj1.delete()
        self.sentry_proj2.delete()

