# import pytest
from unittest import TestCase
from stylist.cli import logger

def get_delete_proj_endpoint(host, org_slug, proj_slug):
    endpoint_template = 'https://{}/api/0/projects/{}/{}/'
    return endpoint_template.format(host, org_slug, proj_slug)

def del_proj():
    endpoint = get_delete_proj_endpoint(host, org_slug, proj_slug)


class CreateProjTest(TestCase):
    def test_can_create_nonexistent_project(self):
        proj_slug = 'test_proj_f2857afdaf194eb2b71a4daa4d9d817c'
        auth_token = config['sentry']['auth_token']
        created_proj = create_proj(auth_token, 'threads-styling-ltd', 'threads-styling-ltd', 'test_proj', proj_slug)
        self.assertEqual(created_proj.status, 201)
