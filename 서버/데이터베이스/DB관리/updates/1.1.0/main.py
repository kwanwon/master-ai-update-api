import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD # type: ignore
from tkinter import filedialog, simpledialog, messagebox
import ttkbootstrap as ttk  # type: ignore
from ttkbootstrap.constants import *  # type: ignore
from ttkbootstrap.tooltip import ToolTip  # type: ignore
import pygame  # type: ignore
import os
import threading
import time
from datetime import datetime
import json
import platform
import subprocess

from cryptography.fernet import Fernet  # type: ignore # **추가된 임포트**
import sys  # sys 모듈 임포트 (이미 임포트되어 있으면 중복 제거)
from update_manager import check_for_updates, perform_update  # 👈 이 줄 추가
from update_client import UpdateClient  # 상단에 추가

# 시리얼관리 폴더 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
serial_dir = os.path.join(parent_dir, '개발자', '시리얼관리')
sys.path.append(serial_dir)

# 이제 import
from serial_validator import validate_serial # type: ignore

# 세련된 컬러 팔레트 정의
COLORS = {
    'primary': '#2c3e50',    # 진한 남색
    'secondary': '#34495e',  # 회색빛 남색
    'accent': '#3498db',     # 밝은 파랑
    'success': '#2ecc71',    # 초록
    'warning': '#f1c40f',    # 노랑
    'danger': '#e74c3c',     # 빨강
    'background': '#ecf0f1'  # 밝은 회색
}

def get_app_data_path():
    if platform.system() == 'Windows':
        return os.path.join(os.environ['APPDATA'], 'AI사범님')
    else:
        return os.path.join(os.path.expanduser('~'), '.ai사범님')

