import PyInstaller.__main__
import os
import shutil
import sys

# 현재 디렉토리 경로 확인
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

# 정확한 tkinterdnd2 경로
tkdnd_path = os.path.join(parent_dir, 'venv', 'Lib', 'site-packages', 'tkinterdnd2')

print(f"tkdnd 경로가 존재하는지 확인: {os.path.exists(tkdnd_path)}")  # 디버깅용

# 아이콘 파일 경로
icon_path = os.path.join(parent_dir, '배포용', '리소스', 'myicon.ico')

# 시리얼관리 폴더 경로
serial_validator_path = os.path.join(parent_dir, '개발자', '시리얼관리')

# 기존 파일 정리
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")
for file in os.listdir():
    if file.endswith(".spec"):
        os.remove(file)

# main.py의 전체 경로
main_path = os.path.join(current_dir, 'main.py')

print(f"아이콘 경로: {icon_path}")
print(f"시리얼 검증 모듈 경로: {serial_validator_path}")
print(f"tkdnd 경로: {tkdnd_path}")
print(f"메인 파일 경로: {main_path}")

# PyInstaller 실행
PyInstaller.__main__.run([
    main_path,
    '--name=AI사범님',
    '--onefile',
    '--noconsole',
    '--clean',
    f'--icon={icon_path}',
    f'--paths={serial_validator_path}',
    '--hidden-import=serial_validator',
    '--hidden-import=tkinterdnd2',
    '--hidden-import=_tkinter',
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.filedialog',
    '--hidden-import=pygame',
    f'--add-data={tkdnd_path}/*;tkinterdnd2/',  # 수정된 부분
    '--collect-all=tkinterdnd2'
])