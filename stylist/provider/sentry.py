import os
import requests

from stylist.cli import logger


config = {'sentry': {'auth_token': os.environ.get('SENTRY_AUTH_TOKEN')}}

# TODO the caller to SentryProject should handle this:
# raise Exception('SENTRY_AUTH_TOKEN environment variable is missing. ' +
#                "To create the token go to 'https://sentry.io/api/'.")


class Sentry:

    def __init__(self, auth_token, org_slug, team_slug, host='sentry.io'):
        self.host = host
        self.org_slug = org_slug
        self.team_slug = team_slug
        self.headers = {'Authorization': 'Bearer ' + auth_token}

    def get_create_proj_endpoint(self):
        template = 'https://{}/api/0/teams/{}/{}/projects/'
        return template.format(self.host, self.org_slug, self.team_slug)

    def create(self, proj_slug):
        endpoint = self.get_create_proj_endpoint()
        data = {'name': proj_slug, 'slug': proj_slug}
        response = requests.post(endpoint, data=data, headers=self.headers)
        if response.status_code == requests.codes.created:
            logger.info('[Create Sentry Project] OK')
        elif response.status_code == requests.codes.conflict:
            logger.info('[Create Sentry Project] Already exists. Skipping..')
        else:
            response.raise_for_status()
        return response

