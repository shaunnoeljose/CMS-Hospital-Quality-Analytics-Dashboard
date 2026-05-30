from sqlalchemy import create_engine

# Update this if your SQL Server name is different.
# Common options:
# SERVER = "localhost"
# SERVER = "localhost\\SQLEXPRESS"
# SERVER = ".\\SQLEXPRESS"

SERVER = "localhost"
DATABASE = "cms_hospital_quality"
DRIVER = "ODBC Driver 17 for SQL Server"


def get_engine():
    connection_string = (
        f"mssql+pyodbc://@{SERVER}/{DATABASE}"
        f"?driver={DRIVER.replace(' ', '+')}"
        "&trusted_connection=yes"
    )

    engine = create_engine(
        connection_string,
        fast_executemany=True
    )

    return engine