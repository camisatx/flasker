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

    def test_add_user(self):
        response = _register_user(self.client)
        json_data = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json_data['username'], 'josh')
        self.assertEqual(json_data['email'], 'josh@joshschertz.com')
        self.assertEqual(json_data['name'], 'Josh')
        self.assertEqual(json_data['group'], 'admin')

    def test_add_user_missing_param(self):
        """Test to make sure username, email, name, and password are required
        in order to create an account."""
        response = self.client.post('/v1/users', json={
            'username': 'josh', 'email': 'josh@joshschertz.com',
            'password': 'secret'})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/v1/users', json={
            'username': 'josh', 'name': 'Josh', 'password': 'secret'})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/v1/users', json={
            'email': 'josh@joshschertz.com', 'name': 'Josh',
            'password': 'secret'})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/v1/users', json={
            'username': 'josh', 'email': 'josh@joshschertz.com',
            'name': 'Josh'})
        self.assertEqual(response.status_code, 400)

    def test_add_user_existing_username(self):
        """Test to ensure potential new accounts are not created when an
        existing account with the same username or email already exists."""
        response = self.client.post('/v1/users', json={
            'username': 'josh', 'email': 'josh@joshschertz.com',
            'name': 'Josh', 'password': 'secret'})
        self.assertEqual(response.status_code, 201)
        response = self.client.post('/v1/users', json={
            'username': 'josh', 'email': 'josh1@joshschertz.com',
            'name': 'Josh', 'password': 'secret'})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/v1/users', json={
            'username': 'josh1', 'email': 'josh@joshschertz.com',
            'name': 'Josh', 'password': 'secret'})
        self.assertEqual(response.status_code, 400)

    def test_edit_user(self):
        """Test the ability to edit the current user, including their email,
        username, name, and about_me values."""
        response = self.client.get('/v1/users')
        self.assertEqual(response.status_code, 401)

        # Creat 2 users
        user = _register_user(self.client)
        user_json = user.get_json()
        user_public_id = user_json['public_id']
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

        # Change the username to new valid username
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'username': 'bob'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 200)
        new_user_profile_json = new_user_profile.get_json()
        self.assertEqual(new_user_profile_json['username'], 'bob')

        # Change the username to block list username
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'username': 'admin'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 400)

        # Change the username to an existing username (sara)
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'username': 'sara'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 400)

        # Change email to new valid email
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'email': 'newjosh@joshschertz.com'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 200)
        new_user_profile_json = new_user_profile.get_json()
        self.assertEqual(new_user_profile_json['email'],
                'newjosh@joshschertz.com')

        # Change email to existing email (sara@joshschertz.com)
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'email': 'sara@joshschertz.com'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 400)

        # Change name
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'name': 'Josh Bob'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 200)
        new_user_profile_json = new_user_profile.get_json()
        self.assertEqual(new_user_profile_json['name'], 'Josh Bob')

        # Change email, name, and about_me
        new_user_profile = self.client.put('/v1/users/%s' % user_public_id,
                json={'email': 'bob@joshschertz.com', 'name': 'Bob',
                    'about_me': 'I like solo travel and freedom'},
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(new_user_profile.status_code, 200)
        new_user_profile_json = new_user_profile.get_json()
        self.assertEqual(new_user_profile_json['email'], 'bob@joshschertz.com')
        self.assertEqual(new_user_profile_json['name'], 'Bob')
        self.assertEqual(new_user_profile_json['about_me'],
                'I like solo travel and freedom')

    def test_get_user_token(self):
        """Test process to get a token for a user."""
        response = self.client.post('/v1/tokens')   # no auth should fail
        self.assertEqual(response.status_code, 401)

        # First create a user
        _register_user(self.client)

        # Try getting a token, but using a wrong password; Should fail
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:wrongsecret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 401)

        # Get a token for them, using correct username and password
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:secret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 200)

    def test_revoke_user_token(self):
        """Test the token revokcation function"""
        _register_user(self.client)

        # Get a token for them, using correct username and password
        user_token = self.client.post('/v1/tokens',
                headers={'Authorization': 'Basic ' +
                    base64.b64encode(('josh:secret')
                        .encode('utf-8')).decode('utf-8')})
        self.assertEqual(user_token.status_code, 200)
        user_token_json = user_token.get_json()

        # Try using the token to ensure it works
        users = self.client.get('/v1/users',
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(users.status_code, 200)

        # Revoke the user token; will return a 204 status code
        revokation = self.client.delete('/v1/tokens',
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(revokation.status_code, 204)

        # Now that the token has been revoked, trying to use it should fail
        users = self.client.get('/v1/users',
                headers={'Authorization': 'Bearer ' + user_token_json['token']})
        self.assertEqual(users.status_code, 401)


if __name__ == '__main__':
    unittest.main()
