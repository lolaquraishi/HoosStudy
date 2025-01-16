import random
from faker import Faker
from django.core.management.base import BaseCommand
from hoos_study_app.models import User, Course

class Command(BaseCommand):
    help = "Generate dummy users and assign them to courses"

    def add_arguments(self, parser):
        # Optional argument to specify the number of users to create
        parser.add_argument(
            '--num_users', 
            type=int, 
            default=30, 
            help="Specify the number of dummy users to create (default: 30)"
        )

    def handle(self, *args, **options):
        faker = Faker()
        years = ['1', '2', '3', '4']
        courses = list(Course.objects.all())

        if not courses:
            self.stdout.write(self.style.ERROR("No courses found. Please add courses before running this command."))
            return

        # Get the number of users from the command argument
        num_users = options['num_users']

        for _ in range(num_users):
            try:
                username = f"dummy_{faker.unique.user_name()}"
                email = faker.unique.email()
                first_name = faker.first_name()
                last_name = faker.last_name()
                year = random.choice(years)
                password = faker.password(length=10)  # Random password for each user

                # Create the user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    year=year,
                    password=password
                )

                # Assign the user to random courses
                num_courses = random.randint(1, len(courses))  # Random number of courses per user
                user_courses = random.sample(courses, num_courses)
                for course in user_courses:
                    course.students.add(user)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating user or assigning courses: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {num_users} dummy users and assigned them to courses."))
