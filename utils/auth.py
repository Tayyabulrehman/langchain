users = [
    {
        "email": "senteze1@yopmail.com",
        "password": "Pass1234@",
        "role": "employee"
    },
    {
        "email": "senteze2@yopmail.com",
        "password": "Pass1234@",
        "role": "employee"
    },
    {
        "email": "fascicoli1@yopmail.com",
        "password": "Pass1234@",
        "role": "manager"
    },
    {
        "email": "fascicoli2@yopmail.com",
        "password": "Pass1234@",
        "role": "manager"
    },
    {
        "email": "superadmin@yopmail.com",
        "password": "Pass1234@",
        "role": "admin"
    },
]


def authenticate(email: str, password: str):
    try:
        return list(filter(lambda x: x["email"] == email and x["password"] == password, users))[0]
    except:
        return None
