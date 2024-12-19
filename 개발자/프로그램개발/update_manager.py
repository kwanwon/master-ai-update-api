import requests
import os
import json
import sys
import shutil
import subprocess
from version import VERSION
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from google.auth.transport.requests import Request
import pickle
from googleapiclient.http import MediaIoBaseDownload
import io

# API URL 설정
API_BASE_URL = "http://127.0.0.1:8080"  # 포트 변경
VERSION_CHECK_URL = f"{API_BASE_URL}/check_version"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']  # 읽기 전용 권한만 요청
FOLDER_ID = '1J7MuTkdfz8LsTIpg-dxZuZwithjL9yc_'  # 새로운 폴더 ID

class SerialStorage:
    def __init__(self):
        self.storage_path = os.path.join(os.path.expanduser('~'), '.ai사범님', 'serial.json')
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
    
    def save_serial(self, serial_number, expiration_date):
        """시리얼 정보를 저장"""
        data = {
            'serial_number': serial_number,
            'expiration_date': expiration_date
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)
    
    def load_serial(self):
        """저장된 시리얼 정보를 로드"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def clear_serial(self):
        """저장된 시리얼 정보를 삭제"""
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

def get_google_drive_service():
    """Google Drive API 서비스 객체를 생성하는 함수"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def check_for_updates():
    """업데이트 확인 함수"""
    try:
        service = get_google_drive_service()
        
        # update_info.json 파일 찾기
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents and name='update_info.json'",
            fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            print("업데이트 정보 파일을 찾을 수 없습니다.")
            return False
            
        # 업데이트 정보 읽기
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        update_info = json.loads(fh.read().decode())
        
        # 버전 비교
        current_version = VERSION
        new_version = update_info['version']
        
        print(f"현재 버전: {current_version}")
        print(f"최신 버전: {new_version}")
        
        return new_version > current_version
        
    except Exception as e:
        print(f"업데이트 확인 중 오류 발생: {e}")
        return False

def download_update():
    """업데이트 파일 다운로드 함수"""
    try:
        service = get_google_drive_service()
        
        # 업데이트 폴더 찾기
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)").execute()
        folders = results.get('files', [])
        
        if not folders:
            print("업데이트 폴더를 찾을 수 없습니다.")
            return False
            
        update_folder_id = folders[0]['id']
        
        # 업데이트 파일 다운로드
        results = service.files().list(
            q=f"'{update_folder_id}' in parents",
            fields="files(id, name)").execute()
        files = results.get('files', [])
        
        for file in files:
            request = service.files().get_media(fileId=file['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            fh.seek(0)
            with open(file['name'], 'wb') as f:
                f.write(fh.read())
        
        return True
        
    except Exception as e:
        print(f"업데이트 다운로드 중 오류 발생: {e}")
        return False

def perform_update():
    """업데이트를 수행하는 함수"""
    try:
        print("업데이트를 시작합니다...")
        
        # 1. 현재 디렉토리 확인
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backup_dir = os.path.join(current_dir, "backup")
        update_dir = os.path.join(current_dir, "update")
        
        # 2. 백업 디렉토리 생성
        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(update_dir, exist_ok=True)
        
        # 3. 현재 파일들 백업 (중요 파일만)
        print("프로그램 백업 중...")
        important_files = ['main.py', 'version.py', 'update_manager.py', 'update_client.py']
        for file in important_files:
            if os.path.exists(os.path.join(current_dir, file)):
                shutil.copy2(
                    os.path.join(current_dir, file),
                    os.path.join(backup_dir, file)
                )
        
        # 4. 버전 정보 업데이트
        version_file = os.path.join(current_dir, 'version.py')
        with open(version_file, 'w') as f:
            f.write(f'VERSION = "{latest_version}"')  # type: ignore # API에서 받은 버전으로 업데이트
        
        print("업데이트가 완료되었습니다.")
        return True
        
    except Exception as e:
        print(f"업데이트 중 오류: {e}")
        # 5. 오류 발생시 백업에서 복구
        try:
            if os.path.exists(backup_dir):
                for file in important_files:
                    backup_file = os.path.join(backup_dir, file)
                    if os.path.exists(backup_file):
                        shutil.copy2(backup_file, os.path.join(current_dir, file))
                print("백업에서 복구되었습니다.")
        except:
            print("복구 중 오류가 발생했습니다.")
        return False 