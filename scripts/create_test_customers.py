from razorpay.errors import BadRequestError
from app.integrations.razorpay import create_test_customer

customers = [
    ("Rahul Sharma", "rahul@test.com", "9000000001"),
    ("Priya Mehta", "priya@test.com", "9000000002"),
    ("Amit Verma", "amit@test.com", "9000000003"),
    ("Neha Kapoor", "neha@test.com", "9000000004"),
    ("Arjun Malhotra", "arjun@test.com", "9000000005"),
    ("Sneha Iyer", "sneha@test.com", "9000000006"),
    ("Vikram Singh", "vikram@test.com", "9000000007"),
    ("Ananya Rao", "ananya@test.com", "9000000008"),
    ("Karan Patel", "karan@test.com", "9000000009"),
    ("Riya Shah", "riya@test.com", "9000000010"),
]


for name, email, contact in customers:

    try:
        customer = create_test_customer(
            name=name,
            email=email,
            contact=contact,
        )

        print(f"Created: {customer['id']} | {customer['name']}")

    except BadRequestError as e:
        if "already exists" in str(e):
            print(f"Already exists: {name}")
        else:
            raise