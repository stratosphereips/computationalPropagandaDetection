from DB.propaganda_db import DB
from DB.create_db import create_db
import datetime
import pytest
import os

path = os.path.join(os.path.dirname(__file__), "test_propaganda.db")


@pytest.fixture
def db():
    create_db(path)
    db = DB(path)
    yield db
    os.remove(path)


def test_times(db):
    time_today = datetime.datetime.now()
    time_tommorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    link_1 = "link_1"
    db.insert_url(url=link_1, date_of_query=time_today, is_propaganda=1)
    db.insert_url(url=link_1, date_of_query=time_tommorrow, is_propaganda=1)

    # for link un URL we save the last date of the query
    returned_time = db.get_date_of_query_url(link_1)
    assert str(time_tommorrow) == returned_time

    link_2 = "link_2"
    db.insert_url(url=link_2, date_of_query=time_tommorrow, is_propaganda=0)
    db.insert_link_urls(link_1, link_2, link_date=time_today)
    db.insert_link_urls(link_1, link_2, link_date=time_tommorrow)

    # for the link we save the first query date
    returned_time = db.get_date_of_link(link_1, link_2)
    assert str(time_today) == returned_time

    # check if link doesnt exist
    returned_time = db.get_date_of_query_url("not_existing_link1")
    assert returned_time is None
