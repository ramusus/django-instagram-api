import re
import simplejson as json
from oauth_tokens.providers.instagram import InstagramAuthRequest


class GraphQL(object):

    url = 'https://www.instagram.com/query/'

    def related_users(self, endpoint, user):
        req = InstagramAuthRequest()
        url = 'https://www.instagram.com/%s/' % user.username
        response = req.authorized_request('get', url=url)
        csrf_token = re.findall(r'"csrf_token": "([^"]+)"}', response.content)[0]
        headers = {
            'Referer': url,
            'X-CSRFToken': csrf_token,
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

            response = req.authorized_request('post', url=self.url, data={'q': graphql}, headers=headers)
            json_response = json.loads(response.content)

            method = 'after'
            args = '%s, %s' % (json_response[endpoint]['page_info']['end_cursor'], limit)
            next_page = json_response[endpoint]['page_info']['has_next_page']
            # print json_response[endpoint]['count'], len(json_response[endpoint]['nodes']), next_page
            yield json_response[endpoint]['nodes']
