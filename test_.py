import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import hypothesis.strategies as st
import pytest
from hypothesis import given

import db
import cards


@given(no=st.integers(min_value=0, max_value=cards.CARDS - 1))
def test_get_name_and_image(no):
    cards.get_name(no)
    cards.get_image(cards.im, no)


@pytest.fixture
async def database():
    try:
        await db.set_up_db_connection()
        yield
    finally:
        await db.close_db_connection()


@pytest.mark.asyncio
async def test_cotd_sent_today(database):
    chat_id = 133526395
    assert await db.cotd_sent_today(chat_id)
