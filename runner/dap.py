import random
import string


def generate_task_id():
    return random.randbytes(32)


def generate_auth_token(label: str):
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(random.choices(alphabet, k=20))
    return f"{label}-{random_part}"
