import os
import requests

from stylist.cli import logger


config = {'sentry': {'auth_token': os.environ.get('SENTRY_AUTH_TOKEN')}}

# TODO the caller to SentryProject should handle this:
# raise Exception('SENTRY_AUTH_TOKEN environment variable is missing. ' +
#                "To create the token go to 'https://sentry.io/api/'.")

class SentryProject:

    def __init__(self, auth_token, org_slug, team_slug, host='sentry.io'):
        self.host = host
        self.org_slug = org_slug
        self.team_slug = team_slug
        self.headers = {'Authorization': 'Bearer ' + config['sentry']['auth_token']}

    def get_create_proj_endpoint(self, proj_slug):
        template = 'https://{}/api/0/teams/{}/{}/projects/'
        return template.format(self.host, self.org_slug, self.team_slug)

    def get_delete_proj_endpoint(self, proj_slug):
        template = 'https://{}/api/0/projects/{}/{}/'
        return template.format(self.host, self.org_slug, proj_slug)

    def create(self, proj_slug):
        endpoint = self.get_create_proj_endpoint(proj_slug)
        data = {'name': proj_slug, 'slug': proj_slug}
        response = requests.post(endpoint, data=data, headers=self.headers)
        if response.status_code == 201:
            logger.info('[Create Sentry Project] OK')
        elif response.status_code == 409:
            logger.info('[Create Sentry Project] Already exists. Skipping..')
        else:
            exception_msg_template = '[Create Sentry Project] Unexpected issue. Response status code is {}.'
            raise Exception(exception_msg_template.format(response.status_code), response)
        return response

    def delete(self, proj_slug):
        endpoint = self.get_delete_proj_endpoint(proj_slug)
        requests.delete(endpoint, headers=self.headers)

