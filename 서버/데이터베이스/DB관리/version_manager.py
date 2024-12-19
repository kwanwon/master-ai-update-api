import sqlite3
import os
import json

class VersionManager:
    def __init__(self):
        # 현재 파일의 디렉토리 경로
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # DB 파일 경로
        self.db_path = os.path.join(current_dir, 'serials.db')
        
        # updates 폴더 경로
        self.updates_path = os.path.join(current_dir, 'updates')
        
        # updates 폴더가 없으면 생성
        if not os.path.exists(self.updates_path):
            os.makedirs(self.updates_path)
            print(f"updates 폴더 생성됨: {self.updates_path}")
    
    def add_version_table(self):
        """버전 정보를 저장할 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS program_versions (
                    version_number TEXT PRIMARY KEY,
                    release_date TEXT,
                    description TEXT,
                    is_required INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            
        except Exception as e:
            print(f"테이블 생성 중 오류: {e}")
            
        finally:
            cursor.close()
            conn.close()
    
    def add_new_version(self, version, release_date, description, is_required=0):
        """새로운 버전 정보 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO program_versions 
                (version_number, release_date, description, is_required)
                VALUES (?, ?, ?, ?)
            ''', (version, release_date, description, is_required))
            conn.commit()
            print(f"새 버전 {version} 추가됨")
            
        except Exception as e:
            print(f"버전 추가 중 오류: {e}")
            
        finally:
            cursor.close()
            conn.close()
    
    def get_latest_version(self):
        """최신 버전 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT version_number, release_date, description, is_required
                FROM program_versions
                ORDER BY CAST(REPLACE(REPLACE(version_number, 'v', ''), '.', '') AS INTEGER) DESC
                LIMIT 1
            ''')
            return cursor.fetchone()
            
        except Exception as e:
            print(f"버전 조회 중 오류: {e}")
            return None
            
        finally:
            cursor.close()
            conn.close()
    
    def reset_version_table(self):
        """버전 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DROP TABLE IF EXISTS program_versions')
            conn.commit()
            print("버전 테이블이 초기화되었습니다.")
            
        except Exception as e:
            print(f"테이블 초기화 중 오류: {e}")
            
        finally:
            cursor.close()
            conn.close()
    
    def get_update_files(self, version):
        """특정 버전의 업데이트 파일 정보 반환"""
        try:
            # 업데이트 폴더 경로
            update_path = os.path.join(self.updates_path, version)
            info_file = os.path.join(update_path, 'update_info.json')
            
            print(f"업데이트 정보 파일 경로: {info_file}")
            
            if not os.path.exists(info_file):
                print(f"버전 {version}의 업데이트 정보 파일이 없습니다.")
                return None
            
            # JSON 파일 읽기
            with open(info_file, 'r', encoding='utf-8') as f:
                update_info = json.load(f)
            
            return update_info
            
        except Exception as e:
            print(f"업데이트 파일 정보 읽기 오류: {e}")
            return None

if __name__ == "__main__":
    vm = VersionManager()
    
    # 0. 테이블 초기화 (기존 데이터 삭제)
    print("테이블 초기화 중...")
    vm.reset_version_table()
    
    # 1. 테이블 생성
    print("\n버전 관리 테이블 생성 중...")
    vm.add_version_table()
    
    # 2. 초기 버전 정보 추가
    print("\n초기 버전 정보 추가 중...")
    vm.add_new_version(
        version="1.0.0",
        release_date="2024-03-26",
        description="초기 버전",
        is_required=0
    )
    
    # 3. 업데이트 버전 정보 추가
    print("\n업데이트 버전 정보 추가 중...")
    vm.add_new_version(
        version="1.1.0",
        release_date="2024-03-26",
        description="버그 수정 및 새로운 기능 추가",
        is_required=1
    )
    
    # 4. 최신 버전 정보 확인
    print("\n최신 버전 정보 확인 중...")
    latest = vm.get_latest_version()
    if latest:
        print(f"최신 버전: {latest[0]}")
        print(f"배포일: {latest[1]}")
        print(f"설명: {latest[2]}")
        print(f"필수 업데이트: {'예' if latest[3] else '아니오'}")
        
        # 5. 업데이트 파일 정보 확인
        print("\n업데이트 파일 정보:")
        update_info = vm.get_update_files(latest[0])
        if update_info:
            print(f"버전: {update_info['version']}")
            print("포함된 파일:")
            for file in update_info['files']:
                print(f"- {file}")
            print(f"필수 업데이트: {'예' if update_info['required'] else '아니오'}")
        else:
            print("업데이트 파일 정보를 찾을 수 없습니다.")