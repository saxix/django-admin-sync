import json

from admin_sync.utils import (
    decode_natural_key,
    encode_natural_key,
    # get_client_ip,
    # is_logged_to_remote,
    remote_reverse,
    # render,
    # set_cookie,
    unwrap,
    wraps,
)

DATA = (
    '{"data": "%5B%7B%22model%22%3A%20%22auth.user%22%2C%20%22fields%22%3A%20%7B%22'
    "password%22%3A%20%22%22%2C%20%22last_login%22%3A%20%222022-09-05T15%3A17%3A28."
    "017Z%22%2C%20%22is_superuser%22%3A%20true%2C%20%22username%22%3A%20%22"
    "pippo2%22%2C%20%22first_name%22%3A%20%22%22%2C%20%22last_name%22%3A%20%22%22%2C%20%22"
    "email%22%3A%20%22pippo2%40demo.org%22%2C%20%22is_staff%22%3A%20true%2C%20%22"
    "is_active%22%3A%20true%2C%20%22date_joined%22%3A%20%222022-09-05T15%3A17%3A28.009Z%22%2C%20%22"
    "groups%22%3A%20%5B%5D%2C%20%22user_permissions%22%3A%20%5B%5D%7D%7D%2C%20%7B%22"
    "model%22%3A%20%22auth.user%22%2C%20%22fields%22%3A%20%7B%22password%22%3A%20%22%22%2C%20%22"
    "last_login%22%3A%20%222022-09-05T15%3A23%3A41.500Z%22%2C%20%22is_superuser%22%3A%20true%2C%20%22"
    "username%22%3A%20%22sss%22%2C%20%22first_name%22%3A%20%22%22%2C%20%22"
    "last_name%22%3A%20%22%22%2C%20%22email%22%3A%20%22sss%40demo.org%22%2C%20%22"
    "is_staff%22%3A%20true%2C%20%22is_active%22%3A%20true%2C%20%22"
    "date_joined%22%3A%20%222022-09-05T15%3A18%3A08.198Z%22%2C%20%22groups%22%3A%20%5B%5D%2C%20%22"
    "user_permissions%22%3A%20%5B%5D%7D%7D%2C%20%7B%22model%22%3A%20%22auth.user%22%2C%20%22"
    "fields%22%3A%20%7B%22password%22%3A%20%22%22%2C%20%22"
    "last_login%22%3A%20%222022-09-06T03%3A40%3A36.060Z%22%2C%20%22is_superuser%22%3A%20"
    "true%2C%20%22username%22%3A%20%22admin%22%2C%20%22first_name%22%3A%20%22%22%2C%20%22"
    "last_name%22%3A%20%22%22%2C%20%22email%22%3A%20%22admin%40demo.org%22%2C%20%22"
    "is_staff%22%3A%20true%2C%20%22is_active%22%3A%20true%2C%20%22"
    "date_joined%22%3A%20%222022-09-06T03%3A31%3A18.124Z%22%2C%20%22groups%22%3A%20%5B%5D%2C%20%22"
    'user_permissions%22%3A%20%5B%5D%7D%7D%5D"}'
)


def test_unwrap():
    source = json.dumps({"a": 1})
    assert unwrap(wraps(source)) == source


def test_remote_reverse():
    assert remote_reverse("admin:login") == "http://remote/login/"


def test_encode_natural_key(admin_user):
    assert decode_natural_key(encode_natural_key(admin_user)) == admin_user.natural_key()
