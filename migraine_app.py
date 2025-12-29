import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import time

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================
st.set_page_config(page_title="Migraine Diary", page_icon="🧠", layout="wide")

DATA_FILE = "migraine_data.csv"

# ==========================================
# 2. СЛОВАРИ И ПЕРЕВОД
# ==========================================
VAL_MAP = {
    "Виски": "רקות", "Затылок": "עורף", "Лоб": "מצח",
    "Правая сторона": "צד ימין", "Левая сторона": "צד שמאל",
    "Вся голова": "כל הראש", "Шея": "צוואר", "Глаза": "עיניים", "Мигрирующая": "נודד",
    "Тошнота": "בחילה", "Светобоязнь": "רגישות לאור", "Звукобоязнь": "רגישות לרעש",
    "Аура": "אורה", "Головокружение": "סחרחורת", "Слабость": "חולשה", "Рвота": "הקאה",
    "Стресс": "לחץ/סטרס", "Недосып": "חוסר שינה", "Перемена погоды": "מזג אוויר",
    "Алкоголь": "אלכוהול", "Кофеин": "קפאין", "Голод": "רעב",
    "Экран/Монитор": "מסכים", "Запахи": "ריחות", "Пропуск еды": "דילוג על ארוחה",
    "Яркий свет": "אור חזק"
}
REV_VAL_MAP = {v: k for k, v in VAL_MAP.items()}

LANG = {
    "Russian": {
        "dir": "ltr",
        "cols": ["Дата", "Время", "Интенсивность (1-10)", "Локализация", "Симптомы", "Триггеры", "Лекарства", "Заметки"],
        "ui": {
            "menu_add": "📝 Добавить запись", "menu_stats": "📊 Статистика", "menu_edit": "✏️ Редактор",
            "add_title": "Новая запись", "save_btn": "Сохранить", "success": "Запись сохранена!",
            "stats_title": "Аналитика", "total": "Всего", "avg": "Средняя боль", "last": "Последний раз",
            "c_cal": "Хронология", "c_loc": "Локализация", "c_trig": "Триггеры",
            "edit_title": "Редактор", "edit_help": "Для удаления выделите строку слева и нажмите Delete.",
            "update_btn": "Обновить данные", "empty": "Нет данных"
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
            "edit_title": "ניהול רשומות", "edit_help": "למחיקה: סמן שורה משמאל ולחץ Delete במקלדת",
            "update_btn": "עדכן נתונים", "empty": "אין נתונים"
        },
        "opts": {
            "loc": [VAL_MAP.get(x, x) for x in ["Виски", "Затылок", "Лоб", "Правая сторона", "Левая сторона", "Вся голова", "Шея", "Глаза"]],
            "sym": [VAL_MAP.get(x, x) for x in ["Тошнота", "Светобоязнь", "Звукобоязнь", "Аура", "Головокружение", "Слабость", "Рвота"]],
            "trig": [VAL_MAP.get(x, x) for x in ["Стресс", "Недосып", "Перемена погоды", "Алкоголь", "Кофеин", "Голод", "Экран/Монитор", "Запахи"]]
        }
    }
}

SYS_COLS = LANG["Russian"]["cols"]

# ==========================================
# 3. ФУНКЦИИ ДАННЫХ
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=SYS_COLS)
    try:
        df = pd.read_csv(DATA_FILE)
        # Fix columns
        rename_map = {}
        for col in df.columns:
            if "Интенсивность" in col and col != "Интенсивность (1-10)":
                rename_map[col] = "Интенсивность (1-10)"
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
            df.to_csv(DATA_FILE, index=False)
        
        # Fix types
        if not df.empty:
            df['Дата'] = pd.to_datetime(df['Дата']).dt.date
            def parse_time(t):
                try:
                    return pd.to_datetime(str(t), format='%H:%M:%S').time()
                except:
                    try:
                        return pd.to_datetime(str(t), format='%H:%M').time()
                    except:
                        return datetime.now().time()
            df['Время'] = df['Время'].apply(parse_time)
        return df
    except:
        return pd.DataFrame(columns=SYS_COLS)

def save_data(df):
    df_save = df.copy()
    if len(df_save.columns) == len(SYS_COLS):
        df_save.columns = SYS_COLS
    df_save.to_csv(DATA_FILE, index=False)

# ==========================================
# 4. ИНТЕРФЕЙС И CSS (ИСПРАВЛЕНИЕ)
# ==========================================

# Языковая панель
st.sidebar.title("Language / שפה")
lang_key = st.sidebar.selectbox("Select", ["Russian", "Hebrew"], label_visibility="collapsed")
T = LANG[lang_key]

