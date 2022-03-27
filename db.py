import os

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]


async def set_up_db_connection():
    global aconn
    aconn = await psycopg.AsyncConnection.connect(DATABASE_URL)


async def close_db_connection():
    await aconn.close()


async def next_daily_cotd(this_morning):
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


async def save_send_cotd_setting(chat_id, new_setting):
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


async def update_last_request(chat_id):
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


async def update_last_cotd(chat_id, cur=None):
    QUERY = "UPDATE users SET last_cotd = now() WHERE id = %(id)s"

    if cur:
        await cur.execute(QUERY, {"id": chat_id})
    else:
        with aconn.cursor() as cur:
            await cur.execute(QUERY, {"id": chat_id})

    await aconn.commit()
