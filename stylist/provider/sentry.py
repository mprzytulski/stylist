import os
import requests
import git
import giturlparse

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
            raise(Exception('[Create Sentry Project] ' + json.loads(resp.text)['detail']))
        return resp

    def create_client_key(self, proj_slug):
        resp = requests.post(self._get_create_client_key_endpoint(proj_slug),
                             data={'name': proj_slug + "'s key"},
                             headers=self.headers)
        resp.raise_for_status()
        return resp.json()


def get_git_remote_origin_url():
    git_url = next(git.Repo().remotes.origin.urls)
    return giturlparse.parse(git_url).repo


def proj_init_integration(auth_token, ctx, org, team):
    git_repo_name = get_git_remote_origin_url()
    sentry = Sentry(auth_token, org, team)
    sentry.create_proj(git_repo_name)
    client_key = sentry.create_client_key(git_repo_name)
    for environment in ['staging']:
        ctx.load(environment)
        ssm_param_name = ctx.provider.ssm.write("service:" + git_repo_name,
                                                'dsn_secret',
                                                client_key['dsn']['secret'],
                                                True)
    return git_repo_name, ssm_param_name

# TODO find how versioned/dev config works

