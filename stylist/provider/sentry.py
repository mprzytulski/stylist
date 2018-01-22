import copy
import json
import os

import click
import requests

from stylist.cli import logger
from stylist.commands.cmd_profile import select
from stylist.commands.cmd_ssm import write

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

    def _get_create_proj_endpoint(self):
        template = 'https://{}/api/0/teams/{}/{}/projects/'
        return template.format(self.host, self.org_slug, self.team_slug)

    def _get_create_client_key_endpoint(self, proj_slug):
        template = 'https://{}/api/0/projects/{}/{}/keys/'
        return template.format(self.host, self.org_slug, proj_slug)

    def create_proj(self, proj_slug):
        resp = requests.post(self._get_create_proj_endpoint(),
                             data={'name': proj_slug, 'slug': proj_slug},
                             headers=self.headers)
        if resp.status_code == requests.codes.created:
            logger.info('[Create Sentry Project] OK')
        elif resp.status_code == requests.codes.conflict:
            logger.info('[Create Sentry Project] Already exists. Skipping..')
        else:
            raise (Exception('[Create Sentry Project] ' + json.loads(resp.text)['detail']))
        return resp

    def create_client_key(self, proj_slug):
        resp = requests.post(self._get_create_client_key_endpoint(proj_slug),
                             data={'name': proj_slug + "'s key"},
                             headers=self.headers)
        resp.raise_for_status()
        return resp.json()


def proj_init_integration(auth_token, ctx, org, team, envs):
    sentry = Sentry(auth_token, org, team)
    resp = sentry.create_proj(ctx.name)
    client_key = sentry.create_client_key(ctx.name)
    # bind .invoke method into ctx so that we can deepcopy ctx and use .load/.invoke
    ctx.invoke = click.get_current_context().invoke.__get__(ctx)
    for environment in envs:
        ctx_copy = copy.deepcopy(ctx)
        # I don't do a lot. Just here to pretty print the environment name
        ctx_copy.invoke(select, name=environment)
        ctx_copy.load(environment)  # I'm the one that changes the environment
        ctx_copy.invoke(write,
                        parameter='sentry',
                        value=client_key['dsn']['secret'])
