import sys
import unittest

sys.path.append('../')
from app import db                      # NOQA
from app.models import User             # NOQA
from tests.base import BaseTestCase     # NOQA


class UserModelCase(BaseTestCase):

    def test_model_password_hashing(self):
        """Test the password hashing."""
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_model_follow(self):
        """Test the user following mechanic."""
        u1 = User(username='josh', email='josh@example.com', public_id='1',
                group='user')
        u1.set_password('cat')
        u2 = User(username='sara', email='sara@example.com', public_id='2',
                group='user')
        u2.set_password('cat')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u2.followed.all(), [])

        # Test the follow mechanic
        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'sara')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'josh')

        # Test the unfollow mechanic
        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)


if __name__ == '__main__':
    unittest.main()
