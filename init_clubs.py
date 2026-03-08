import os
import json

USER_DATA_DIR = 'user_data'

def init_clubs_file():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    clubs_file = os.path.join(USER_DATA_DIR, 'clubs.json')
    
    if not os.path.exists(clubs_file):
        with open(clubs_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print(f'已创建 {clubs_file}')
    else:
        print(f'{clubs_file} 已存在')

if __name__ == '__main__':
    init_clubs_file()
