# serials_validator.py (전체 수정된 코드)

import sqlite3
import os
from datetime import datetime, timedelta
from tkinter import Tk, messagebox, simpledialog
import uuid
import hashlib
import tkinter as tk
from tkinter import ttk
import pyperclip
import requests
import platform
import sys
from serial_storage import SerialStorage

def validate_serial(serial_number=None, root=None):
    """시리얼 넘버의 유효성을 검증"""
    storage = SerialStorage()
    
    try:
        # 저장된 시리얼 정보 확인
        saved_serial = storage.load_serial()
        if saved_serial:
            serial_number = saved_serial['serial_number']
            expiration_date = datetime.strptime(saved_serial['expiration_date'], '%Y-%m-%d').date()
            
            # 만료 여부 확인
            days_left = (expiration_date - datetime.now().date()).days
            
            if days_left < 0:
                # 만료된 경우
                messagebox.showwarning("시리얼 만료", "시리얼 넘버가 만료되었습니다. 새로운 시리얼을 입력해주세요.")
                storage.clear_serial()
                return validate_serial(None, root)
            elif days_left <= 7:
                # 만료 임박
                messagebox.showwarning("시리얼 만료 임박", f"시리얼 넘버가 {days_left}일 후 만료됩니다.")
            
            return True
            
        # 저장된 시리얼이 없는 경우
        if serial_number is None:
            serial_number = simpledialog.askstring(
                "시리얼 넘버 입력", 
                "시리얼 넘버를 입력하세요:"
            )
            if serial_number is None:  # 취소 버튼 클릭
                return False

        # DB에서 시리얼 검증
        if validate_serial_from_db(serial_number):
            # 유효한 시리얼이면 저장
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT expiration_date FROM serial_numbers WHERE serial_number = ?', (serial_number,))
            expiration_date = cursor.fetchone()[0]
            conn.close()
            
            storage.save_serial(serial_number, expiration_date)
            return True
        else:
            messagebox.showerror("오류", "올바르지 않은 시리얼 넘버입니다.")
            return validate_serial(None, root)
            
    except Exception as e:
        print(f"시리얼 검증 중 오류: {e}")
        return False

def validate_serial_from_db(serial_number):
    """시리얼 넘버의 유효성을 검증하고, 디바이스와 연동합니다."""
    try:
        # 개발 중에는 항상 True 반환
        return True
    except Exception as e:
        print(f"DB 검증 중 오류: {e}")
        return False

def generate_serial_number(expiration_days=365):
    unique_id = uuid.uuid4().hex[:8].upper()
    creation_date = datetime.now().strftime('%Y%m%d')
    expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime('%Y%m%d')
    serial_prefix = f"SN-{unique_id}-{creation_date}-{expiration_date}"
    verification_code = hashlib.sha256(serial_prefix.encode()).hexdigest()[:8].upper()
    serial_number = f"{serial_prefix}-{verification_code}"
    return serial_number

# 데이터베이스 경로 설정
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serials.db')

# DB_PATH를 확인하기 위한 출력
print("사용하는 DB 경로:", DB_PATH)

