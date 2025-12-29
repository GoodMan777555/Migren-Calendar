import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time as dt_time
import os
import time

# ==========================================
# 1. НАСТРОЙКИ И КОНСТАНТЫ
# ==========================================
st.set_page_config(page_title="Migraine Diary", page_icon="🧠", layout="wide")

DATA_FILE = "migraine_data.csv"

# Словари для перевода ЗНАЧЕНИЙ (данных внутри ячеек)
VAL_MAP = {
    # Локализация
    "Виски": "רקות", "Затылок": "עורף", "Лоб": "מצח",
    "Правая сторона": "צד ימין", "Левая сторона": "צד שמאל",
    "Вся голова": "כל הראש", "Шея": "צוואר", "Глаза": "עיניים", 
    "Мигрирующая": "נודד",
    # Симптомы
    "Тошнота": "בחילה", "Светобоязнь": "רגישות לאור", "Звукобоязнь": "רגישות לרעש",
    "Аура": "אורה", "Головокружение": "סחרחורת", "Слабость": "חולשה", "Рвота": "הקאה",
    # Триггеры
    "Стресс": "לחץ/סטרס", "Недосып": "חוסר שינה", "Перемена погоды": "מזג אוויר",
    "Алкоголь": "אלכוהול", "Кофеин": "קפאין", "Голод": "רעב",
    "Экран/Монитор": "מסכים", "Запахи": "ריחות", "Пропуск еды": "דילוג על ארוחה",
    "Яркий свет": "אור חזק"
}
# Обратный словарь (Hebrew -> Russian)
REV_VAL_MAP = {v: k for k, v in VAL_MAP.items()}

# Словари интерфейса
LANG = {
    "Russian": {
        "dir": "ltr",
        "cols": ["Дата", "Время", "Интенсивность (1-10)", "Локализация", "Симптомы", "Триггеры", "Лекарства", "Заметки"],
        "ui": {
            "menu_add": "📝 Добавить запись", "menu_stats": "📊 Статистика", "menu_edit": "✏️ Редактор",
            "add_title": "Новая запись", "save_btn": "Сохранить", "success": "Запись сохранена!",
            "stats_title": "Аналитика", "total": "Всего", "avg": "Средняя боль", "last": "Последний раз",
            "c_cal": "Хронология", "c_loc": "Локализация", "c_trig": "Триггеры",
            "edit_title": "Редактор", "edit_help": "Выделите строку слева и нажмите Delete для удаления.",
            "update_btn": "Обновить данные", "empty": "Нет данных", "download": "Скачать Excel"
        },
        "opts": {
            "loc": ["Виски", "Затылок", "Лоб", "Правая сторона", "Левая сторона", "Вся голова", "Шея", "Глаза"],
            "sym": ["Тошнота", "Светобоязнь", "Звукобоязнь", "Аура", "Головокружение", "Слабость", "Рвота"],
            "trig": ["Стресс", "Недосып", "Перемена погоды", "Алкоголь", "Кофеин", "Голод", "Экран/Монитор", "Запахи"]
        }
    },
    "Hebrew": {
        "dir": "rtl",
        "cols": ["תאריך", "שעה", "עוצמה (1-10)", "מיקום", "תסמינים", "טריגרים", "תרופות", "הערות"],
        "ui": {
            "menu_add": "📝 הוספת רשומה", "menu_stats": "📊 סטטיסטיקה", "menu_edit": "✏️ עריכה",
            "add_title": "רשומה חדשה", "save_btn": "שמור רשומה", "success": "נשמר בהצלחה!",
            "stats_title": "ניתוח נתונים", "total": "סה״כ התקפים", "avg": "עוצמה ממוצעת", "last": "התקף אחרון",
            "c_cal": "לוח שנה של הכאב", "c_loc": "מיקום הכאב", "c_trig": "טריגרים נפוצים",
            "edit_title": "ניהול רשומות", "edit_help": "כדי למחוק: סמן שורה משמאל ולחץ Delete במקלדת",
            "update_btn": "עדכן נתונים", "empty": "אין נתונים", "download": "הורד קובץ Excel"
        },
        "opts": {
            # Генерация списка опций на иврите
            "loc": [VAL_MAP.get(x, x) for x in ["Виски", "Затылок", "Лоб", "Правая сторона", "Левая сторона", "Вся голова", "Шея", "Глаза"]],
            "sym": [VAL_MAP.get(x, x) for x in ["Тошнота", "Светобоязнь", "Звукобоязнь", "Аура", "Головокружение", "Слабость", "Рвота"]],
            "trig": [VAL_MAP.get(x, x) for x in ["Стресс", "Недосып", "Перемена погоды", "Алкоголь", "Кофеин", "Голод", "Экран/Монитор", "Запахи"]]
        }
    }
}

