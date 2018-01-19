import uuid
import requests
import stylist.provider.sentry as sentry

from unittest import TestCase
from nose.plugins.attrib import attr


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
        self.sentry_proj = Sentry(sentry.config['sentry']['auth_token'],
                                  'threads-styling-ltd',
                                  'threads-styling-ltd')

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

    # def test_proj_init_integration(self):
    #     # TODO test that the project is in Sentry
    #     # TODO test that the DSN is added to AWS SSM without duplicating it
    #     ctx = Context()
    #     #ctx.provider
    #     print type(ctx.provider.ssm)
    #     #(proj_name, ssm_param_name) = sentry.proj_init_integration(sentry.config['sentry']['auth_token'],
    #     #                                                           SSM(ssm, ctx), # TODO find wth is
    #     #                                                           'threads-styling-ltd',
    #     #                                                           'threads-styling-ltd')
    #     #self.assertEqual((proj_name, ssm_param_name), ('abc', 'def'))

    def tearDown(self):
        self.sentry_proj.delete(self.proj_slug)

