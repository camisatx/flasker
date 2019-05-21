import sys
import unittest

sys.path.append('../')
from app import create_test_app, db      # NOQA
from config import TestingConfig    # NOQA


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_test_app(TestingConfig)
        # Push an app context for the app instance just created
        #   app_context (current_app) and request_context (current_user)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
