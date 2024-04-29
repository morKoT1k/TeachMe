import random
import string
from models import User, Student  # Assuming the User and Student models are defined in models.py
from extensions import db
import logging
from routes.auth import generate_username

# List of sample surnames and names
surnames = [
    "Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Kučera", "Veselý", "Horák", "Němec",
    "Pokorný", "Pospíšil", "Marek", "Hájek", "Jelínek", "Král", "Richter", "Fiala", "Urban", "Havlíček",
    "Zeman", "Beneš", "Šťastný", "Šimůnek", "Fišer", "Štěpánek", "Mráz", "Nádherný", "Válek", "Krejčí",
    "Bartoš", "Hudec", "Sýkora", "Kopecký", "Růžička", "Kolář", "Bártová", "Vlček", "Kříž", "Šebestová",
    "Nešpor", "Horváth", "Mach", "Marák", "Ševčík", "Vaňková", "Konečný", "Blažek", "Kubík", "Vlach",
    "Křížová", "Adamová", "Holub", "Dušek", "Ludvík", "Němcová", "Růžičková", "Machová", "Čermák", "Kučerová",
    "Vaněk", "Nováková", "Tichý", "Pospíchal", "Matějka", "Holá", "Štěpánová", "Kratochvíl", "Kratochvílová",
    "Kubíček", "Mareček", "Šimáček", "Čížek", "Kubíková", "Pokorná", "Horáček", "Dušková", "Doležal", "Nováček",
    "Richtrová", "Hruška", "Zábranský", "Vondráček", "Svobodová", "Urbanová", "Macháček", "Novotná", "Havránek",
    "Doležel", "Růžička", "Tichá", "Blažková", "Holá", "Šimek", "Šulc", "Šimánek", "Blahová", "Hlaváček"
]
names = [
    "Jan", "Petr", "Pavel", "Martin", "Josef", "Jakub", "Tomáš", "Miroslav", "František", "Milan",
    "Jaroslav", "Michal", "Václav", "David", "Lukáš", "Jiří", "Karel", "Zdeněk", "Radek", "Vladimír",
    "Adam", "Aleš", "Daniel", "Ondřej", "Stanislav", "Marek", "Jiří", "Jana", "Marie", "Eva",
    "Hana", "Anna", "Lenka", "Kateřina", "Lucie", "Petra", "Alena", "Martina", "Veronika", "Barbora",
    "Jitka", "Ivana", "Zdeňka", "Elena", "Dagmar", "Jarmila", "Ludmila", "Markéta", "Věra", "Simona",
    "Tereza", "Michaela", "Monika", "Zuzana", "Andrea", "Vladimíra", "Iveta", "Adéla", "Denisa", "Dominika",
    "Klára", "Kristýna", "Nikola", "Renata", "Romana", "Stanislava", "Šárka", "Štěpánka", "Vendula", "Vlasta",
    "Zlata", "Bohumila", "Bohuslava", "Božena", "Diana", "Gabriela", "Gita", "Hedvika", "Hedva", "Helena",
    "Hermína", "Charvát", "Kubíček", "Kvasnička", "Ludvík", "Macek", "Nábělek", "Nešpor", "Novák", "Novosad"
]

def generate_dummy_users(app, num_users=100):
    with app.app_context():
        logging.info(f"Generating {num_users} dummy users...")
        if User.query.count() >= 100:
            logging.warning("There are already 100 or more users in the database. No additional users will be generated.")
            return

        for _ in range(num_users):
            # Randomly select a surname and name from the lists
            name = random.choice(names)
            surname = random.choice(surnames)

            # Generate a unique username
            username = generate_username(surname)
            # Generate a random email with 12 characters
            random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            email = f"{random_part}@mail.com"

            # Create a new User instance
            user = User(
                name=name,
                surname=surname,
                email=email,  # Assuming email format based on surname
                registered=True,
                username=username,
                is_teacher=False
            )
            user.set_password("12345678")

            # Create a corresponding Student instance
            new_student = Student(
                username=user.username,
                surname=user.surname,
                name=user.name
            )

            # Add both user and student to the database session
            db.session.add(user)
            db.session.add(new_student)

        # Commit all changes to the database
        db.session.commit()
        logging.info(f"Generated {num_users} dummy users successfully.")
