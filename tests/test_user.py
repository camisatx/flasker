import base64
#import pprint
import sys
import unittest

sys.path.append('../')
from tests.base import BaseTestCase     # NOQA


def _register_user(client):
    response = client.post('/v1/users', json={
        'username': 'josh', 'email': 'josh@joshschertz.com',
        'name': 'Josh', 'password': 'secret'})
    return response


class UserApiCase(BaseTestCase):

    def test_get_users(self):
        """Test process to retrieve a list of users. Requires creating user,
        getting a token, then getting the user list."""
        response = self.client.get('/v1/users')
        self.assertEqual(response.status_code, 401)

        # Creat a few users
        self.client.post('/v1/users', json={
            'username': 'josh', 'email': 'josh@joshschertz.com',
            'name': 'Josh', 'password': 'secret'})
        self.client.post('/v1/users', json={
            'username': 'bob', 'email': 'bob@joshschertz.com', 'name': 'Bob',
            'password': 'secret'})
        self.client.post('/v1/users', json={
            'username': 'sara', 'email': 'sara@joshschertz.com', 'name': 'Sara',
            'password': 'secret'})

        # Get a token for them, using correct username and password
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:secret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 200)
        user_token_json = user_token.get_json()
        users = self.client.get('/v1/users',
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(users.status_code, 200)
        users_json = users.get_json()
        #import pprint
        #pprint.pprint(users_json)
        self.assertEqual(users_json['_meta']['page'], 1)
        self.assertEqual(users_json['_meta']['total_items'], 3)

    def test_get_own_user_profile(self):
        """Test process to retrieve a user's own profile. Requires creating a
        user, getting a token, then getting the user's profile."""
        response = self.client.get('/v1/users')
        self.assertEqual(response.status_code, 401)

        # Creat a user
        user = _register_user(self.client)
        user_json = user.get_json()
        user_public_id = user_json['public_id']

        # Get a token for them, using correct username and password
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:secret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 200)
        user_token_json = user_token.get_json()

        # Retrieve the user's own profile
        user_profile = self.client.get('/v1/users/%s' % user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(user_profile.status_code, 200)
        user_profile_json = user_profile.get_json()
        self.assertEqual(user_profile_json['public_id'], user_public_id)
        self.assertEqual(user_profile_json['username'], 'josh')
        self.assertEqual(user_profile_json['email'], 'josh@joshschertz.com')
        self.assertEqual(user_profile_json['_links']['self'],
                '/v1/users/%s' % user_public_id)
        self.assertEqual(user_profile_json['_links']['followed'],
                '/v1/users/%s/followed' % user_public_id)
        self.assertEqual(user_profile_json['_links']['followers'],
                '/v1/users/%s/followers' % user_public_id)

    def test_get_other_user_profile(self):
        """Test process to retrieve a different user's profile. Requires
        creating two users, getting a token, then getting the user profile."""
        response = self.client.get('/v1/users')
        self.assertEqual(response.status_code, 401)

        # Creat two users
        _register_user(self.client)
        other_user = self.client.post('/v1/users', json={
            'username': 'sara', 'email': 'sara@joshschertz.com', 'name': 'Sara',
            'password': 'secret'})
        other_user_json = other_user.get_json()
        other_user_public_id = other_user_json['public_id']

        # Get a token for them, using correct username and password
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:secret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 200)
        user_token_json = user_token.get_json()

        # Retrieve another user's profile
        user_profile = self.client.get('/v1/users/%s' % other_user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(user_profile.status_code, 200)
        user_profile_json = user_profile.get_json()
        self.assertEqual(user_profile_json['public_id'], other_user_public_id)
        self.assertEqual(user_profile_json['username'], 'sara')
        self.assertFalse(user_profile_json.get('email'))
        self.assertEqual(user_profile_json['_links']['self'],
                '/v1/users/%s' % other_user_public_id)
        self.assertEqual(user_profile_json['_links']['followed'],
                '/v1/users/%s/followed' % other_user_public_id)
        self.assertEqual(user_profile_json['_links']['followers'],
                '/v1/users/%s/followers' % other_user_public_id)

    def test_user_follow_mechanic(self):
        """Test user follow api mechanic. Inlcudes following and unfollowing
        another user, and retrieving the followed and followers json lists
        for both sides of the following mechanic.

        Requires creating two users, getting a token, making one user follow
        the other, then retrieve the followers list from the main user."""
        response = self.client.get('/v1/users')
        self.assertEqual(response.status_code, 401)

        # Creat two users
        user = _register_user(self.client)
        user_json = user.get_json()
        user_public_id = user_json['public_id']
        other_user = self.client.post('/v1/users', json={
            'username': 'sara', 'email': 'sara@joshschertz.com', 'name': 'Sara',
            'password': 'secret'})
        other_user_json = other_user.get_json()
        other_user_public_id = other_user_json['public_id']

        # Get a token for them, using correct username and password
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:secret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 200)
        user_token_json = user_token.get_json()

        # Retrieve josh's following list which should be empty
        user_following = self.client.get('/v1/users/%s/followed' %
                user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(user_following.status_code, 200)
        user_following_json = user_following.get_json()
        self.assertEqual(len(user_following_json['items']), 0)

        # Make josh follow sara
        follow_request = self.client.post('/v1/users/%s/follow' %
                other_user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(follow_request.status_code, 200)

        # Retrieve josh's following list that should show sara
        user_following = self.client.get('/v1/users/%s/followed' %
                user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(user_following.status_code, 200)
        user_following_json = user_following.get_json()
        self.assertEqual(len(user_following_json['items']), 1)
        self.assertEqual(user_following_json['items'][0]['username'], 'sara')
        self.assertEqual(user_following_json['_meta']['total_items'], 1)

        # Retrieve sara's followed list that should show josh
        other_user_followers = self.client.get('/v1/users/%s/followers' %
                other_user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(other_user_followers.status_code, 200)
        other_user_followers_json = other_user_followers.get_json()
        self.assertEqual(len(other_user_followers_json['items']), 1)
        self.assertEqual(other_user_followers_json['items'][0]['username'],
                'josh')
        self.assertEqual(other_user_followers_json['_meta']['total_items'], 1)

        # Make josh unfollow sara
        follow_request = self.client.delete('/v1/users/%s/follow' %
                other_user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(follow_request.status_code, 204)

        # Retrieve josh's following list when it should be empty again
        user_following = self.client.get('/v1/users/%s/followed' %
                user_public_id,
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(user_following.status_code, 200)
        user_following_json = user_following.get_json()
        self.assertEqual(len(user_following_json['items']), 0)


if __name__ == '__main__':
    unittest.main()
