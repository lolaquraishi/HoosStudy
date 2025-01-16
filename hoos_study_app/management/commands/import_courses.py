import requests
from django.core.management.base import BaseCommand
from hoos_study_app.models import Course
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Import courses from SIS API'

    def add_arguments(self, parser):
        # Default term is set to '1248'
        parser.add_argument('--term', type=str, default='1248', help="Term code for the courses, e.g., 1248 for Fall 2024. Defaults to 1248.")
        parser.add_argument('--subject', type=str, required=True, help="Department code, e.g., CS for Computer Science.")

        # Optional arguments
        parser.add_argument('--catalog_nbr', type=str, required=False, help="Specific course number to filter, e.g., 1010 for CS1010.")
        parser.add_argument('--page', type=int, required=False, help="Specify a page number to import only that page's courses.")

    def handle(self, *args, **options):
        term = options['term']
        subject = options['subject']
        catalog_nbr = options.get('catalog_nbr')
        single_page = options.get('page')  # Get the specified page number if provided

        # Map term codes to readable semester names
        term_mapping = {
            "2": "Spring",
            "8": "Fall"
        }
        year = f"20{term[1:3]}"  # Extract year from the term
        semester_key = term[3]  # Extract semester key (2 or 8)
        semester = f"{term_mapping.get(semester_key, 'Unknown')} {year}"  # e.g., "Fall 2024"

        page = single_page if single_page else 1

        while True:
            # Build the URL with optional catalog number and page filtering
            url = f"https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UVA01&term={term}&subject={subject}&page={page}"
            if catalog_nbr:
                url += f"&catalog_nbr={catalog_nbr}"

            response = requests.get(url)

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR("Failed to fetch data"))
                break

            try:
                data = response.json()
                print(data)
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"Failed to parse JSON response: {e}"))
                break

            # Extract the 'classes' key from the response
            classes = data.get('classes', [])

            if not classes:
                self.stdout.write(self.style.WARNING("No classes found. Ending import."))
                break  # Exit the loop if there are no courses on this page

            for course_data in classes:
                # Extracting data for each course
                mnemonic = course_data.get('subject')
                number = course_data.get('catalog_nbr')
                title = course_data.get('descr')

                # Creating or updating the course in the database
                course, created = Course.objects.update_or_create(
                    mnemonic=mnemonic,
                    number=number,
                    defaults={'title': title, 'semester': semester}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created course {course}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Updated course {course}"))

            # Break if a single page was specified
            if single_page:
                break

            page += 1  # Move to the next page for more courses
            if page > data.get('pageCount', 1):  # Stop if the current page exceeds total pages
                break

        self.stdout.write(self.style.SUCCESS("Courses imported successfully"))
