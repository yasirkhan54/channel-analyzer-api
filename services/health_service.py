from configurations.database_configuration import database


async def is_database_healthy() -> bool:
    try:
        await database.query_raw("SELECT 1")
    except Exception:
        return False
    return True