def init_database():
    """데이터베이스와 테이블을 초기화하는 함수"""
    try:
        # DB 디렉토리 생성
        db_dir = os.path.dirname(DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        with sqlite3.connect(DB_PATH, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS serial_numbers (
                    serial_number TEXT PRIMARY KEY,
                    creation_date TEXT,
                    expiration_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_blacklisted INTEGER DEFAULT 0,
                    renewal_count INTEGER DEFAULT 0,
                    device_id TEXT,
                    last_renewal_date TEXT
                )
            ''')
            conn.commit()
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류: {e}")

def get_all_serials():
    """데이터베이스에서 모든 시리얼 정보를 가져오는 함수"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT serial_number, creation_date, expiration_date, 
                   is_blacklisted, renewal_count, device_id 
            FROM serial_numbers
            ORDER BY creation_date DESC
        ''')
        records = cursor.fetchall()
        return records
    except Exception as e:
        print(f"시리얼 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def load_serials(tree):
    """시리얼 목록을 새로고침하는 함수"""
    try:
        for item in tree.get_children():
            tree.delete(item)
        serials = get_all_serials()
        for serial in serials:
            sn, creation, expiration, blacklisted, renewal, device_id = serial
            status = "블랙리스트" if blacklisted else ("등록" if device_id else "미등록")
            device_info = device_id if device_id else "미등록"
            tree.insert('', 'end', values=(
                status,
                sn,
                creation,
                expiration,
                renewal,
                device_info
            ))
    except Exception as e:
        print(f"목록 표시 중 오류 발생: {e}")

def create_new_serial(window, tree):
    """새로운 시리얼 넘버를 생성하는 함수"""
    validity_days = simpledialog.askinteger("시리얼 생성", 
                                          "사용 기간(일)을 입력하세요:", 
                                          initialvalue=365, 
                                          minvalue=1)
    if validity_days:
        try:
            serial = generate_serial_number(validity_days)
            creation_date = datetime.now().date()
            expiration_date = creation_date + timedelta(days=validity_days)
            
            # 로컬 DB에 저장
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO serial_numbers 
                (serial_number, creation_date, expiration_date, is_active)
                VALUES (?, ?, ?, 1)
            ''', (serial, str(creation_date), str(expiration_date)))
            conn.commit()
            
            # 서버에 등록
            if sync_with_server(serial, creation_date, expiration_date):
                messagebox.showinfo("성공", f"시리얼 번호가 생성되고 서버에 등록되었습니다.\n시리얼: {serial}")
            else:
                messagebox.showwarning("경고", "시리얼은 생성되었으나 서버 등록에 실패했습니다.")
            
            load_serials(tree)
        except Exception as e:
            messagebox.showerror("오류", f"시리얼 생성 중 오류 발생: {e}")
        finally:
            conn.close()

def blacklist_serial(serial, is_blacklist=True):
    """시리얼 넘버를 블랙리스트에 추가하거나 복원하는 함수"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE serial_numbers SET is_blacklisted = ? WHERE serial_number = ?', 
                       (1 if is_blacklist else 0, serial))
        conn.commit()
        action = "블랙리스트에 추가" if is_blacklist else "블랙리스트에서 복원"
        messagebox.showinfo("성공", f"시리얼 넘버 '{serial}'가 {action}되었습니다.")
    except sqlite3.Error as e:
        messagebox.showerror("오류", f"블랙리스트 처리 중 오류 발생: {e}")
    finally:
        conn.close()

def delete_selected_serial(tree):
    """선택한 시리얼을 삭제하는 함수"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("경고", "삭제할 항목을 선택하세요.")
        return
        
    if messagebox.askyesno("확인", "선택한 시리얼을 삭제하시겠습니까?"):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for item in selected:
                values = tree.item(item)['values']
                serial = values[1]  # 시리얼 번호
                cursor.execute('DELETE FROM serial_numbers WHERE serial_number = ?', (serial,))
            
            conn.commit()
            load_serials(tree)
            messagebox.showinfo("성공", "선택한 시리얼이 삭제되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"삭제 중 오류 발생: {e}")
        finally:
            conn.close()

def copy_selected_serial(tree):
    """선택한 시리얼 번호 복사"""
    selected = tree.selection()
    if selected:
        values = tree.item(selected[0])['values']
        serial = values[1]  # 시리얼 번호 컬럼
        pyperclip.copy(serial)
        messagebox.showinfo("복사 완료", "시리얼 번호가 클립보드에 복사되었습니다.")

def register_device(tree):
    """시리얼에 디바이스 정보를 등록하는 함수"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("경고", "등록할 시리얼을 선택하세요.")
        return
    
    # 디바이스 ID 입력 받기
    device_id = simpledialog.askstring("디바이스 등록", "디바이스 ID를 입력하세요:")
    if not device_id:
        messagebox.showwarning("경고", "디바이스 ID를 입력해야 합니다.")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for item in selected:
            values = tree.item(item)['values']
            serial = values[1]  # 시리얼 번호
            cursor.execute('''
                UPDATE serial_numbers 
                SET device_id = ?
                WHERE serial_number = ?
            ''', (device_id, serial))
        
        conn.commit()
        load_serials(tree)
        messagebox.showinfo("성공", "디바이스가 등록되었습니다.")
    except Exception as e:
        messagebox.showerror("오류", f"디바이스 등록 중 오류 발생: {e}")
    finally:
        conn.close()

def renew_serial(serial, days):
    """시리얼 갱신 함수"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT expiration_date, renewal_count FROM serial_numbers WHERE serial_number = ?', (serial,))
        result = cursor.fetchone()
        if result:
            current_expiration, renewal_count = result
            current_date = datetime.strptime(current_expiration, '%Y-%m-%d').date()
            new_expiration = current_date + timedelta(days=days)
            
            cursor.execute('''
                UPDATE serial_numbers 
                SET expiration_date = ?, 
                    renewal_count = ?,
                    last_renewal_date = ?
                WHERE serial_number = ?
            ''', (str(new_expiration), renewal_count + 1, str(datetime.now().date()), serial))
            
            conn.commit()
            messagebox.showinfo("성공", f"시리얼이 갱신되었습니다.\n새 만료일: {new_expiration}")
            return True
    except Exception as e:
        messagebox.showerror("오류", f"갱신 중 오류 발생: {e}")
        return False
    finally:
        conn.close()

def renew_selected(tree):
    """선택한 시리얼 갱신"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("경고", "갱신할 시리얼을 선택하세요.")
        return
        
    days = simpledialog.askinteger("갱신", "연장할 기간(일)을 입력하세요:", 
                                  initialvalue=30, minvalue=1)
    if days:
        for item in selected:
            values = tree.item(item)['values']
            serial = values[1]  # 시리얼 번호
            if renew_serial(serial, days):
                load_serials(tree)

def copy_selected_rows(tree):
    """선택한 행 전체 복사"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("경고", "복사할 항목을 선택하세요.")
        return
        
    try:
        copied_rows = []
        for item in selected:
            values = tree.item(item)['values']
            row_text = '\t'.join(str(value) for value in values)
            copied_rows.append(row_text)
            
        all_text = '\n'.join(copied_rows)
        pyperclip.copy(all_text)
        messagebox.showinfo("복사 완료", "선택한 항목이 클립보드에 복사되었습니다.")
    except Exception as e:
        messagebox.showerror("오류", f"복사 중 오류 발생: {e}")

def copy_all_rows(tree):
    """모든 행 전체 복사"""
    try:
        all_rows = []
        for item in tree.get_children():
            values = tree.item(item)['values']
            row_text = '\t'.join(str(value) for value in values)
            all_rows.append(row_text)
            
        if all_rows:
            all_text = '\n'.join(all_rows)
            pyperclip.copy(all_text)
            messagebox.showinfo("복사 완료", "모든 항목이 클립보드에 복사되었습니다.")
        else:
            messagebox.showwarning("경고", "복사할 항목이 없습니다.")
    except Exception as e:
        messagebox.showerror("오류", f"복사 중 오류 발생: {e}")

def blacklist_selected(tree):
    """선택한 시리얼 블랙리스트 추가/해제"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("경고", "블랙리스트 처리할 항목을 선택하세요.")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for item in selected:
            values = tree.item(item)['values']
            status = values[0]  # 상태
            serial = values[1]  # 시리얼 번호
            
            is_blacklist = status != "블랙리스트"
            
            cursor.execute('''
                UPDATE serial_numbers 
                SET is_blacklisted = ? 
                WHERE serial_number = ?
            ''', (1 if is_blacklist else 0, serial))
            
        conn.commit()
        load_serials(tree)  # 목록 새로고침
        messagebox.showinfo("성공", "블랙리스트 처리가 완료되었습니다.")
        
    except Exception as e:
        messagebox.showerror("오류", f"블랙리스트 처리 중 오류 발생: {e}")
    finally:
        conn.close()

def copy_selected_serial(tree):
    """선택한 시리얼 번호 복사"""
    selected = tree.selection()
    if selected:
        values = tree.item(selected[0])['values']
        serial = values[1]  # 시리얼 번호 컬럼
        pyperclip.copy(serial)
        messagebox.showinfo("복사 완료", "시리얼 번호가 클립보드에 복사되었습니다.")

# 서버 URL 설정
# Render.com에서 배포한 서버의 실제 URL로 설정하세요
SERVER_URL = "https://your-service.onrender.com"

def sync_with_server(serial_number, creation_date, expiration_date):
    """서버에 시리얼 정보 등록"""
    try:
        data = {
            "serial": serial_number,
            "creation_date": str(creation_date),
            "expiration_date": str(expiration_date)
        }
        print(f"서버에 전송할 데이터: {data}")  # 디버그용
        response = requests.post(f"{SERVER_URL}/register_serial", json=data)
        print(f"서버 응답 코드: {response.status_code}")  # 디버그용
        print(f"서버 응답 내용: {response.text}")  # 디버그용
        return response.status_code == 200
    except Exception as e:
        print(f"서버 연동 중 오류: {e}")
        return False

def fetch_serials_from_server():
    """서버에서 시리얼 상태를 가져와 로컬 DB를 업데이트하는 함수"""
    try:
        response = requests.get(f"{SERVER_URL}/get_serials")
        print(f"서버로부터 시리얼 상태 가져오기 응답 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                serials = data.get("serials", [])
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                for serial in serials:
                    serial_number = serial.get("serial_number")
                    device_id = serial.get("device_id")
                    if device_id:
                        # 시리얼이 사용되었으면 device_id 업데이트
                        cursor.execute('''
                            UPDATE serial_numbers
                            SET device_id = ?
                            WHERE serial_number = ?
                        ''', (device_id, serial_number))
                    else:
                        # 시리얼이 사용되지 않았으면 device_id를 NULL로 설정
                        cursor.execute('''
                            UPDATE serial_numbers
                            SET device_id = NULL
                            WHERE serial_number = ?
                        ''', (serial_number,))
                conn.commit()
                conn.close()
                print("로컬 DB가 서버의 시리얼 상태로 업데이트되었습니다.")
                return True
            else:
                print(f"서버에서 오류 메시지: {data.get('message')}")
        else:
            print("서버 응답이 좋지 않아요.")
    except Exception as e:
        print(f"서버에서 시리얼 상태 가져오기 중 오류 발생: {e}")
    return False

def update_from_server(tree):
    """서버에서 시리얼 상태를 가져와 업데이트하고 목록을 새로고침하는 함수"""
    if fetch_serials_from_server():
        messagebox.showinfo("성공", "서버에서 시리얼 상태를 가져와 업데이트했어요!")
        load_serials(tree)
    else:
        messagebox.showerror("오류", "서버에서 시리얼 상태를 가져오는 데 실패했어요.")

def create_gui():
    window = Tk()
    window.title("시리얼 넘버 관리 도구")
    window.geometry("1200x600")

    # 메인 프레임 생성
    main_frame = ttk.Frame(window)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Treeview 생성
    columns = ('status', 'serial', 'created', 'expired', 'renewal', 'device')
    tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
    
    # 컬럼 설정
    tree.heading('status', text='상태')
    tree.heading('serial', text='시리얼 번호')
    tree.heading('created', text='생성일')
    tree.heading('expired', text='만료일')
    tree.heading('renewal', text='갱신 횟수')
    tree.heading('device', text='디바이스 정보')
    
    # 컬럼 너비 설정
    tree.column('status', width=80, anchor='center')
    tree.column('serial', width=300, anchor='w')
    tree.column('created', width=100, anchor='center')
    tree.column('expired', width=100, anchor='center')
    tree.column('renewal', width=80, anchor='center')
    tree.column('device', width=150, anchor='w')
    
    # 스크롤바
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Treeview와 스크롤바 배치
    tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    def on_click(event):
        """시리얼 번호 컬럼 클릭 시 복사"""
        region = tree.identify("region", event.x, event.y)
        column = tree.identify_column(event.x)
        if region == "cell" and column == "#2":  # 시리얼 번호 컬럼
            item = tree.identify_row(event.y)
            if item:
                tree.selection_set(item)
                copy_selected_serial(tree)

    # 클릭 이벤트 바인딩
    tree.bind('<ButtonRelease-1>', on_click)

    # 우클릭 메뉴
    context_menu = tk.Menu(window, tearoff=0)
    context_menu.add_command(label="시리얼 번호 복사", 
                             command=lambda: copy_selected_serial(tree))
    context_menu.add_command(label="선택 행 복사", 
                             command=lambda: copy_selected_rows(tree))
    context_menu.add_command(label="전체 복사", 
                             command=lambda: copy_all_rows(tree))
    context_menu.add_separator()
    context_menu.add_command(label="선택 항목 삭제", 
                             command=lambda: delete_selected_serial(tree))
    context_menu.add_command(label="블랙리스트 추가/해제", 
                             command=lambda: blacklist_selected(tree))
    context_menu.add_command(label="시리얼 갱신", 
                             command=lambda: renew_selected(tree))

    def show_popup(event):
        item = tree.identify('row', event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)

    # 우클릭 이벤트 바인딩
    tree.bind('<Button-3>', show_popup)

    # 버튼 프레임
    button_frame = ttk.Frame(window)
    button_frame.pack(fill='x', padx=10, pady=5)

    # 버튼들
    ttk.Button(button_frame, text="시리얼 생성", 
               command=lambda: create_new_serial(window, tree)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="선택 항목 삭제", 
               command=lambda: delete_selected_serial(tree)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="블랙리스트 추가/복원", 
               command=lambda: blacklist_selected(tree)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="시리얼 갱신", 
               command=lambda: renew_selected(tree)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="선택 복사", 
               command=lambda: copy_selected_rows(tree)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="전체 복사", 
               command=lambda: copy_all_rows(tree)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="디바이스 등록", 
               command=lambda: register_device(tree)).pack(side='left', padx=5)
    
    # 새로 추가한 "서버에서 업데이트" 버튼
    ttk.Button(button_frame, text="서버에서 업데이트", 
               command=lambda: update_from_server(tree)).pack(side='left', padx=5)

    # 초기 데이터 로드
    load_serials(tree)

    window.mainloop()

if __name__ == "__main__":
    init_database()
    create_gui()
