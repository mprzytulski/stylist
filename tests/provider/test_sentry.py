from unittest import TestCase
from nose.plugins.attrib import attr
from stylist.provider.sentry import SentryProject, config
import uuid


class CreateProjTest(TestCase):

    def setUp(self):
        self.proj_slug = 'test_proj' + '_' + uuid.uuid4().hex
        self.sentry_proj = SentryProject(config['sentry']['auth_token'],
                                         'threads-styling-ltd',
                                         'threads-styling-ltd')

    @attr('clutter')
    def test_can_create_project(self):
        response = self.sentry_proj.create(self.proj_slug)
        self.assertEqual(response.status_code, 201)

    @attr('clutter')
    def test_two_projs_same_name_only_one_created_proj(self):
        # TODO test throwing exception on unknown response status code
        # TODO test project creation messages being printed
        successfully_created_proj_status_code = self.sentry_proj.create(self.proj_slug).status_code
        unsuccessfully_created_proj_status_code = self.sentry_proj.create(self.proj_slug).status_code
        self.assertEqual([successfully_created_proj_status_code, unsuccessfully_created_proj_status_code],
                         [201, 409])

    def tearDown(self):
        self.sentry_proj.delete(self.proj_slug)