# Стандартные (системные) имена колонок для CSV
SYS_COLS = LANG["Russian"]["cols"]

# ==========================================
# 2. РАБОТА С ДАННЫМИ
# ==========================================

def load_data():
    """Загрузка данных + исправление типов"""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=SYS_COLS)
    
    try:
        df = pd.read_csv(DATA_FILE)
        
        # 1. ЛЕЧЕНИЕ ИМЕН КОЛОНОК (если старый файл)
        rename_map = {}
        for col in df.columns:
            if "Интенсивность" in col and col != "Интенсивность (1-10)":
                rename_map[col] = "Интенсивность (1-10)"
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
            df.to_csv(DATA_FILE, index=False)

        # 2. ИСПРАВЛЕНИЕ ТИПОВ ДАННЫХ (Критично для ошибки из скриншота!)
        if not df.empty:
            # Дата в datetime
            df['Дата'] = pd.to_datetime(df['Дата']).dt.date
            
            # Время в time object (исправляет ошибку редактирования)
            # Функция пытается понять формат, даже если там просто текст
            def parse_time(t):
                try:
                    return pd.to_datetime(str(t), format='%H:%M:%S').time()
                except:
                    try:
                        return pd.to_datetime(str(t), format='%H:%M').time()
                    except:
                        return datetime.now().time() # Если время битое, ставим текущее
            
            df['Время'] = df['Время'].apply(parse_time)
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=SYS_COLS)

def save_data(df):
    """Сохранение в CSV"""
    # Конвертируем объекты времени обратно в строки перед сохранением
    df_save = df.copy()
    # Принудительно делаем колонки стандартными (русскими) перед записью
    # Если df пришел с ивритскими заголовками, переименуем обратно по индексу
    if len(df_save.columns) == len(SYS_COLS):
        df_save.columns = SYS_COLS
        
    df_save.to_csv(DATA_FILE, index=False)

# ==========================================
# 3. ИНТЕРФЕЙС
# ==========================================

# Сайдбар
st.sidebar.title("Language / שפה")
lang_key = st.sidebar.selectbox("Select", ["Russian", "Hebrew"], label_visibility="collapsed")
T = LANG[lang_key]

