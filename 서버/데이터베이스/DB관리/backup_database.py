# backup_database.py

import shutil
from datetime import datetime

def backup_database():
    source = 'serial_numbers.db'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = f'serial_numbers_backup_{timestamp}.db'
    shutil.copyfile(source, destination)
    print(f"데이터베이스가 '{destination}'으로 백업되었습니다.")

if __name__ == "__main__":
    backup_database()