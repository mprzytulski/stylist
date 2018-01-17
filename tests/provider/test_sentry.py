import uuid
import requests

from unittest import TestCase
from nose.plugins.attrib import attr

import stylist.provider.sentry as sentry


class Sentry(sentry.Sentry):

    def __init__(self, *args, **kwargs):
        sentry.Sentry.__init__(self, *args, **kwargs)

    def get_delete_proj_endpoint(self, proj_slug):
        template = 'https://{}/api/0/projects/{}/{}/'
        return template.format(self.host, self.org_slug, proj_slug)

    def delete(self, proj_slug):
        endpoint = self.get_delete_proj_endpoint(proj_slug)
        requests.delete(endpoint, headers=self.headers)


class CreateProjTest(TestCase):

    def setUp(self):
        self.proj_slug = 'test_proj' + '_' + uuid.uuid4().hex
        self.sentry_proj = Sentry(sentry.config['sentry']['auth_token'],
                                  'threads-styling-ltd',
                                  'threads-styling-ltd')

    @attr('clutter')
    def test_can_create_project(self):
        response = self.sentry_proj.create(self.proj_slug)
        self.assertEqual(response.status_code, requests.codes.created)

    @attr('clutter')
    def test_two_projs_same_name_only_one_created_proj(self):
        # TODO test throwing exception on unknown response status code
        # TODO test project creation messages being printed
        successfully_created_proj_status_code = self.sentry_proj.create(self.proj_slug).status_code
        unsuccessfully_created_proj_status_code = self.sentry_proj.create(self.proj_slug).status_code
        self.assertEqual([successfully_created_proj_status_code, unsuccessfully_created_proj_status_code],
                         [requests.codes.created, requests.codes.conflict])

    def tearDown(self):
        self.sentry_proj.delete(self.proj_slug)