# CSS для RTL
if T["dir"] == "rtl":
    st.markdown("""
    <style>
        .stApp { direction: rtl; text-align: right; }
        section[data-testid="stSidebar"] { direction: rtl; text-align: right; }
        div.stButton > button { float: right; }
        div[data-testid="stMetricValue"] { direction: ltr; text-align: right; }
        p, h1, h2, h3, label, .stMarkdown { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title(T["ui"]["menu_add"] if lang_key=="Russian" else "תפריט")
page = st.sidebar.radio("Nav", [T["ui"]["menu_add"], T["ui"]["menu_stats"], T["ui"]["menu_edit"]], label_visibility="collapsed")

# ------------------------------------------
# СТРАНИЦА: ДОБАВИТЬ
# ------------------------------------------
if page == T["ui"]["menu_add"]:
    st.title(T["ui"]["add_title"])
    
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            date_in = st.date_input(T["cols"][0], datetime.now())
            time_in = st.time_input(T["cols"][1], datetime.now())
            pain_in = st.slider(T["cols"][2], 1, 10, 5)
            loc_in = st.selectbox(T["cols"][3], T["opts"]["loc"])
        with c2:
            sym_in = st.multiselect(T["cols"][4], T["opts"]["sym"])
            trig_in = st.multiselect(T["cols"][5], T["opts"]["trig"])
            meds_in = st.text_input(T["cols"][6])
        
        note_in = st.text_area(T["cols"][7])
        submitted = st.form_submit_button(T["ui"]["save_btn"])

        if submitted:
            # Переводим обратно на русский для базы данных
            loc_db = REV_VAL_MAP.get(loc_in, loc_in)
            sym_db = ", ".join([REV_VAL_MAP.get(x, x) for x in sym_in])
            trig_db = ", ".join([REV_VAL_MAP.get(x, x) for x in trig_in])

            new_entry = {
                SYS_COLS[0]: date_in,
                SYS_COLS[1]: time_in, # сохраняем как объект, pandas сам разберется
                SYS_COLS[2]: pain_in,
                SYS_COLS[3]: loc_db,
                SYS_COLS[4]: sym_db,
                SYS_COLS[5]: trig_db,
                SYS_COLS[6]: meds_in,
                SYS_COLS[7]: note_in
            }
            
            df = load_data()
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            st.balloons()
            st.success(T["ui"]["success"])

# ------------------------------------------
# СТРАНИЦА: СТАТИСТИКА
# ------------------------------------------
elif page == T["ui"]["menu_stats"]:
    st.title(T["ui"]["stats_title"])
    df = load_data()

    if df.empty:
        st.info(T["ui"]["empty"])
    else:
        # Метрики
        c1, c2, c3 = st.columns(3)
        c1.metric(T["ui"]["total"], len(df))
        c2.metric(T["ui"]["avg"], f"{df[SYS_COLS[2]].mean():.1f}")
        c3.metric(T["ui"]["last"], str(df[SYS_COLS[0]].max()))
        st.markdown("---")

        # Перевод данных для отображения (Russian DB -> Hebrew Display)
        df_viz = df.copy()
        if lang_key == "Hebrew":
            df_viz[SYS_COLS[3]] = df_viz[SYS_COLS[3]].replace(VAL_MAP) # Локализация
        
        # Переименование колонок для графиков
        df_viz.columns = T["cols"]

        # График 1: Пузырьки
        st.subheader(T["ui"]["c_cal"])
        fig1 = px.scatter(df_viz, x=T["cols"][0], y=T["cols"][2], 
                          size=T["cols"][2], color=T["cols"][2], color_continuous_scale="Reds")
        st.plotly_chart(fig1, use_container_width=True)

        # График 2 и 3
        gc1, gc2 = st.columns(2)
        with gc1:
            st.subheader(T["ui"]["c_loc"])
            fig2 = px.bar(df_viz, x=T["cols"][3], color=T["cols"][3])
            st.plotly_chart(fig2, use_container_width=True)
        
        with gc2:
            st.subheader(T["ui"]["c_trig"])
            # Сложная обработка триггеров (split -> translate -> count)
            # Берем из ОРИГИНАЛЬНОГО df (русского), разбиваем, потом переводим
            raw_trigs = df[SYS_COLS[5]].str.split(', ', expand=True).stack()
            if not raw_trigs.empty:
                if lang_key == "Hebrew":
                    raw_trigs = raw_trigs.map(lambda x: VAL_MAP.get(x, x))
                fig3 = px.pie(names=raw_trigs.values)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.write(T["ui"]["empty"])

# ------------------------------------------
# СТРАНИЦА: РЕДАКТОР (Исправленный)
# ------------------------------------------
elif page == T["ui"]["menu_edit"]:
    st.title(T["ui"]["edit_title"])
    st.info(T["ui"]["edit_help"])
    
    df = load_data()
    
    if df.empty:
        st.warning(T["ui"]["empty"])
    else:
        # 1. Переименовываем колонки для отображения В ТАБЛИЦЕ (чтобы были на Иврите)
        # Мы создаем копию, чтобы редактор показал красивые заголовки
        display_df = df.copy()
        display_df.columns = T["cols"]
        
        # 2. Настройка конфигурации колонок (Column Config)
        # Важно: используем новые (переведенные) имена колонок как ключи
        col_cfg = {
            T["cols"][1]: st.column_config.TimeColumn(format="HH:mm"), # Время
            T["cols"][0]: st.column_config.DateColumn(format="DD.MM.YYYY"), # Дата
            T["cols"][2]: st.column_config.NumberColumn(min_value=1, max_value=10) # Боль
        }

        # 3. Сам редактор
        edited_df = st.data_editor(
            display_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config=col_cfg
        )

        # Кнопка обновления
        if st.button(T["ui"]["update_btn"]):
            # При сохранении нам нужно вернуть русские заголовки!
            # Так как edited_df имеет заголовки на текущем языке (Hebrew),
            # функция save_data сама вернет их к системному виду (SYS_COLS) по порядку.
            save_data(edited_df)
            st.success(T["ui"]["success"])
            time.sleep(1)
            st.rerun()