# --- ГЛАВНОЕ ИСПРАВЛЕНИЕ ---
# Мы не меняем глобальный direction, чтобы не ломать меню.
# Мы меняем только выравнивание текста (text-align) и внутренних элементов.
if T["dir"] == "rtl":
    st.markdown("""
    <style>
        /* Выравниваем заголовки и текст */
        h1, h2, h3, p, label, .stMarkdown {
            text-align: right !important;
        }
        
        /* Выравниваем содержимое инпутов */
        .stTextInput input, .stTextArea textarea, .stNumberInput input {
            text-align: right !important;
            direction: rtl;
        }
        
        /* Выравниваем выпадающие списки */
        div[data-baseweb="select"] {
            direction: rtl;
        }
        
        /* Выравниваем мультиселекты */
        .stMultiSelect {
            direction: rtl;
        }
        
        /* Выравниваем кнопки (сдвигаем вправо) */
        div.stButton {
            display: flex;
            flex-direction: row-reverse;
        }
        
        /* Метрики */
        div[data-testid="stMetricValue"] {
            text-align: right;
        }
        
        /* Боковая панель: текст справа, но само меню работает стандартно */
        section[data-testid="stSidebar"] {
            text-align: right;
        }
        
        /* Исправление для radio buttons в сайдбаре */
        .stRadio div[role="radiogroup"] {
            align-items: flex-end;
        }
    </style>
    """, unsafe_allow_html=True)

# Навигация
st.sidebar.title(T["ui"]["menu_add"] if lang_key=="Russian" else "תפריט")
page = st.sidebar.radio("Nav", [T["ui"]["menu_add"], T["ui"]["menu_stats"], T["ui"]["menu_edit"]], label_visibility="collapsed")

# ==========================================
# СТРАНИЦА: ДОБАВИТЬ
# ==========================================
if page == T["ui"]["menu_add"]:
    st.title(T["ui"]["add_title"])
    
    with st.form("add_form", clear_on_submit=True):
        # Меняем порядок колонок визуально для иврита
        if lang_key == "Hebrew":
            c2, c1 = st.columns(2)
        else:
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
            # Save Logic
            loc_db = REV_VAL_MAP.get(loc_in, loc_in)
            sym_db = ", ".join([REV_VAL_MAP.get(x, x) for x in sym_in])
            trig_db = ", ".join([REV_VAL_MAP.get(x, x) for x in trig_in])

            new_entry = {
                SYS_COLS[0]: date_in,
                SYS_COLS[1]: time_in,
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

# ==========================================
# СТРАНИЦА: СТАТИСТИКА
# ==========================================
elif page == T["ui"]["menu_stats"]:
    st.title(T["ui"]["stats_title"])
    df = load_data()

    if df.empty:
        st.info(T["ui"]["empty"])
    else:
        # Metrics
        m1, m2, m3 = st.columns(3)
        # Если иврит, отобразим метрики справа налево визуально
        if lang_key == "Hebrew":
             m3.metric(T["ui"]["total"], len(df))
             m2.metric(T["ui"]["avg"], f"{df[SYS_COLS[2]].mean():.1f}")
             m1.metric(T["ui"]["last"], str(df[SYS_COLS[0]].max()))
        else:
             m1.metric(T["ui"]["total"], len(df))
             m2.metric(T["ui"]["avg"], f"{df[SYS_COLS[2]].mean():.1f}")
             m3.metric(T["ui"]["last"], str(df[SYS_COLS[0]].max()))
             
        st.markdown("---")

        df_viz = df.copy()
        if lang_key == "Hebrew":
            df_viz[SYS_COLS[3]] = df_viz[SYS_COLS[3]].replace(VAL_MAP)
        
        df_viz.columns = T["cols"]

        st.subheader(T["ui"]["c_cal"])
        fig1 = px.scatter(df_viz, x=T["cols"][0], y=T["cols"][2], 
                          size=T["cols"][2], color=T["cols"][2], color_continuous_scale="Reds")
        st.plotly_chart(fig1, use_container_width=True)

        gc1, gc2 = st.columns(2)
        with gc1:
            st.subheader(T["ui"]["c_loc"])
            fig2 = px.bar(df_viz, x=T["cols"][3], color=T["cols"][3])
            st.plotly_chart(fig2, use_container_width=True)
        
        with gc2:
            st.subheader(T["ui"]["c_trig"])
            raw_trigs = df[SYS_COLS[5]].str.split(', ', expand=True).stack()
            if not raw_trigs.empty:
                if lang_key == "Hebrew":
                    raw_trigs = raw_trigs.map(lambda x: VAL_MAP.get(x, x))
                fig3 = px.pie(names=raw_trigs.values)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.write(T["ui"]["empty"])

# ==========================================
# СТРАНИЦА: РЕДАКТОР
# ==========================================
elif page == T["ui"]["menu_edit"]:
    st.title(T["ui"]["edit_title"])
    st.info(T["ui"]["edit_help"])
    
    df = load_data()
    
    if df.empty:
        st.warning(T["ui"]["empty"])
    else:
        display_df = df.copy()
        display_df.columns = T["cols"]
        
        col_cfg = {
            T["cols"][1]: st.column_config.TimeColumn(format="HH:mm"),
            T["cols"][0]: st.column_config.DateColumn(format="DD.MM.YYYY"),
            T["cols"][2]: st.column_config.NumberColumn(min_value=1, max_value=10)
        }

        edited_df = st.data_editor(
            display_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config=col_cfg
        )

        if st.button(T["ui"]["update_btn"]):
            save_data(edited_df)
            st.success(T["ui"]["success"])
            time.sleep(1)
            st.rerun()