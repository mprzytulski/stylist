import uuid
import requests

import stylist.provider.sentry as sentry

from unittest import TestCase
from nose.plugins.attrib import attr
import stylist.config as config


class Sentry(sentry.Sentry):

    def get_delete_proj_endpoint(self, proj_slug):
        template = 'https://{}/api/0/projects/{}/{}/'
        return template.format(self.host, self.org_slug, proj_slug)

    def delete(self, proj_slug):
        requests.delete(self.get_delete_proj_endpoint(proj_slug),
                        headers=self.headers)


class SentryIntegrationTest(TestCase):

    def setUp(self):
        self.proj_slug = 'test_proj' + '_' + uuid.uuid4().hex
        settings = config.conform(config.get())
        self.sentry_proj = Sentry(settings['sentry']['auth_token'],
                                  settings['sentry']['org'],
                                  settings['sentry']['team'])

    @attr('clutter')
    def test_can_create_project(self):
        response = self.sentry_proj.create_proj(self.proj_slug)
        self.assertEqual(response.status_code, requests.codes.created)

    @attr('clutter')
    def test_two_projs_same_name_only_one_created_proj(self):
        # TODO test throwing exception on unknown response status code
        # TODO test project creation messages being printed
        successfully_created_proj_status_code = self.sentry_proj.create_proj(self.proj_slug).status_code
        unsuccessfully_created_proj_status_code = self.sentry_proj.create_proj(self.proj_slug).status_code
        self.assertEqual([successfully_created_proj_status_code, unsuccessfully_created_proj_status_code],
                         [requests.codes.created, requests.codes.conflict])

    @attr('clutter')
    def test_create_client_key(self):
        self.sentry_proj.create_proj(self.proj_slug)
        client_key = self.sentry_proj.create_client_key(self.proj_slug)
        self.assertIn('dsn', client_key.keys())

    def tearDown(self):
        self.sentry_proj.delete(self.proj_slug)
