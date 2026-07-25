import mysql.connector


def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="391112",
        database="ai3dstudio"
    )

def save_aircraft(
    name,
    wingspan,
    fuselage_length
):

    conn = get_connection()

    cursor = conn.cursor()

    query = """
    INSERT INTO aircraft
    (
        name,
        wingspan,
        fuselage_length
    )
    VALUES
    (%s,%s,%s)
    """

    cursor.execute(
        query,
        (
            name,
            wingspan,
            fuselage_length
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

def save_model(
    name,
    model_type
):

    print(
        f"Saved {name} ({model_type})"
    )