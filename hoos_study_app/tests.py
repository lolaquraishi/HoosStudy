from django.test import TestCase

# Create your tests here.
from .models import Course, User

class UserModelTest(TestCase):

    def test_user_str_representation(self):
        user = User.objects.create(username="testuser", first_name="Test", last_name="User")
        self.assertEqual(str(user), "testuser")

    def test_user_year_field(self):
        user = User.objects.create(username="student1", year='1')
        self.assertEqual(user.year, '1')
        self.assertEqual(user.get_year_display(), 'First Year')  # Test choice display

    def test_user_is_pma_admin_default(self):
        user = User.objects.create(username="testuser")
        self.assertFalse(user.is_pma_admin)  # By default, is_pma_admin should be False


class CourseModelTest(TestCase):

    def test_course_str_representation(self):
        course = Course.objects.create(mnemonic="CS", number=1010, title="Intro to Computer Science")
        self.assertEqual(str(course), "CS 1010 Intro to Computer Science")

    def test_course_has_students(self):
        course = Course.objects.create(mnemonic="CS", number=1010, title="Intro to Computer Science")
        user1 = User.objects.create(username="student1")
        user2 = User.objects.create(username="student2")
        
        course.students.add(user1, user2)
        
        self.assertIn(user1, course.students.all())
        self.assertIn(user2, course.students.all())
        self.assertEqual(course.students.count(), 2)