import streamlit as st
import sqlite3
import hashlib # 비밀번호 해싱을 위해 추가
from datetime import date # 날짜 입력을 위해 추가

# --- 데이터베이스 초기화 함수 ---
def init_db():
    conn = sqlite3.connect('database.db') # database.db 파일 사용
    c = conn.cursor()

    # users 테이블 생성 (비밀번호는 해싱된 형태로 저장)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- 해싱된 비밀번호 저장
            email TEXT,
            gender TEXT,
            birthday TEXT,
            age INTEGER
        )
    ''')

    # routines 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            routine_name TEXT NOT NULL,
            days_of_week TEXT, -- 예: "월,수,금" 또는 "매일" (콤마로 구분)
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # exercises 테이블 생성 (루틴에 포함된 개별 운동)
    c.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            sets INTEGER,
            reps_or_duration TEXT, -- 횟수(예: "10-12회") 또는 시간(예: "30분")
            FOREIGN KEY (routine_id) REFERENCES routines(id) ON DELETE CASCADE
        )
    ''')

    # exercise_logs 테이블 생성 (실제 운동 기록)
    c.execute('''
        CREATE TABLE IF NOT EXISTS exercise_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            log_date TEXT NOT NULL, -- YYYY-MM-DD 형식
            actual_sets INTEGER,
            actual_reps_or_duration TEXT,
            completed BOOLEAN, -- 운동 완료 여부 (0: False, 1: True)
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# --- 비밀번호 해싱 함수 ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- DB 초기화 실행 (앱 시작 시 한 번만) ---
init_db()

# --- Streamlit 앱 시작 ---
st.set_page_config(layout="centered", page_title="나만의 운동 루틴 관리 앱")
st.title("💪 나만의 운동 루틴 관리 앱")
st.markdown("---")

# 세션 상태 초기화 (로그인 여부, 현재 사용자 ID 등을 저장)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user_id = None
    st.session_state.current_username = None

# --- 사이드바 메뉴 ---
if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("메뉴", ["로그인", "회원가입"])
else:
    st.sidebar.write(f"환영합니다, **{st.session_state.current_username}**님!")
    menu = st.sidebar.selectbox("메뉴", ["내 루틴", "운동 기록", "로그아웃"])

# --- 로그인/회원가입/로그아웃 처리 ---
if menu == "로그인" and not st.session_state.logged_in:
    st.header("로그인")
    username = st.text_input("아이디", key="login_username")
    password = st.text_input("비밀번호", type='password', key="login_password")
    login_button = st.button("로그인")

    if login_button:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and hash_password(password) == user[2]: # 해싱된 비밀번호 비교
            st.session_state.logged_in = True
            st.session_state.current_user_id = user[0]
            st.session_state.current_username = user[1]
            st.success(f"{username}님 환영합니다! 페이지가 새로고침됩니다.")
            st.balloons()
            st.rerun()
        else:
            st.error("로그인 실패: 아이디 또는 비밀번호가 올바르지 않습니다.")

elif menu == "회원가입" and not st.session_state.logged_in:
    st.header("회원가입")
    with st.form("signup_form", clear_on_submit=True):
        new_username = st.text_input("아이디 (필수):")
        new_password = st.text_input("비밀번호 (필수):", type='password')
        new_password_chk = st.text_input("비밀번호 확인 (필수):", type='password')
        new_email = st.text_input("이메일 (선택):")
        new_gender = st.selectbox("성별 (선택):", ["선택 안함", "남성", "여성", "기타"])
        new_birthday = st.date_input("생일 (선택):", value=date(2000, 1, 1))
        new_age = st.number_input("나이 (선택):", min_value=0, max_value=120, step=1, value=20)
        join_button = st.form_submit_button("회원가입")

        if join_button:
            if not new_username or not new_password:
                st.error("아이디와 비밀번호는 필수 입력 사항입니다.")
            elif new_password != new_password_chk:
                st.error("비밀번호 확인이 일치하지 않습니다.")
            else:
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                try:
                    hashed_password = hash_password(new_password)
                    c.execute("INSERT INTO users(username, password, email, gender, birthday, age) VALUES (?, ?, ?, ?, ?, ?)",
                              (new_username, hashed_password, new_email, new_gender, str(new_birthday), new_age))
                    conn.commit()
                    st.success("회원가입이 완료되었습니다! 이제 로그인해 주세요.")
                except sqlite3.IntegrityError:
                    st.error("이미 존재하는 아이디입니다. 다른 아이디를 사용해 주세요.")
                except Exception as e:
                    st.error(f"회원가입 중 오류가 발생했습니다: {e}")
                finally:
                    conn.close()

elif menu == "로그아웃" and st.session_state.logged_in:
    st.session_state.logged_in = False
    st.session_state.current_user_id = None
    st.session_state.current_username = None
    st.success("로그아웃 되었습니다. 페이지가 새로고침됩니다.")
    st.rerun()

# --- 로그인 후 기능 ---
if st.session_state.logged_in:
    user_id = st.session_state.current_user_id

    if menu == "내 루틴":
        st.header("내 운동 루틴")

        # --- 이미지 추가 및 크기 조절 부분 ---
        try:
            # 'exercise_background.jpg' 파일을 app.py와 같은 폴더에 넣어주세요.
            # width 매개변수를 사용하여 이미지 너비를 픽셀 단위로 조절할 수 있습니다.
            # use_column_width=False로 설정하여 width 값을 존중합니다.
            st.image("poirier.jpg", caption="당신의 건강한 습관을 응원합니다!", width=400, use_column_width=False)
        except FileNotFoundError:
            st.warning("`poirier.jpg` 이미지를 찾을 수 없습니다. 파일을 `app.py`와 같은 폴더에 넣어주세요.")
        # --- 이미지 추가 및 크기 조절 부분 끝 ---

        st.markdown("---") # 이미지와 다음 섹션 구분

        # 루틴 추가 폼
        st.subheader("새 루틴 추가 ➕")
        with st.form("add_routine_form", clear_on_submit=True):
            routine_name = st.text_input("루틴 이름:", key="new_routine_name")
            days_options = ["월", "화", "수", "목", "금", "토", "일", "매일"]
            selected_days = st.multiselect("운동 요일:", options=days_options, key="new_routine_days")
            add_routine_button = st.form_submit_button("루틴 추가")

            if add_routine_button:
                if routine_name and selected_days:
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO routines (user_id, routine_name, days_of_week) VALUES (?, ?, ?)",
                              (user_id, routine_name, ",".join(selected_days)))
                    conn.commit()
                    conn.close()
                    st.success(f"'{routine_name}' 루틴이 추가되었습니다.")
                    st.rerun()
                else:
                    st.warning("루틴 이름과 운동 요일을 입력해주세요.")

        st.markdown("---")

        # 기존 루틴 목록 표시 및 관리
        st.subheader("나의 루틴 목록 📋")
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, routine_name, days_of_week FROM routines WHERE user_id = ?", (user_id,))
        my_routines = c.fetchall()
        conn.close()

        if not my_routines:
            st.info("아직 등록된 루틴이 없습니다. 위에 있는 '새 루틴 추가' 기능을 활용해 보세요!")
        else:
            for r_id, r_name, r_days in my_routines:
                with st.expander(f"**{r_name}** ({r_days})"):
                    # 루틴 수정
                    st.markdown("##### 루틴 정보 수정")
                    edited_routine_name = st.text_input("루틴 이름 수정:", value=r_name, key=f"edit_r_name_{r_id}")
                    # default 값 설정 시 r_days가 None이거나 빈 문자열일 경우 [] 처리
                    default_days = r_days.split(',') if r_days else []
                    edited_days = st.multiselect("운동 요일 수정:", options=days_options, default=default_days, key=f"edit_r_days_{r_id}")
                    update_routine_button = st.button(f"'{r_name}' 루틴 업데이트", key=f"update_r_{r_id}")

                    if update_routine_button:
                        conn = sqlite3.connect('database.db')
                        c = conn.cursor()
                        c.execute("UPDATE routines SET routine_name = ?, days_of_week = ? WHERE id = ?",
                                  (edited_routine_name, ",".join(edited_days), r_id))
                        conn.commit()
                        conn.close()
                        st.success(f"'{r_name}' 루틴이 업데이트되었습니다.")
                        st.rerun()

                    st.markdown("---")

                    # 이 루틴에 운동 추가
                    st.markdown(f"##### '{r_name}'에 운동 추가 ➕")
                    with st.form(f"add_exercise_form_{r_id}", clear_on_submit=True):
                        exercise_name = st.text_input("운동 종목 (예: 푸쉬업):", key=f"ex_name_{r_id}")
                        sets = st.number_input("세트 수:", min_value=1, step=1, value=3, key=f"ex_sets_{r_id}")
                        reps_or_duration = st.text_input("횟수 또는 시간 (예: 10-12회 / 30분):", key=f"ex_reps_{r_id}")
                        add_exercise_button = st.form_submit_button("운동 추가")

                        if add_exercise_button:
                            if exercise_name:
                                conn = sqlite3.connect('database.db')
                                c = conn.cursor()
                                c.execute("INSERT INTO exercises (routine_id, exercise_name, sets, reps_or_duration) VALUES (?, ?, ?, ?)",
                                          (r_id, exercise_name, sets, reps_or_duration))
                                conn.commit()
                                conn.close()
                                st.success(f"'{exercise_name}' 운동이 '{r_name}' 루틴에 추가되었습니다.")
                                st.rerun()
                            else:
                                st.warning("운동 종목을 입력해주세요.")

                    st.markdown("---")

                    # 이 루틴의 운동 목록 표시 및 삭제
                    st.markdown(f"##### '{r_name}'의 운동 목록")
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("SELECT id, exercise_name, sets, reps_or_duration FROM exercises WHERE routine_id = ?", (r_id,))
                    exercises_in_routine = c.fetchall()
                    conn.close()

                    if not exercises_in_routine:
                        st.info("이 루틴에 등록된 운동이 없습니다.")
                    else:
                        for e_id, e_name, e_sets, e_reps in exercises_in_routine:
                            col1, col2 = st.columns([0.8, 0.2])
                            with col1:
                                st.write(f"- **{e_name}** ({e_sets}세트, {e_reps})")
                            with col2:
                                delete_exercise_button = st.button("삭제", key=f"del_ex_{e_id}", help="이 운동을 루틴에서 삭제합니다.")
                                if delete_exercise_button:
                                    conn = sqlite3.connect('database.db')
                                    c = conn.cursor()
                                    c.execute("DELETE FROM exercise_logs WHERE exercise_id = ?", (e_id,)) # 관련 로그도 삭제
                                    c.execute("DELETE FROM exercises WHERE id = ?", (e_id,))
                                    conn.commit()
                                    conn.close()
                                    st.success(f"'{e_name}' 운동이 삭제되었습니다.")
                                    st.rerun()
                    st.markdown("---")
                    # 루틴 삭제
                    st.markdown("##### 루틴 삭제")
                    delete_routine_button = st.button(f"'{r_name}' 루틴 삭제 (🚨)", key=f"delete_r_{r_id}", help="이 루틴과 포함된 모든 운동, 그리고 관련 운동 기록이 삭제됩니다.")
                    if delete_routine_button:
                        # 삭제 확인 메시지
                        st.warning(f"정말로 '{r_name}' 루틴과 관련된 모든 데이터를 삭제하시겠습니까? (되돌릴 수 없음)")
                        if st.button(f"✅ 예, '{r_name}' 루틴을 삭제합니다.", key=f"confirm_delete_r_{r_id}"):
                            conn = sqlite3.connect('database.db')
                            c = conn.cursor()
                            # CASCADE 옵션으로 인해 routines 삭제 시 related exercises와 exercise_logs도 삭제됨
                            c.execute("DELETE FROM routines WHERE id = ?", (r_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"'{r_name}' 루틴이 삭제되었습니다.")
                            st.rerun()


    elif menu == "운동 기록":
        st.header("운동 기록 📝")

        # 운동 기록 입력 폼
        st.subheader("오늘의 운동 기록 남기기")
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # 사용자의 모든 루틴의 운동을 가져옴
        c.execute("""
            SELECT r.routine_name, e.exercise_name, e.id
            FROM routines r
            JOIN exercises e ON r.id = e.routine_id
            WHERE r.user_id = ?
            ORDER BY r.routine_name, e.exercise_name
        """, (user_id,))
        all_exercises_for_log = c.fetchall()
        conn.close()

        if not all_exercises_for_log:
            st.info("루틴과 운동을 먼저 등록해야 운동 기록을 남길 수 있습니다. '내 루틴' 메뉴에서 추가해주세요.")
        else:
            exercise_options = [f"[{ex[0]}] {ex[1]}" for ex in all_exercises_for_log]
            selected_exercise_str = st.selectbox("운동 선택:", options=exercise_options, key="log_select_exercise")

            if selected_exercise_str:
                # 선택된 운동의 ID 찾기
                selected_exercise_id = None
                for ex in all_exercises_for_log:
                    if f"[{ex[0]}] {ex[1]}" == selected_exercise_str:
                        selected_exercise_id = ex[2]
                        break

                if selected_exercise_id:
                    log_date = st.date_input("운동 날짜:", value=date.today(), key="log_date_input")
                    actual_sets = st.number_input("실제 수행 세트 수:", min_value=1, step=1, value=3, key="log_sets_input")
                    actual_reps_or_duration = st.text_input("실제 수행 횟수 또는 시간:", key="log_reps_input", help="예: 10회, 12-10-8회, 30분")
                    completed = st.checkbox("완료했습니까?", key="log_completed_checkbox")

                    record_button = st.button("기록 추가")

                    if record_button:
                        conn = sqlite3.connect('database.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO exercise_logs (user_id, exercise_id, log_date, actual_sets, actual_reps_or_duration, completed) VALUES (?, ?, ?, ?, ?, ?)",
                                  (user_id, selected_exercise_id, str(log_date), actual_sets, actual_reps_or_duration, completed))
                        conn.commit()
                        conn.close()
                        st.success(f"'{selected_exercise_str}' 운동 기록이 추가되었습니다.")
                        st.rerun()
                else:
                    st.error("운동을 선택하는 데 오류가 발생했습니다. 다시 시도해 주세요.")

        st.markdown("---")

        # 운동 기록 조회
        st.subheader("내 운동 기록 보기 📖")
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # join을 통해 루틴 이름과 운동 종목을 함께 가져옴
        c.execute("""
            SELECT el.log_date, r.routine_name, e.exercise_name, el.actual_sets, el.actual_reps_or_duration, el.completed, el.id
            FROM exercise_logs el
            JOIN exercises e ON el.exercise_id = e.id
            JOIN routines r ON e.routine_id = r.id
            WHERE el.user_id = ?
            ORDER BY el.log_date DESC, r.routine_name, e.exercise_name
        """, (user_id,))
        all_logs = c.fetchall()
        conn.close()

        if not all_logs:
            st.info("아직 등록된 운동 기록이 없습니다.")
        else:
            for log_date, routine_name, exercise_name, sets, reps, completed, log_id in all_logs:
                status = "✅ 완료" if completed else "❌ 미완료"
                # HTML과 CSS를 사용하여 기록을 더 보기 좋게 표시
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    **날짜:** {log_date} <br>
                    **루틴:** {routine_name} <br>
                    **운동:** {exercise_name} <br>
                    **수행:** {sets}세트, {reps} <br>
                    **상태:** {status}
                    <div style="text-align: right; margin-top: 5px;">
                        {st.button("기록 삭제", key=f"del_log_{log_id}", help="이 운동 기록을 삭제합니다.")}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 삭제 버튼 클릭 시 처리
                if st.session_state.get(f"del_log_{log_id}"): # 버튼 클릭 여부 확인
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM exercise_logs WHERE id = ?", (log_id,))
                    conn.commit()
                    conn.close()
                    st.success("운동 기록이 삭제되었습니다.")
                    st.rerun()