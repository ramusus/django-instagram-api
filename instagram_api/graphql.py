import requests
import simplejson as json
from oauth_tokens.providers.instagram import InstagramAuthRequest


class GraphQL(object):

    url = 'https://www.instagram.com/query/'
    cookies = '__utma=227057989.1129888433.1423302270.1433340455.1434559808.20; __utmc=227057989; mid=VpvY_gAEAAHrA7w3K-gGUZNO3gUn; sessionid=IGSC7c09257a24e6a71806e9f9dc952d22e2aeca0b9a471b86c84c75ffa10511a509%3Avb2zOhH21hwjUVG4UItD2ruVR09hq2tF%3A%7B%22_token_ver%22%3A2%2C%22_auth_user_id%22%3A1687258424%2C%22_token%22%3A%221687258424%3AWd6qVgJRS6fbkEhrfKM1D5xo2XM8YFHk%3Abaa3b7fd09a33cea01f659a626fc6cb738c577ca896390beb5960043ec113298%22%2C%22asns%22%3A%7B%22188.40.74.9%22%3A24940%2C%22time%22%3A1466597282%7D%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22last_refreshed%22%3A1466597282.193233%2C%22_platform%22%3A4%7D; ig_pr=2; ig_vw=1618; csrftoken=CSRF_TOKEN; s_network=; ds_user_id=1687258424'

    def related_users(self, endpoint, user):
        req = InstagramAuthRequest()
        session = requests.Session()
        url = 'https://www.instagram.com/%s/' % user.username
        # response = req.authorized_request('get', url=url)
        response = session.get(url=url)
        csrf_token = req.get_csrf_token_from_content(response.content)
        headers = {
            'Referer': url,
            'X-CSRFToken': csrf_token,
            'Cookie': self.cookies.replace('CSRF_TOKEN', csrf_token),
        }

        user_id = user.id
        limit = 1000
        method = 'first'
        args = limit
        next_page = True

        while next_page:

            graphql = '''
ig_user(%(user_id)s) {
    %(endpoint)s.%(method)s(%(args)s) {
        count, page_info { end_cursor, has_next_page },
        nodes { id, is_verified, followed_by_viewer, requested_by_viewer, full_name, profile_pic_url, username }
    }
}''' % locals()

            # response = req.authorized_request('post', url=self.url, data={'q': graphql}, headers=headers)
            response = session.post(url=self.url, data={'q': graphql}, headers=headers)
            json_response = json.loads(response.content)

            method = 'after'
            args = '%s, %s' % (json_response[endpoint]['page_info']['end_cursor'], limit)
            next_page = json_response[endpoint]['page_info']['has_next_page']
            # print json_response[endpoint]['count'], len(json_response[endpoint]['nodes']), next_page
            yield json_response[endpoint]['nodes']
