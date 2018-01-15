import os
import sys
import requests
# import uuid

PRECONDITION_FAILED_STATUS = 412

config = {'sentry': {'auth_token': os.environ.get('SENTRY_AUTH_TOKEN')}}

def create_headers(auth_token):
    return {'Authorization': 'Bearer ' + auth_token}

def get_create_proj_endpoint(host, org_slug, team_slug):
    endpoint_template = 'https://{}/api/0/teams/{}/{}/projects/'
    return endpoint_template.format(host, org_slug, team_slug)

def create_proj(auth_token, org_slug, team_slug, proj_name, proj_slug):
    endpoint = get_create_proj_endpoint('sentry.io', org_slug, team_slug)
    headers = {'Authorization': 'Bearer ' + auth_token}
    data = {'name': proj_name, 'slug': proj_slug}
    response = requests.post(endpoint, data=data, headers=headers)
    if response.status == 201:
        return response


class Sentry:
    def __init__(self):
        auth_token = config['sentry']['auth_token']
        if not auth_token:
            logger.error('SENTRY_AUTH_TOKEN environment variable is missing. ' +
                         "To create the token go to 'https://sentry.io/api/'.")
            sys.exit(PRECONDITION_FAILED_STATUS)
        self.auth_token = auth_token


class SentryOrg(Sentry):
    def __init__(self, org_slug):
        Sentry.__init__(self)
        self.org_slug = org_slug


class SentryTeam(SentryOrg):
    def __init__(self, team_slug):
        SentryOrg.__init__(self)
        self.team_slug = team_slug
