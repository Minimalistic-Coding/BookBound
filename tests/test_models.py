import os
from config import Config
from datetime import datetime, timezone, timedelta
import unittest
from app import db
from app.models import User, Comment, Book

class TestConfig(Config):
    TESTING = True  
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class UserModelCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username="Susan", email="susan1234@example.com")
        u.set_password("dog")
        self.assertFalse(u.check_password("cat"))
        self.assertTrue(u.check_password("dog"))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        following = db.session.scalars(u1.following.select()).all()
        followers = db.session.scalars(u2.followers.select()).all()

        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        u1.follow(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)

        u1_following = db.session.scalars(u1.following.select()).all()
        u2_followers = db.session.scalars(u2.followers.select()).all()

        self.assertEqual(u1_following[0].username, "susan")
        self.assertEqual(u2_followers[0].username, "john")

        u1.unfollow(u2)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_follow_comments(self):
        # Create Mock Books for Testing
        b1 = Book(
            title='The Midnight Library',
            price=18.99,
            rating=4,
            availability=15,
            description='Between life and death there is a library. When Nora Seed finds herself in the Midnight Library, she has a chance to make things right.',
            cover='https://example.com/covers/midnight_library.jpg'
        )

        b2 = Book(
            title='Project Hail Mary',
            price=22.50,
            rating=5,
            availability=8,
            description='A lone astronaut must save humanity from an extinction-level threat. Ryland Grace is the only survivor on a desperate mission.',
            cover='https://example.com/covers/project_hail_mary.jpg'
        )

        db.session.add_all([b1, b2])
        db.session.commit()

        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()

        # create four comments
        now = datetime.now(timezone.utc)
        p1 = Comment(body="comment from john", author=u1, book=b1,
                     timestamp=now + timedelta(seconds=1))
        p2 = Comment(body="comment from susan", author=u2, book=b2,
                     timestamp=now + timedelta(seconds=4))
        p3 = Comment(body="comment from mary", author=u3, book=b1,
                     timestamp=now + timedelta(seconds=3))
        p4 = Comment(body="comment from david", author=u4, book=b2,
                     timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # get feeds
        f1 = db.session.scalars(u1.following_comments()).all()
        f2 = db.session.scalars(u2.following_comments()).all()
        f3 = db.session.scalars(u3.following_comments()).all()
        f4 = db.session.scalars(u4.following_comments()).all()

        # assert
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

if __name__ == "__main__":
    unittest.main(verbosity=2)