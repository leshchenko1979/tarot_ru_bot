import datetime as dt
import os

import psycopg

import utils

DATABASE_URI = os.environ["DATABASE_URI"]


async def set_up_db_connection():
    global aconn
    if not aconn:
        aconn = await psycopg.AsyncConnection.connect(DATABASE_URI)


async def close_db_connection():
    await aconn.close()


async def next_daily_cotd(this_morning: dt.datetime):
    """Iterate over users who need to be sent their daily card of the day.

    Such users have their `send_cotd` setting equal to 1 and haven't still
    received their card of the day today (since `this_morning`).

    Agruments:
        this_morning (dt.datetime): time of this morning, when
            the daily cards of the day are sent

    Yields:
        int: chat_id of the user
    """
    async with aconn.cursor() as cur:
        while True:
            await cur.execute(
                """
                SELECT id FROM users
                WHERE last_cotd < %(this_morning)s AND send_cotd = 1
                LIMIT 1
                """,
                {"this_morning": this_morning},
            )
            record = await cur.fetchone()

            if record:
                yield record[0]
            else:
                break


async def cotd_sent_today(chat_id: int):
    """Check if the user has already received his card of the day today.

    Args:
        chat_id (int): user chat_id
    """
    last_cotd = await load_last_cotd(chat_id)

    return last_cotd >= utils.start_of_day_MSK() if last_cotd else False


async def load_last_cotd(chat_id: int):
    """Load the time when the user has last received his card of the day.

    Args:
        chat_id (int): user chat_id
    """
    QUERY = "SELECT last_cotd FROM users WHERE id = %(id)s"

    async with aconn.cursor() as cur:
        await cur.execute(QUERY, {"id": chat_id})
        record = await cur.fetchone()

    return record[0] if record else None


async def save_send_cotd_setting(chat_id: int, new_setting: int):
    """Save the user's "send daily card of the day" setting."""

    async with aconn.cursor() as cur:
        await cur.execute(
            """
            UPDATE users SET
                send_cotd = %(new_setting)s,
                last_cotd = now()
            WHERE id = %(id)s
            """,
            {"new_setting": new_setting, "id": chat_id},
        )
    await aconn.commit()


async def update_last_request(chat_id: int):
    """Update the time of the last request of the user."""

    async with aconn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO users (id, last_request, last_cotd, send_cotd)
            VALUES (%(id)s, now(), now(), 1)
            ON CONFLICT (id) DO UPDATE SET last_request = now()
            """,
            {"id": chat_id},
        )
    await aconn.commit()


async def update_last_cotd(chat_id: int, cur: psycopg.AsyncCursor = None):
    """Update the time when the user has last received his card of the day.

    Args:
        chat_id (int): user chat_id
        cur (psycopg.AsyncCursor, optional): cursor to use. If None, a new cursor is used.
            Defaults to None.
    """
    QUERY = "UPDATE users SET last_cotd = now() WHERE id = %(id)s"

    if cur:
        await cur.execute(QUERY, {"id": chat_id})
    else:
        async with aconn.cursor() as cur:
            await cur.execute(QUERY, {"id": chat_id})

    await aconn.commit()
