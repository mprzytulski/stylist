import os
import sys
import requests
import uuid

from stylist.cli import logger


config = {'sentry': {'auth_token': os.environ.get('SENTRY_AUTH_TOKEN')}}


# TODO use this when calling SentryProject
# logger.error('SENTRY_AUTH_TOKEN environment variable is missing. ' +
#             "To create the token go to 'https://sentry.io/api/'.")


class SentryProject:

    def __init__(self, org_slug, team_slug, host='sentry.io'):
        if config['sentry']['auth_token']:  # FIXME replace with exception
            self.auth_token = config['sentry']['auth_token']
            self.host = host
            self.org_slug = org_slug
            self.team_slug = team_slug
            self.headers = {'Authorization': 'Bearer ' + self.auth_token}
            self.project = None
        else:
            self = None

    def get_create_proj_endpoint(self):
        template = 'https://{}/api/0/teams/{}/{}/projects/'
        return template.format(self.host, self.org_slug, self.team_slug)

    def get_delete_proj_endpoint(self):
        template = 'https://{}/api/0/projects/{}/{}/'
        return template.format(self.host, self.org_slug, self.project['slug'])

    def create(self, proj_name):
        proj_slug = proj_name + '_' + uuid.uuid4().hex
        endpoint = self.get_create_proj_endpoint()
        data = {'name': proj_name, 'slug': proj_slug}
        response = requests.post(endpoint, data=data, headers=self.headers)
        if response.status_code == 201:
            self.project = response.json()

    def delete(self):
        if self.project:
            endpoint = self.get_delete_proj_endpoint()
            response = requests.delete(endpoint, headers=self.headers)
            if response.status_code == 204:
                self.project = None