def resource_path(relative_path):
    """
    리소스 파일의 경로를 반환하는 함수.
    실행 파일과 개발 환경 모두에서 작동하도록 개선.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)

def validate_serial_number(decrypted_serial):
    """
    복호화된 시리얼 넘버를 검증하는 함수.
    """
    try:
        # 복호화된 시리얼 넘버를 문자열로 디코딩
        serial_str = decrypted_serial.decode('utf-8')
        print(f"복호화된 시리얼 넘버: {serial_str}")  # 디버그 출력

        # 시리얼 넘버를 콤마로 구분된 값으로 파싱
        parts = serial_str.split(',')
        print(f"파싱된 시리얼 넘버 부분: {parts}")  # 디버그 출력
        if len(parts) != 3:
            return False, "시리얼 넘버 형식이 올바르지 않습니다.", None

        product_id, user_id, expiry_date_str = parts

        # 만료일 확인
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        print(f"만료일: {expiry_date}")  # 디버그 출력

        # 제품 ID와 사용자 ID 증 (필요에 따라 추 로직 구현)
        if not product_id or not user_id:
            return False, "제품 ID 또는 사용자 ID가 유효하지 않습니다.", None

        return True, "시리얼 넘버가 유효합니다.", expiry_date
    except Exception as e:
        print(f"시리얼 넘버 검증 중 오류 발생: {e}")  # 디버그 출력
        return False, f"시리얼 넘버 검증 중 오류 발생: {e}", None

def check_serial_number(root):
    """이전 버전과의 호환성을 위해 유지"""
    return validate_serial(None, root)

class CommandManagementProgram:
    def __init__(self, root):
        self.root = root
        
        # macOS Dock 아이콘 클릭 이벤트 처리 추가
        if platform.system() == 'Darwin':
            self.root.createcommand('::tk::mac::ReopenApplication', self.root.deiconify)
        
        self.setup_root()

    # ttkbootstrap 스타일 설정
        self.style = ttk.Style("flatly")
    
    # 새로운 버 스타일 정의 (예: Custom.TButton)
        self.style.configure('Custom.TButton', font=('Helvetica', 12, 'bold'))
    
    # 새로운 레이블 스타일 정의 (예: Custom.TLabel)
        self.style.configure('Custom.TLabel', font=('Helvetica', 16, 'bold'))
    
    # 기존 초기화 코드...
        pygame.mixer.init()
        self.is_playing_sessions = {}
        self.paused_sessions = {}
        self.play_threads = {}
        self.channels = {}
        self.sounds = {}

        self.command_files = {}
        self.delay_times = {}
        self.repetitions = {}
        self.clipboard = []
        self.undo_stack = []
        self.context_menus = {}  # 컨텍스트 메뉴 딕셔너리 추가
        self.last_selected_index = {}  # 마지막 선택된 인덱스를 저장하는 딕셔너리 초기화
        self.drag_start_index = None  # 드래그 시작 인덱스 초기화

        self.create_menu()
        self.create_main_ui()  # 메인 UI를 생성
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.schedule_checker()

        # 플랫폼에 따라 Ctrl 또는 Command 키 바인딩 설정
        self.set_key_bindings()

    def set_key_bindings(self):
        # 플랫폼에 따라 단축키 설정
        if platform.system() == 'Darwin':  # macOS
            # Command 키 바인딩
            self.root.bind('<Command-z>', lambda e: self.undo())
            self.root.bind('<Command-c>', lambda e: self.copy_items(self.current_session))
            self.root.bind('<Command-v>', lambda e: self.paste_items(self.current_session))
            self.root.bind('<Command-x>', lambda e: self.cut_items(self.current_session))
            
            # 각 세션별 리스트박스에도 바인딩
            for session in [f"수련{i}" for i in range(1, 7)]:
                self.command_files[session].bind('<Command-z>', lambda e: self.undo())
                self.command_files[session].bind('<Command-c>', lambda e: self.copy_items(session))
                self.command_files[session].bind('<Command-v>', lambda e: self.paste_items(session))
                self.command_files[session].bind('<Command-x>', lambda e: self.cut_items(session))
        else:  # Windows, Linux
            # Control 키 바인딩
            self.root.bind('<Control-z>', lambda e: self.handle_keyboard_event(e, self.undo))
            self.root.bind('<Control-c>', lambda e: self.handle_keyboard_event(e, lambda: self.copy_items(self.current_session)))
            self.root.bind('<Control-v>', lambda e: self.handle_keyboard_event(e, lambda: self.paste_items(self.current_session)))
            self.root.bind('<Control-x>', lambda e: self.handle_keyboard_event(e, lambda: self.cut_items(self.current_session)))
            
            # 각 세션별 리스트박스에도 바인딩
            for session in [f"수련{i}" for i in range(1, 7)]:
                listbox = self.command_files[session]
                listbox.bind('<Control-z>', lambda e, s=session: self.handle_keyboard_event(e, self.undo))
                listbox.bind('<Control-c>', lambda e, s=session: self.handle_keyboard_event(e, lambda: self.copy_items(s)))
                listbox.bind('<Control-v>', lambda e, s=session: self.handle_keyboard_event(e, lambda: self.paste_items(s)))
                listbox.bind('<Control-x>', lambda e, s=session: self.handle_keyboard_event(e, lambda: self.cut_items(s)))

    def handle_keyboard_event(self, event, callback):
        event.widget.after(1, callback)  # 약간의 지연을 주어 기본 동작과 충돌 방지
        return "break"  # 이벤트의 기본 동작을 중단

    def setup_root(self):
        self.root.title("명령 관리 프로그램")
        self.style = ttk.Style("flatly")
        self.root.geometry("1400x1000")  # 화면 크기 조정
        self.root.configure(bg=self.style.colors.bg)
        self.current_session = None  # 현재 작업 중인 세션

    def create_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="새 프로젝트", command=self.new_project)
        filemenu.add_command(label="불러오기", command=self.load_schedule)  # load_schedule 메서드 추가
        filemenu.add_command(label="저장", command=self.save_schedule)      # save_schedule 메서드 추가
        filemenu.add_separator()
        filemenu.add_command(label="닫기", command=self.on_closing)
        menubar.add_cascade(label="파일", menu=filemenu)
        self.root.config(menu=menubar)

    def on_closing(self):
        if messagebox.askokcancel("종료", "정말로 프로그램을 종료하시겠습니까?"):
            self.root.destroy()

    def new_project(self):
        for i in range(1, 7):
            session = f"수련{i}"
            self.command_files[session].delete(0, tk.END)
            self.delay_times[session] = []
            self.repetitions[session] = []
            self.command_files[f"{session}_paths"] = []  # 'session_paths' 초기화 추가
            self.update_total_time(session)
        for i in range(1, 9):
            self.schedule[i]['start'].set('')
            self.schedule[i]['end'].set('')
            self.schedule[i]['checked'].set(False)
            self.schedule[i]['session'].set("수련1")
        messagebox.showinfo("새 프로젝트", "새 프로젝트가 시작되었습니다.")

    def create_main_ui(self):
        # 메인 프레임 생성
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)

        # 전체를 감싸는 캔버스 생성  
        self.main_canvas = tk.Canvas(main_frame)
        self.main_canvas.grid(row=0, column=0, sticky='nsew')

        # 스크롤바 생성
        self.v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.main_canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')

        self.h_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=self.main_canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky='ew', columnspan=2)

        self.main_canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # 그리드 설정
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # 캔버스 내부에 프레임 생성
        self.canvas_frame = ttk.Frame(self.main_canvas)
        self.canvas_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")
            )
        )
        self.main_canvas.create_window((0, 0), window=self.canvas_frame, anchor='nw')

        notebook = ttk.Notebook(self.canvas_frame)  # 탭 생성
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # 그룹1 탭 생성 (수련1~3)
        group1_tab = ttk.Frame(notebook)
        notebook.add(group1_tab, text="그룹1")
        self.create_group_ui(group1_tab, ["수련1", "수련2", "수련3"])

        # 그룹2 탭 생성 (수련4~6)
        group2_tab = ttk.Frame(notebook)
        notebook.add(group2_tab, text="그룹2")
        self.create_group_ui(group2_tab, ["수련4", "수련5", "수련6"])

        # 수련 시간 설정 탭
        schedule_tab = ttk.Frame(notebook)
        notebook.add(schedule_tab, text="수 시간 설정")
        self.create_training_schedule_interface(schedule_tab)

        # 캔버스 스크롤 바인딩
        self.main_canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas_frame.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas_frame.bind('<Leave>', self._unbound_to_mousewheel)

    def on_canvas_configure(self, event):
        self.main_canvas.itemconfig("all", width=event.width)

    def _bound_to_mousewheel(self, event):
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.main_canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.main_canvas.unbind_all("<MouseWheel>")
        self.main_canvas.unbind_all("<Shift-MouseWheel>")

    def _on_mousewheel(self, event):
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shift_mousewheel(self, event):
        self.main_canvas.xview_scroll(int(-1*(event.delta/120)), "units")

    def create_group_ui(self, parent, session_names):
        session_frame = ttk.Frame(parent)
        session_frame.pack(expand=True, fill='both')

        for idx, session in enumerate(session_names):
            frame = ttk.Frame(session_frame)
            frame.grid(row=0, column=idx, padx=5)
            self.create_command_ui(frame, session)

    def create_command_ui(self, parent, session):
        main_frame = ttk.Frame(parent)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(side=tk.TOP, fill='x')

        label_frame = ttk.Frame(top_frame)
        label_frame.pack(side=tk.LEFT)

        self.command_files[f"{session}_label"] = ttk.Label(
             label_frame, 
             text=f"{session} - 총시간: 00분 00초", 
             style='Custom.TLabel'  # 커스텀 스타일 적용
)
        self.command_files[f"{session}_label"].pack(side=tk.TOP, padx=5)

        # 리스트박스와 버튼을 담을 프레임 생성
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(expand=True, fill='both', pady=10)

        # 리스트박스 생성
        self.command_files[session] = tk.Listbox(
            content_frame,
            font=("Pretendard", 11),
            selectmode=tk.MULTIPLE,
            width=40,
            height=55,
            bg="#ffffff",
            fg="#2c3e50",
            selectbackground="#3498db",
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            borderwidth=1
        )
        self.command_files[session].pack(side=tk.LEFT, fill='y')
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.command_files[session].yview)
        scrollbar.pack(side=tk.LEFT, fill='y')
        self.command_files[session].config(yscrollcommand=scrollbar.set)
        # **드래그 앤 드롭 설정 추가**
        self.command_files[session].drop_target_register(DND_FILES)
        self.command_files[session].dnd_bind('<<Drop>>', lambda e, s=session: self.handle_drop(e, s))
        
        # 버튼 프레임 생성
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(side=tk.LEFT, padx=10)

        # 버튼들 생성 및 같은 크기로 설정
        button_width = 12  # 버튼의 너비를 12로 설정 (필요에 따라 조정)

        play_button = ttk.Button(
            button_frame, 
            text="재생",
            command=lambda s=session: self.start_play_thread(s),
            style="Custom.Success.TButton", 
            width=button_width
        )
        play_button.pack(side=tk.TOP, pady=2)
        ToolTip(play_button, text="선택한 파일을 재생합니다.")

        pause_button = ttk.Button(button_frame, text="일시정지", command=lambda s=session: self.pause_playback(s), bootstyle="warning-outline", width=button_width)
        pause_button.pack(side=tk.TOP, pady=2)
        ToolTip(pause_button, text="재생을 일시정지하거나 다시 시작합니다.")

        stop_button = ttk.Button(button_frame, text="정지", command=lambda s=session: self.stop_playback_on_click(s), bootstyle="danger-outline", width=button_width)
        stop_button.pack(side=tk.TOP, pady=2)
        ToolTip(stop_button, text="재생을 완전히 중지합니다.")

        add_button = ttk.Button(button_frame, text="열기", command=lambda s=session: self.add_mp3_file(s), bootstyle="info-outline", width=button_width)
        add_button.pack(side=tk.TOP, pady=2)
        ToolTip(add_button, text="MP3 파일을 추가합니다.")

        repeat_button = ttk.Button(button_frame, text="반복재생", command=lambda s=session: self.repeat_playback(s), bootstyle="primary-outline", width=button_width)
        repeat_button.pack(side=tk.TOP, pady=2)
        ToolTip(repeat_button, text="선택한 파일을 반복 재생합니다.")

        select_remove_button = ttk.Button(button_frame, text="선택 제거", command=lambda s=session: self.remove_selected_mp3_files(s), bootstyle="danger-outline", width=button_width)
        select_remove_button.pack(side=tk.TOP, pady=2)
        ToolTip(select_remove_button, text="선택한 파을 삭제합니다.")

        select_all_button = ttk.Button(button_frame, text="전체 선택", command=lambda s=session: self.select_all_files(s), bootstyle="secondary-outline", width=button_width)
        select_all_button.pack(side=tk.TOP, pady=2)
        ToolTip(select_all_button, text="모든 파일을 선택합니다.")

        deselect_all_button = ttk.Button(button_frame, text="선택 해제", command=lambda s=session: self.deselect_all_files(s), bootstyle="secondary-outline", width=button_width)
        deselect_all_button.pack(side=tk.TOP, pady=2)
        ToolTip(deselect_all_button, text="선택을 해제합니다.")

        # 드래그 앤 드롭으로 파일 추가 기능
        self.command_files[session].drop_target_register(DND_FILES)
        self.command_files[session].dnd_bind('<<Drop>>', lambda e, s=session: self.handle_drop(e, s))

        self.command_files[session].bind("<Double-Button-1>", lambda event, s=session: self.modify_delay_time(s))
        self.command_files[session].bind("<Control-c>", lambda event, s=session: self.copy_items(s))
        self.command_files[session].bind("<Control-x>", lambda event, s=session: self.cut_items(s))
        self.command_files[session].bind("<Control-v>", lambda event, s=session: self.paste_items(s))

        # 마우스 클릭 및 드래그 이벤트 바인딩 수정
        self.command_files[session].bind("<ButtonPress-1>", lambda event, s=session: self.on_item_press(event, s))
        self.command_files[session].bind("<B1-Motion>", lambda event, s=session: self.on_item_motion(event, s))
        self.command_files[session].bind("<ButtonRelease-1>", lambda event, s=session: self.on_item_release(event, s))
        self.command_files[session].bind("<Shift-ButtonPress-1>", lambda event, s=session: self.shift_click_select(event, s))

        # 마우스 우클릭 컨텍스트 메뉴 바인딩
        self.command_files[session].bind("<Button-3>", lambda event, s=session: self.show_context_menu(event, s))
        # macOS의 경우 마우스 우클릭 이벤트가 <Button-2>일 수 있음
        self.command_files[session].bind("<Button-2>", lambda event, s=session: self.show_context_menu(event, s))

        self.create_context_menu(session)  # 컨텍스트 메뉴 생성

        self.delay_times[session] = []
        self.repetitions[session] = []
        self.command_files[f"{session}_paths"] = []  # 'session_paths' 초기화 추가

    def handle_drop(self, event, session):
        mp3_files = self.root.tk.splitlist(event.data)
        for mp3_file in mp3_files:
            file_name = os.path.splitext(os.path.basename(mp3_file))[0]
            delay_time = 0
            self.command_files[session].insert(tk.END, f"{file_name} ({delay_time}초)")

            self.command_files[f"{session}_paths"].append(mp3_file)
            self.delay_times[session].append(delay_time)
            self.repetitions[session].append(1)

        self.update_total_time(session)

    def on_item_press(self, event, session):
        widget = event.widget
        self.drag_start_index = widget.nearest(event.y)
        self.last_selected_index[session] = self.drag_start_index
        if event.state & 0x0001:  # Shift 키가 눌린 상태
            self.shift_click_select(event, session)
        else:
            # 드래그를 위한 데이터 초기화
            self.drag_data = {'session': session}
        # 기본 선택 동작을 허용하기 위해 아무 작업도 하지 않음

    def on_item_motion(self, event, session):
        if not hasattr(self, 'drag_start_index') or self.drag_start_index is None:
            return
        widget = event.widget
        drag_end_index = widget.nearest(event.y)
        if drag_end_index != self.drag_start_index:
            # 아이템을 새로운 위치로 이동
            self.move_item(widget, self.drag_start_index, drag_end_index, session)
            self.drag_start_index = drag_end_index

    def on_item_release(self, event, session):
        # 드래그 데이터 초기화
        self.drag_start_index = None
        self.update_total_time(session)

    def move_item(self, widget, from_index, to_index, session):
        selected_indices = widget.curselection()
        if not selected_indices:
            return
        
        # 선택된 모든 항목의 데이터 저장
        items_to_move = []
        for idx in selected_indices:
            items_to_move.append({
                'item': widget.get(idx),
                'path': self.command_files[f"{session}_paths"][idx],
                'delay': self.delay_times[session][idx],
                'repeat': self.repetitions[session][idx]
            })
        
        # 선택된 항목들 삭제
        for idx in reversed(selected_indices):
            widget.delete(idx)
            del self.command_files[f"{session}_paths"][idx]
            del self.delay_times[session][idx]
            del self.repetitions[session][idx]
        
        # 새 위치에 항목들 삽입
        for i, item_data in enumerate(items_to_move):
            insert_pos = to_index + i
            widget.insert(insert_pos, item_data['item'])
            self.command_files[f"{session}_paths"].insert(insert_pos, item_data['path'])
            self.delay_times[session].insert(insert_pos, item_data['delay'])
            self.repetitions[session].insert(insert_pos, item_data['repeat'])
            
        # 이동된 항목들 선택
        widget.selection_clear(0, tk.END)
        for i in range(len(items_to_move)):
            widget.selection_set(to_index + i)

    def select_all_files(self, session):
        self.command_files[session].select_set(0, tk.END)

    def deselect_all_files(self, session):
        self.command_files[session].select_clear(0, tk.END)

    def create_training_schedule_interface(self, parent):
        schedule_frame = ttk.Frame(parent, width=250)  # 폭을 줄임
        schedule_frame.pack(side=tk.TOP, padx=10, pady=10, fill='both')

        self.schedule = {}

        header_labels = ["사용", "시작 시간 (HH:MM)", "종료 시간 (HH:MM)", "수련 세션"]
        for idx, text in enumerate(header_labels):
            label = ttk.Label(schedule_frame, text=text, style='Custom.TLabel' )
            label.grid(row=0, column=idx, padx=5, pady=5)

        for i in range(1, 21):  # Changed from 9 to 21 to create 20 rows
            check_var = tk.BooleanVar()
            start_var = tk.StringVar()
            end_var = tk.StringVar()
            session_var = tk.StringVar(value="수련1")

            self.schedule[i] = {
                'checked': check_var,
                'start': start_var,
                'end': end_var,
                'session': session_var
            }

            checkbox = ttk.Checkbutton(schedule_frame, variable=check_var)
            checkbox.grid(row=i, column=0, padx=5, pady=5)

            start_time_entry = ttk.Entry(schedule_frame, textvariable=start_var, width=10, font=("Helvetica", 13))
            start_time_entry.grid(row=i, column=1, padx=5, pady=5)

            end_time_entry = ttk.Entry(schedule_frame, textvariable=end_var, width=10, font=("Helvetica", 13))
            end_time_entry.grid(row=i, column=2, padx=5, pady=5)

            session_menu = ttk.Combobox(schedule_frame, textvariable=session_var, values=["수련1", "수련2", "수련3", "수련4", "수련5", "수련6"], width=8, state="readonly", font=("Helvetica", 13))
            session_menu.grid(row=i, column=3, padx=5, pady=5)

        save_button = ttk.Button(schedule_frame, text="설정 저장", command=self.save_schedule, style='Custom.TButton')
        save_button.grid(row=21, column=0, columnspan=4, pady=10)  # Moved to row 21 since we now have 20 rows

    def schedule_checker(self):
        now = datetime.now().time()
        for i, config in self.schedule.items():
            if config['checked'].get() and config['start'].get() and config['end'].get():
                try:
                    start_time_str = config['start'].get()
                    end_time_str = config['end'].get()
                    start_time = datetime.strptime(start_time_str, "%H:%M").time()
                    end_time = datetime.strptime(end_time_str, "%H:%M").time()
                except ValueError:
                    continue

                session = config['session'].get()

                if start_time <= now < end_time and not self.is_playing_sessions.get(session):
                    self.start_play_thread(session)

                if now >= end_time and self.is_playing_sessions.get(session):
                    # 체크박스 자동 해제
                    config['checked'].set(False)
                    # 재생 중지
                    self.stop_playback_on_click(session)

        self.root.after(1000, self.schedule_checker)

    def start_play_thread(self, session, repeat_count=1, selected_indices=None):
        if self.is_playing_sessions.get(session):
            return

        if selected_indices is None:
            selected_indices = self.command_files[session].curselection()
            if not selected_indices:
                selected_indices = range(self.command_files[session].size())

        self.is_playing_sessions[session] = True
        self.paused_sessions[session] = False

        self.channels[session] = pygame.mixer.Channel(len(self.channels))
        self.sounds[session] = []

        play_thread = threading.Thread(target=self.play_command, args=(session, selected_indices, repeat_count))
        play_thread.start()
        self.play_threads[session] = play_thread

    def play_command(self, session, selected_indices, repeat_count=1):
        listbox = self.command_files[session]
        commands = listbox.get(0, tk.END)

        for _ in range(repeat_count):
            for i in selected_indices:
                while self.paused_sessions.get(session):
                    if not self.is_playing_sessions.get(session):
                        break
                    time.sleep(0.1)

                if not self.is_playing_sessions.get(session):
                    break

                command = commands[i]
                file_name = command.split(' (')[0]
                try:
                    mp3_file = self.command_files[f"{session}_paths"][i]
                except IndexError:
                    print(f"Error: MP3 파일 경로가 없습니다 for {file_name}.")
                    continue
                delay_time = self.delay_times[session][i]

                listbox.itemconfig(i, {'bg': '#3498db', 'fg': 'white'})
                listbox.see(i)

                try:
                    sound = pygame.mixer.Sound(mp3_file)
                    self.sounds[session].append(sound)
                    self.channels[session].play(sound)
                    while self.channels[session].get_busy():
                        if not self.is_playing_sessions.get(session):
                            self.channels[session].stop()
                            break
                        if self.paused_sessions.get(session):
                            self.channels[session].pause()
                            while self.paused_sessions.get(session):
                                if not self.is_playing_sessions.get(session):
                                    break
                                time.sleep(0.1)
                            self.channels[session].unpause()
                        pygame.time.Clock().tick(10)
                    if not self.is_playing_sessions.get(session):
                        break
                    time.sleep(delay_time)
                except pygame.error as e:
                    print(f"Error: Unable to play file {file_name}. {e}")
                finally:
                    listbox.itemconfig(i, {'bg': 'white', 'fg': 'black'})

                if not self.is_playing_sessions.get(session):
                    break

        self.is_playing_sessions[session] = False
        self.paused_sessions[session] = False
        self.play_threads.pop(session, None)
        self.channels.pop(session, None)
        self.sounds.pop(session, None)

    def stop_playback_on_click(self, session):
        if self.is_playing_sessions.get(session):
            self.is_playing_sessions[session] = False
            self.paused_sessions[session] = False
            if session in self.channels:
                self.channels[session].stop()

            listbox = self.command_files[session]
            for i in range(listbox.size()):
                listbox.itemconfig(i, {'bg': 'white', 'fg': 'black'})

    def pause_playback(self, session):
        if self.is_playing_sessions.get(session):
            self.paused_sessions[session] = not self.paused_sessions[session]
            if self.paused_sessions[session]:
                if session in self.channels:
                    self.channels[session].pause()
            else:
                if session in self.channels:
                    self.channels[session].unpause()

    def create_context_menu(self, session):
        # 컨텍스트 메뉴 생성
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="재생", command=lambda s=session: self.start_play_thread(s))
        menu.add_command(label="일시정지", command=lambda s=session: self.pause_playback(s))
        menu.add_command(label="정지", command=lambda s=session: self.stop_playback_on_click(s))
        menu.add_separator()
        menu.add_command(label="열기", command=lambda s=session: self.add_mp3_file(s))
        menu.add_command(label="반복재생", command=lambda s=session: self.repeat_playback(s))
        menu.add_separator()
        menu.add_command(label="선택 제거", command=lambda s=session: self.remove_selected_mp3_files(s))
        menu.add_command(label="전체 선택", command=lambda s=session: self.select_all_files(s))
        menu.add_command(label="선택 해제", command=lambda s=session: self.deselect_all_files(s))
        menu.add_separator()
        menu.add_command(label="잘라내기", command=lambda s=session: self.cut_items(s))
        menu.add_command(label="복사", command=lambda s=session: self.copy_items(s))
        menu.add_command(label="붙여넣기", command=lambda s=session: self.paste_items(s))
        menu.add_separator()
        menu.add_command(label="딜레이 시간 수정", command=lambda s=session: self.modify_delay_time(s))
        self.context_menus[session] = menu

    def show_context_menu(self, event, session):
        # 컨텍스트 메뉴 표시
        menu = self.context_menus.get(session)
        if menu:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def add_mp3_file(self, session):
        mp3_files = filedialog.askopenfilenames(title="MP3 파일 선택", filetypes=(("MP3 파일", "*.mp3"), ("모든 파일", "*.*")))
        if mp3_files:
            listbox = self.command_files[session]
            for mp3_file in mp3_files:
                file_name = os.path.splitext(os.path.basename(mp3_file))[0]
                delay_time = 0
                listbox.insert(tk.END, f"{file_name} ({delay_time}초)")

                self.command_files[f"{session}_paths"].append(mp3_file)
                self.delay_times[session].append(delay_time)
                self.repetitions[session].append(1)

            self.update_total_time(session)

    def remove_selected_mp3_files(self, session):
        listbox = self.command_files[session]
        selected_indices = listbox.curselection()
        selected_indices = list(selected_indices)
        selected_indices.reverse()

        removed_items = []
        for index in selected_indices:
            try:
                removed_items.append((
                    listbox.get(index),
                    self.command_files[f"{session}_paths"][index],
                    self.delay_times[session][index],
                    self.repetitions[session][index]
                ))
            except IndexError:
                continue  # 경로가 없을 경우 무시
            listbox.delete(index)
            del self.command_files[f"{session}_paths"][index]
            del self.delay_times[session][index]
            del self.repetitions[session][index]

        self.undo_stack.append(('remove', session, selected_indices, removed_items))
        self.update_total_time(session)

    def copy_items(self, session):
        if session is None:
            return
        selected_indices = self.command_files[session].curselection()
        if selected_indices:
            self.clipboard = [(self.command_files[session].get(i), self.command_files[f"{session}_paths"][i],
                               self.delay_times[session][i], self.repetitions[session][i]) for i in selected_indices]
            self.undo_stack.append(('copy', session, list(selected_indices), list(self.clipboard)))
            self.current_session = session  # 현재 세션 설정

    def cut_items(self, session):
        if session is None:
            return
        selected_indices = self.command_files[session].curselection()
        if selected_indices:
            self.copy_items(session)
            self.remove_selected_mp3_files(session)
            self.undo_stack.append(('cut', session, list(selected_indices)))
            self.current_session = session  # 현재 세션 설정

    def paste_items(self, session):
        if session is None:
            return
        if self.clipboard:
            try:
                active_index = self.command_files[session].index(tk.ACTIVE)
            except tk.TclError:
                active_index = tk.END
            for idx, item in enumerate(self.clipboard):
                command, path, delay_time, repetition = item
                listbox = self.command_files[session]
                if active_index == tk.END:
                    insert_index = tk.END
                else:
                    insert_index = active_index + 1 + idx
                listbox.insert(insert_index, command)
                self.command_files[f"{session}_paths"].insert(insert_index, path)
                self.delay_times[session].insert(insert_index, delay_time)
                self.repetitions[session].insert(insert_index, repetition)

            self.undo_stack.append(('paste', session, list(self.clipboard), active_index))
            self.update_total_time(session)
            self.current_session = session  # 현재 세션 설정

    def undo(self, event=None):
        if self.undo_stack:
            last_action = self.undo_stack.pop()
            action_type = last_action[0]

            if action_type == 'copy':
                pass  # 복사 동작은 undo할 필요 없음

            elif action_type == 'cut':
                session, indices = last_action[1], last_action[2]
                for idx, item in zip(indices, reversed(self.clipboard)):
                    command, path, delay_time, repetition = item
                    self.command_files[session].insert(idx, command)
                    self.command_files[f"{session}_paths"].insert(idx, path)
                    self.delay_times[session].insert(idx, delay_time)
                    self.repetitions[session].insert(idx, repetition)

                self.update_total_time(session)

            elif action_type == 'paste':
                session, clipboard, active_index = last_action[1], last_action[2], last_action[3]
                for idx, _ in enumerate(clipboard):
                    del_idx = active_index + 1 + idx
                    try:
                        self.command_files[session].delete(del_idx)
                        del self.command_files[f"{session}_paths"][del_idx]
                        del self.delay_times[session][del_idx]
                        del self.repetitions[session][del_idx]
                    except IndexError:
                        continue  # 삭제할 인덱스가 없을 경우 무시

                self.update_total_time(session)

            elif action_type == 'remove':
                session, indices, items = last_action[1], last_action[2], last_action[3]
                for idx, item in zip(indices, reversed(items)):
                    command, path, delay_time, repetition = item
                    self.command_files[session].insert(idx, command)
                    self.command_files[f"{session}_paths"].insert(idx, path)
                    self.delay_times[session].insert(idx, delay_time)
                    self.repetitions[session].insert(idx, repetition)

                self.update_total_time(session)

    def modify_delay_time(self, session):
        listbox = self.command_files[session]
        selected_indices = listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            command = listbox.get(index)
            try:
                # 수정된 부분: '초'를 제거하고 숫자만 추출
                delay_time_str = command.split('(')[1].split('초')[0].strip()
                current_delay = int(delay_time_str)
                
                delay_time = simpledialog.askinteger(
                    "딜레이 시간 수정", 
                    "딜레이 시간을 초 단위로 입력하세요 (0 ~ 1800초):",
                    initialvalue=current_delay, 
                    minvalue=0, 
                    maxvalue=1800
                )
                
                if delay_time is not None:
                    file_name = command.split(' (')[0]
                    listbox.delete(index)
                    listbox.insert(index, f"{file_name} ({delay_time}초)")
                    old_delay_time = self.delay_times[session][index]
                    self.delay_times[session][index] = delay_time

                    self.undo_stack.append(('modify_delay', session, index, old_delay_time))
                    self.update_total_time(session)
                    
            except (IndexError, ValueError) as e:
                print(f"딜레이 시간 수정 중 오류 발생: {e}")  # 디버깅용
                messagebox.showerror("입력 오류", "유효한 숫자를 입력하세요.")
                return

    def repeat_playback(self, session):
        selected_indices = self.command_files[session].curselection()

        if not selected_indices:
            selected_indices = range(self.command_files[session].size())

        repeat_count = simpledialog.askinteger(
            "반복 재생 횟수", "몇 번 반복하시겠습니까?", initialvalue=1, minvalue=1, maxvalue=100
        )
        if repeat_count:
            self.start_play_thread(session, repeat_count, selected_indices)

    def update_total_time(self, session):
        total_time = 0
        paths = self.command_files.get(f"{session}_paths", [])
        for i in range(len(paths)):
            try:
                sound = pygame.mixer.Sound(paths[i])
                sound_length = sound.get_length()
            except pygame.error:
                sound_length = 0
            total_time += (sound_length * self.repetitions[session][i]) + self.delay_times[session][i]

        minutes, seconds = divmod(int(total_time), 60)
        total_time_str = f"{minutes:02d}분 {seconds:02d}초"
        self.command_files[f"{session}_label"].config(text=f"{session} - 총시간: {total_time_str}")

    def load_schedule(self):
        """
        저장된 JSON 파일에서 스케줄을 불러오는 메서드입니다.
        """
        # 파일 열기 대화상자 열기
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
            title="스케줄 불러오기"
        )
        if not file_path:
            return  # 사용자가 취소를 누른 우

        # JSON 파일에서 데이터 로드
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("불러오기 실", f"스케줄 불러오기 중 오류가 발생했습니다:\n{e}")
            return

        # 스케줄 데이터 적용
        schedule_data = data.get('schedules', {})
        for i, config in schedule_data.items():
            try:
                i = int(i)
                if i < 1 or i > 8:
                    continue  # 유효하지 않은 인덱스는 무시
                self.schedule[i]['checked'].set(config.get('checked', False))
                self.schedule[i]['start'].set(config.get('start', ''))
                self.schedule[i]['end'].set(config.get('end', ''))
                session = config.get('session', '수련1')
                if session not in [f"수련{n}" for n in range(1,7)]:
                    session = "수련1"  # 유효하지 않은 세션은 기본값으로 설정
                self.schedule[i]['session'].set(session)
            except ValueError:
                continue  # 인덱스 변환 실패 시 무시

        # Commands 데이터 적용
        commands_data = data.get('commands', {})
        for session, cmd in commands_data.items():
            if session not in [f"수련{n}" for n in range(1,7)]:
                continue  # 유효하지 않은 세션은 무시

            paths = cmd.get('paths', [])
            delay_times = cmd.get('delay_times', [])
            repetitions = cmd.get('repetitions', [])

            # 리스트박스 초기화
            listbox = self.command_files.get(session)
            if listbox:
                listbox.delete(0, tk.END)
                self.command_files[session + '_paths'] = paths.copy()
                self.delay_times[session] = delay_times.copy()
                self.repetitions[session] = repetitions.copy()

                # 리스트박스에 MP3 파일 추가
                for path, delay, rep in zip(paths, delay_times, repetitions):
                    file_name = os.path.splitext(os.path.basename(path))[0]
                    listbox.insert(tk.END, f"{file_name} ({delay}초)")

        self.update_all_total_times()
        messagebox.showinfo("불러오기 완료", f"스케줄이 성공적로 불러와졌습니다:\n{file_path}")

    def save_schedule(self):
        try:
            print("설정 저장 버튼 클릭됨")  # 디버깅용
            # 기존 save_schedule 로직...
            # 예시:
            # 스케줄 데이터를 수집하고 저장하는 로직
            schedule_data = {}
            for i in range(1, 9):
                config = self.schedule[i]
                schedule_data[i] = {
                    'checked': config['checked'].get(),
                    'start': config['start'].get(),
                    'end': config['end'].get(),
                    'session': config['session'].get()
                }

            # Commands 데이터 수집
            commands_data = {}
            for session in [f"수련{n}" for n in range(1,7)]:
                paths = self.command_files.get(session + '_paths', [])
                delay_times = self.delay_times.get(session, [])
                repetitions = self.repetitions.get(session, [])
                commands_data[session] = {
                    'paths': paths,
                    'delay_times': delay_times,
                    'repetitions': repetitions
                }

            # 전체 데이터 저장
            data = {
                'schedules': schedule_data,
                'commands': commands_data
            }

            # 파일 저장 대화상자 열기
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
                title="스케줄 저장"
            )
            if not file_path:
                return  # 사용자가 취소를 른 경우

            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("저장 완료", f"스케줄이 성공적으로 저장되었습니다:\n{file_path}")
        except Exception as e:
            print(f"save_schedule 에서 오류 발생: {e}")
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다:\n{e}")

    def update_all_total_times(self):
        """
        모든 세션의 총 시간을 업데이트하는 메서드입니다.
        """
        for session in [f"수련{n}" for n in range(1,7)]:
            self.update_total_time(session)

    # **기존 메서드들**
    def shift_click_select(self, event, session):
        widget = event.widget
        current_selection = widget.nearest(event.y)
        
        if not hasattr(self, 'last_selected_index'):
            self.last_selected_index = {}
        
        if session not in self.last_selected_index:
            self.last_selected_index[session] = current_selection
            return
        
        # 구간의 시작과 끝 결정
        start = min(self.last_selected_index[session], current_selection)
        end = max(self.last_selected_index[session], current_selection)
        
        # 구간 선택
        for i in range(start, end + 1):
            widget.selection_set(i)

    def create_context_menu(self, session):
        # 컨텍스트 메뉴 생성
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="재생", command=lambda s=session: self.start_play_thread(s))
        menu.add_command(label="일시정지", command=lambda s=session: self.pause_playback(s))
        menu.add_command(label="정지", command=lambda s=session: self.stop_playback_on_click(s))
        menu.add_separator()
        menu.add_command(label="열기", command=lambda s=session: self.add_mp3_file(s))
        menu.add_command(label="반복재생", command=lambda s=session: self.repeat_playback(s))
        menu.add_separator()
        menu.add_command(label="선택 제거", command=lambda s=session: self.remove_selected_mp3_files(s))
        menu.add_command(label="전체 선택", command=lambda s=session: self.select_all_files(s))
        menu.add_command(label="선택 해제", command=lambda s=session: self.deselect_all_files(s))
        menu.add_separator()
        menu.add_command(label="잘라내기", command=lambda s=session: self.cut_items(s))
        menu.add_command(label="복사", command=lambda s=session: self.copy_items(s))
        menu.add_command(label="붙여넣기", command=lambda s=session: self.paste_items(s))
        menu.add_separator()
        menu.add_command(label="딜레이 시간 수정", command=lambda s=session: self.modify_delay_time(s))
        self.context_menus[session] = menu

    def show_context_menu(self, event, session):
        # 컨텍스트 메뉴 표시
        menu = self.context_menus.get(session)
        if menu:
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    # 추가적인 메서드들 필    시 여기에 추가

if __name__ == "__main__":
    try:
        # 업데이트 상태 파일 경로
        update_flag_file = os.path.join(os.path.dirname(__file__), '.update_completed')
        
        # 이전 업데이트 플래그 파일이 있다면 삭제
        if os.path.exists(update_flag_file):
            os.remove(update_flag_file)
            # 프로그램 실행으로 바로 진행
        else:
            root = TkinterDnD.Tk()
            
            # 1. 시리얼 검증
            if not validate_serial(None, root):
                root.destroy()
                sys.exit(1)
            
            # 2. 업데이트 확인
            update_available = check_for_updates()
            if update_available:
                if messagebox.askyesno("업데이트 확인", "새로운 업데이트가 있습니다. 업데이트하시겠습니까?"):
                    if perform_update():
                        # 업데이트 완료 플래그 파일 생성
                        with open(update_flag_file, 'w') as f:
                            f.write('1')
                        
                        messagebox.showinfo("업데이트 완료", "업데이트가 완료되었습니다. 프로그램을 재시작니다.")
                        root.destroy()
                        
                        # 현재 스크립트 재실행
                        current_script = os.path.abspath(sys.argv[0])
                        subprocess.Popen([sys.executable, current_script])
                        sys.exit(0)
                    else:
                        messagebox.showerror("오류", "업데이트 중 오류가 발생했습니다.")
            
        # 3. 프로그램 실행
        if not 'root' in locals():
            root = TkinterDnD.Tk()
        app = CommandManagementProgram(root)
        root.mainloop()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        # 오류 발생 시 콘솔 창이 바로 닫히지 않도록
        input("Enter 키를 누르면 프로그램이 종료됩니다...")
        if 'root' in locals() and root.winfo_exists():
            root.destroy()
        sys.exit(1)