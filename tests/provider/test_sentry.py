from unittest import TestCase
from nose.plugins.attrib import attr
from stylist.provider.sentry import SentryProject


class CreateProjTest(TestCase):

    def setUp(self):
        self.sentry_proj1 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')
        self.sentry_proj2 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')
        self.sentry_proj3 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')
        self.sentry_proj4 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')
        self.sentry_proj5 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')
        self.sentry_proj6 = SentryProject('threads-styling-ltd', 'threads-styling-ltd')

    def test_sentry_project_setup(self):
        self.assertTrue(self.sentry_proj1)

    @attr('clutter')
    def test_can_create_project(self):
        self.sentry_proj1._create_new('test_proj')
        self.assertTrue(self.sentry_proj1.project)

    @attr('clutter')
    def test_can_create_two_projects_same_name(self):
        self.sentry_proj2._create_new('test_proj')
        self.sentry_proj3._create_new('test_proj')
        self.assertNotEqual(self.sentry_proj2.project['slug'],
                            self.sentry_proj3.project['slug'])

    @attr('clutter')
    def test_can_retrieve_non_deleted_project(self):
        self.sentry_proj4._create_new('test_proj')
        self.sentry_proj4.retrieve('test_proj')
        self.assertTrue(self.sentry_proj4.project)
        self.assertNotEqual(self.sentry_proj4.project['status'], 'deleted')

    @attr('clutter')
    def test_can_create_only_one_project_same_name(self):
        self.sentry_proj5.create('test_proj')
        self.sentry_proj6.create('test_proj')
        self.assertEqual(self.sentry_proj5.project['slug'],
                         self.sentry_proj6.project['slug'])

    def tearDown(self):
        self.sentry_proj1.delete()
        self.sentry_proj2.delete()
        self.sentry_proj3.delete()
        self.sentry_proj4.delete()
        self.sentry_proj5.delete()
        self.sentry_proj6.delete()

