# manage_serials.py

import sqlite3
from datetime import datetime, timedelta
from tkinter import Tk, Label, Button, messagebox, Listbox, END, SINGLE, simpledialog, Frame, LEFT
import uuid
from serial_generator import generate_serial_number

def init_database():
    """데이터베이스와 테이블을 초기화하는 함수"""
    conn = sqlite3.connect('serials.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS serial_numbers (
        serial_number TEXT PRIMARY KEY,
        creation_date TEXT,
        expiration_date TEXT,
        user_id TEXT,
        is_active INTEGER DEFAULT 1,
        is_blacklisted INTEGER DEFAULT 0,
        renewal_count INTEGER DEFAULT 0,
        device_id TEXT,
        last_renewal_date TEXT
    )
    ''')
    conn.commit()
    conn.close()

def get_all_serials():
    """데이터베이스에서 모든 시리얼 정보를 가져오는 함수"""
    try:
        conn = sqlite3.connect('serials.db')
        cursor = conn.cursor()
        
        # 디버깅을 위한 출력
        print("데이터베이스 연결 성공")
        
        cursor.execute('''
            SELECT serial_number, creation_date, expiration_date, 
                   is_blacklisted, renewal_count, device_id 
            FROM serial_numbers
            ORDER BY creation_date DESC
        ''')
        
        records = cursor.fetchall()
        print(f"가져온 시리얼 수: {len(records)}")
        
        return records
    except Exception as e:
        print(f"시리얼 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def load_serials(listbox):
    """시리얼 목록을 새로고침하는 함수"""
    try:
        listbox.delete(0, END)
        serials = get_all_serials()
        print(f"표시할 시리얼 수: {len(serials)}")
        
        for serial in serials:
            sn, creation, expiration, blacklisted, renewal, device_id = serial
            status = "[블랙리스트]" if blacklisted else "[활성]"
            device_info = f"디바이스 ID: {device_id}" if device_id else "디바이스 미등록"
            listbox.insert(END, f"{status} 시리얼: {sn} | 생성일: {creation} | 만료일: {expiration} | 갱신 횟수: {renewal} | {device_info}")
    except Exception as e:
        print(f"목록 표시 중 오류 발생: {e}")

def create_new_serial(window, listbox):
    """새로운 시리얼 넘버를 생성하는 함수"""
    user_id = simpledialog.askstring("시리얼 생성", "사용자 ID를 입력하세요:")
    if user_id:
        validity_days = simpledialog.askinteger("시리얼 생성", "유효 기간(일)을 입력하세요:", initialvalue=365, minvalue=1)
        if validity_days:
            try:
                serial = generate_serial_number(validity_days)
                creation_date = datetime.now().date()
                expiration_date = creation_date + timedelta(days=validity_days)
                
                conn = sqlite3.connect('serials.db')
                cursor = conn.cursor()
                
                print(f"저장할 데이터: {serial}, {creation_date}, {expiration_date}, {user_id}")
                
                cursor.execute('''
                    INSERT INTO serial_numbers 
                    (serial_number, creation_date, expiration_date, user_id, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (serial, str(creation_date), str(expiration_date), user_id))
                
                conn.commit()
                print("데이터베이스 저장 성공")
                
                messagebox.showinfo("성공", f"시리얼 넘버가 생성되었습니다.\n시리얼: {serial}\n만료일: {expiration_date}")
                load_serials(listbox)
            except Exception as e:
                print(f"오류 발: {e}")
                messagebox.showerror("오류", f"시리얼 생성 중 오류 발생: {e}")
            finally:
                conn.close()

def blacklist_serial(serial, is_blacklist=True):
    """시리얼 넘버를 블랙리스트에 추가하거나 복원하는 함수"""
    conn = sqlite3.connect('serials.db')
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

