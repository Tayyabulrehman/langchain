users = [
    {
        "email": "senteze@yopmail.com",
        "password": "Pass1234@",
        "role": "employee"
    },
    {
        "email": "fascicoli@yopmail.com",
        "password": "Pass1234@",
        "role": "manager"
    },
    {
        "email": "affairs@astutesoftwares.com",
        "password": "Pass1234@",
        "role": "admin"
    },
]


def authenticate(email: str, password: str):
    try:
        return list(filter(lambda x: x["email"] == email and x["password"] == password, users))[0]
    except:
        return None




