import sys
import unittest

from flask import current_app

sys.path.append('../')
from app import create_app  # NOQA
from config import DevelopmentConfig, ProductionConfig, TestingConfig   # NOQA


class TestDevelopmentConfig(unittest.TestCase):

    def setUp(self):
        self.app = create_app(DevelopmentConfig)

    def test_app_is_development(self):
        self.assertFalse(current_app is None)
        self.assertFalse(self.app.config['TESTING'])


class TestTestingConfig(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)

    def test_app_is_testing(self):
        self.assertTrue(self.app.config['TESTING'])
        self.assertTrue(self.app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite://')


class TestProductionConfig(unittest.TestCase):

    def setUp(self):
        self.app = create_app(ProductionConfig)

    def test_app_is_production(self):
        self.assertFalse(self.app.config['TESTING'])


if __name__ == '__main__':
    unittest.main()