def create_gui():
    window = Tk()
    window.title("시리얼 넘버 관리 도구")
    window.geometry("800x600")

    # 시리얼 넘버 리스트
    listbox = Listbox(window, selectmode=SINGLE, width=120, height=30)
    listbox.pack(pady=10)
    
    # 초기 목록 로드
    load_serials(listbox)

    # 버튼 프레임 생성 (가로 배치)
    button_frame = Frame(window)
    button_frame.pack(pady=5)

    # 시리얼 생성 버튼
    btn_create = Button(button_frame, text="시리얼 생성", 
                       command=lambda: create_new_serial(window, listbox), width=20)
    btn_create.pack(side=LEFT, padx=5)

    # 블랙리스트 추가/복원 버튼
    def blacklist_selected():
        selected = listbox.curselection()
        if selected:
            serial_info = listbox.get(selected)
            serial = serial_info.split(" | ")[0].split(": ")[1]
            is_blacklisted = "[블랙리스트]" in serial_info
            action = "복원" if is_blacklisted else "블랙리스트에 추가"
            confirm = messagebox.askyesno("확인", 
                f"시리얼 넘버 '{serial}'를 {action}하시겠습니까?")
            if confirm:
                blacklist_serial(serial, not is_blacklisted)
                load_serials(listbox)
        else:
            messagebox.showerror("오류", "시리얼 넘버를 선택하세요.")

    btn_blacklist = Button(button_frame, text="블랙리스트 추가/복원", 
                          command=blacklist_selected, width=20)
    btn_blacklist.pack(side=LEFT, padx=5)

    # 시리얼 갱신 버튼
    def renew_selected():
        selected = listbox.curselection()
        if selected:
            serial_info = listbox.get(selected)
            serial = serial_info.split(" | ")[0].split(": ")[1]
            days = simpledialog.askinteger("갱신", "추가할 일 수를 입력하세요 (기본값 30):", minvalue=1)
            if days is None:
                days = 30
            renew_serial(serial, days) # type: ignore
            load_serials(listbox)
        else:
            messagebox.showerror("오류", "갱신할 시리얼 넘버를 선택하세요.")

    btn_renew = Button(button_frame, text="시리얼 갱신", 
                      command=renew_selected, width=20)
    btn_renew.pack(side=LEFT, padx=5)

    # 시리얼 재발급 버튼
    def reissue_selected():
        """시리얼 재발급 버튼 클릭 시 실행되는 함수"""
        selected = listbox.curselection()
        if selected:
            serial_info = listbox.get(selected)
            print(f"선택된 시리얼 정보: {serial_info}")  # 디버깅 메시지
            
            # [활성] 또는 [블랙리스트] 태그 제거
            if "[활성]" in serial_info:
                serial = serial_info.split("[활성] 시리얼: ")[1].split(" | ")[0]
            elif "[블랙리스트]" in serial_info:
                serial = serial_info.split("[블랙리스트] 시리얼: ")[1].split(" | ")[0]
            else:
                serial = serial_info.split("시리얼: ")[1].split(" | ")[0]
            
            print(f"추출된 시리얼 번호: {serial}")  # 디버깅 메시지
            
            user_id = simpledialog.askstring("재발급", 
                f"시리얼 넘버 '{serial}'에 대한 새로운 사용자 ID를 입력하세요 (선택 사항):")
            print(f"입력된 새 사용자 ID: {user_id}")  # 디버깅 메시지
            
            confirm = messagebox.askyesno("확인", 
                f"시리얼 넘버 '{serial}'를 재발급하시겠습니까?")
            if confirm:
                print("재발급 진행")  # 디버깅 메시지
                reissue_serial(serial, user_id)
                load_serials(listbox)
                print("재발급 완료")  # 디버깅 메시지
        else:
            messagebox.showerror("오류", "재발급할 시리얼 넘버를 선택하세요.")

    btn_reissue = Button(button_frame, text="시리얼 재발급", 
                        command=reissue_selected, width=20)
    btn_reissue.pack(side=LEFT, padx=5)

    window.mainloop()

def reissue_serial(serial, new_user_id=None):
    """시리얼 넘버를 재발급하는 함수"""
    conn = sqlite3.connect('serials.db')
    cursor = conn.cursor()
    try:
        # 기존 시리얼 정보 가져오기
        cursor.execute('''
            SELECT user_id, expiration_date 
            FROM serial_numbers 
            WHERE serial_number = ?
        ''', (serial,))
        result = cursor.fetchone()
        
        if result:
            old_user_id, expiration_date = result
            # 새 사용자 ID가 없으면 기존 ID 사용
            user_id = new_user_id if new_user_id else old_user_id
            
            # 디바이스 ID 초기화 및 사용자 ID 업데이트
            cursor.execute('''
                UPDATE serial_numbers 
                SET device_id = NULL, 
                    user_id = ?,
                    is_active = 1
                WHERE serial_number = ?
            ''', (user_id, serial))
            
            conn.commit()
            messagebox.showinfo("성공", f"시리얼 넘버가 재발급되었습니다.\n시리얼: {serial}")
        else:
            messagebox.showerror("오류", "시리얼 넘버를 찾을 수 없습니다.")
    except sqlite3.Error as e:
        messagebox.showerror("오류", f"재발급 중 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()  # 데이터베이스 초기화 추가
    create_gui()