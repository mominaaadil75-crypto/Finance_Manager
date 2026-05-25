import sqlite3

def print_table(table_name):
    """Prints all data from a specific table"""
    print(f"\n{'='*50}")
    print(f"CONTENTS OF {table_name.upper()} TABLE")
    print('='*50)
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print("No records found")
        return
    
    # Print column headers
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    print(" | ".join(columns))
    print("-" * 80)
    
    # Print all rows
    for row in rows:
        print(" | ".join(str(value) for value in row))

# Connect to database
conn = sqlite3.connect('finance.db')
cursor = conn.cursor()

# View all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\nDATABASE TABLES:")
for table in tables:
    print(f"- {table[0]}")

# View contents of each table
print_table('transactions')
print_table('budgets')
print_table('savings')

# Close connection
conn.close()

print("\nDatabase inspection complete!")