#tbl_change_notify.py
import oracledb
import threading
import time

# Enable Thick mode (assuming Instant Client is installed and configured)
oracledb.init_oracle_client()

# Database connection details
DB_USER = "your_user"
DB_PASSWORD = "your_password"
DB_DSN = "your_dsn"

def notification_handler(message):
    print("Notification received:")
    for query_id, table_name, row_ids in message.tables:
        print(f"  Table: {table_name}, Query ID: {query_id}")
        if row_ids:
            print(f"    Affected ROWIDs: {row_ids}")
    print("-" * 20)

def main():
    connection = None
    try:
        connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        print("Connected to Oracle Database.")

        # Create a subscription for CQN
        subscription = connection.subscribe(
            callback=notification_handler,
            timeout=3600, # Subscription timeout in seconds
            qos=oracledb.SUBSCR_QOS_QUERY | oracledb.SUBSCR_QOS_ROWIDS # Get rowids
        )

        # Register a query to monitor a table
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM your_table", subscription=subscription)
        cursor.close()

        print("CQN subscription registered for 'your_table'. Monitoring for changes...")
        print("Press Ctrl+C to stop.")

        # Keep the main thread alive to receive notifications
        while True:
            time.sleep(1)

    except oracledb.Error as e:
        print(f"Oracle error: {e}")
    finally:
        if connection:
            connection.close()
            print("Connection closed.")

if __name__ == "__main__":
    main()
