# manage_serials.py (통합 버전)

import sqlite3
import os
from datetime import datetime, timedelta
from tkinter import Tk, Label, Button, messagebox, Listbox, END, SINGLE, simpledialog, Frame, LEFT
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import requests

# ===== 여기부터 serial_generator.py 내용 통합 =====
import uuid
import hashlib
import datetime as dt

def generate_serial_number(expiration_days=365):
    unique_id = uuid.uuid4().hex[:8].upper()
    creation_date = dt.datetime.now().strftime('%Y%m%d')
    expiration_date = (dt.datetime.now() + dt.timedelta(days=expiration_days)).strftime('%Y%m%d')
    serial_prefix = f"SN-{unique_id}-{creation_date}-{expiration_date}"
    verification_code = hashlib.sha256(serial_prefix.encode()).hexdigest()[:8].upper()
    serial_number = f"{serial_prefix}-{verification_code}"
    return serial_number
# ===== 여기까지 serial_generator.py 내용 통합 =====

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
            status = "블랙리스트" if blacklisted else "활성"
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
    tree.heading('device', text='디이스 정보')
    
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

    def copy_selected_serial(tree):
        """선택한 시리얼 번호 복사"""
        selected = tree.selection()
        if selected:
            values = tree.item(selected[0])['values']
            serial = values[1]  # 시리얼 번호 컬럼
            pyperclip.copy(serial)
            messagebox.showinfo("복사 완료", "시리얼 번호가 클립보드에 복사되었습니다.")

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

    # 초기 데이터 로드
    load_serials(tree)

    window.mainloop()

# 갱신 기능 추가
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

# 서버 URL 설정
SERVER_URL = "https://miniature-memory.onrender.com"

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

if __name__ == "__main__":
    init_database()
    create_gui()
