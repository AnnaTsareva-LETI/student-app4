# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import json
import hashlib
from datetime import date, datetime, timedelta


# ============================================================
# Настройки страницы
# ============================================================

st.set_page_config(
    page_title="Цифровая прослеживаемость",
    page_icon="📏",
    layout="wide"
)


# ============================================================
# Вспомогательные функции
# ============================================================

def to_native(obj):
    """
    Преобразует numpy-типы в стандартные Python-типы,
    чтобы объект можно было корректно сохранить в JSON.
    """
    if isinstance(obj, dict):
        return {str(k): to_native(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [to_native(v) for v in obj]

    elif isinstance(obj, tuple):
        return tuple(to_native(v) for v in obj)

    elif isinstance(obj, np.integer):
        return int(obj)

    elif isinstance(obj, np.floating):
        return float(obj)

    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()

    else:
        return obj


def parse_readings(text):
    """
    Преобразование строки с измерениями в массив чисел.
    Допускаются разделители:
    - пробел;
    - запятая;
    - точка с запятой;
    - перенос строки.

    Важно:
    Для десятичной дроби лучше использовать точку.
    Например: 24.91
    """
    if not isinstance(text, str):
        return np.array([], dtype=float)

    normalized = text.replace(";", " ")
    normalized = normalized.replace("\n", " ")

    # Поддержка десятичной запятой в простом случае:
    # если пользователь ввел "24,91 24,92", заменим запятые на точки.
    # Но если ввел "24,91, 24,92", тоже обработается.
    normalized = normalized.replace(",", " ")

    values = []

    for item in normalized.split():
        item = item.strip()
        try:
            values.append(float(item))
        except ValueError:
            pass

    return np.array(values, dtype=float)


def canonical_hash(data_dict):
    """
    Формирование SHA-256 хеша цифрового документа.
    Хеш позволяет проверить, что данные не были изменены.
    """
    data_dict = to_native(data_dict)

    canonical = json.dumps(
        data_dict,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def uncertainty_budget(
    mean_indication,
    n,
    std,
    resolution,
    u_k,
    u_b,
    u_ref,
    drift_limit,
    env_limit
):
    """
    Расчет составляющих стандартной неопределенности.
    Все результаты приводятся к стандартному типу float.
    """

    mean_indication = float(mean_indication)
    n = int(n)
    std = float(std)
    resolution = float(resolution)
    u_k = float(u_k)
    u_b = float(u_b)
    u_ref = float(u_ref)
    drift_limit = float(drift_limit)
    env_limit = float(env_limit)

    u_repeat = float(std / np.sqrt(n)) if n > 1 else 0.0
    u_resolution = float(resolution / np.sqrt(12))
    u_scale = float(abs(mean_indication) * u_k)
    u_offset = float(u_b)
    u_reference = float(u_ref)
    u_drift = float(drift_limit / np.sqrt(3))
    u_environment = float(env_limit / np.sqrt(3))

    components = {
        "Повторяемость": u_repeat,
        "Разрешение СИ": u_resolution,
        "Неопределенность коэффициента масштаба": u_scale,
        "Неопределенность смещения": u_offset,
        "Неопределенность эталона/калибратора": u_reference,
        "Дрейф между калибровками": u_drift,
        "Влияние условий окружающей среды": u_environment,
    }

    uc = float(np.sqrt(sum(float(v) ** 2 for v in components.values())))
    U = float(2 * uc)

    return components, uc, U


# ============================================================
# Заголовок
# ============================================================

st.title("📏 Виртуальная практическая работа")
st.subheader("Цифровая прослеживаемость результатов измерений")

st.markdown(
    """
    **Дисциплина:** Цифровая метрология  
    **Тема:** Цифровая прослеживаемость результатов измерений  
    **Продолжительность:** 1,5 часа  

    **Цель работы:** изучить принцип цифровой метрологической прослеживаемости,
    рассчитать результат измерения с учетом калибровочных коэффициентов,
    оценить неопределенность и сформировать цифровой сертификат измерения.
    """
)

tabs = st.tabs([
    "1. Описание",
    "2. Цепочка прослеживаемости",
    "3. Исходные данные",
    "4. Расчёт",
    "5. Цифровой сертификат",
    "6. Вопросы и вывод"
])


# ============================================================
# Вкладка 1. Описание
# ============================================================

with tabs[0]:
    st.header("1. Описание практической работы")

    st.markdown(
        """
        В данной работе рассматривается пример цифровой прослеживаемости
        результата измерения температуры.

        **Прослеживаемость** означает, что результат измерения может быть связан
        с эталоном через непрерывную цепочку калибровок, каждая из которых
        имеет документированную неопределенность.

        В рамках работы используется упрощенная измерительная модель:

        $$
        T = k \\cdot I + b
        $$

        где:

        - **T** — исправленное значение температуры, °C;
        - **I** — среднее показание датчика, °C;
        - **k** — коэффициент масштаба;
        - **b** — поправка смещения, °C.

        Итоговый результат представляется в виде:

        $$
        T = \\bar{T} \\pm U, \\quad k_p = 2
        $$

        где **U** — расширенная неопределенность.
        """
    )

    st.info(
        """
        В данной работе цифровой сертификат представлен в учебном формате JSON.
        Он не является официальным цифровым калибровочным сертификатом,
        но демонстрирует основные принципы цифровой метрологии:
        структурирование данных, прослеживаемость, метаданные,
        неопределенность и контроль неизменности через хеш.
        """
    )

    st.markdown("### Что студент должен получить по итогам работы")

    st.markdown(
        """
        По итогам выполнения работы необходимо получить:

        1. Исправленное значение измеряемой величины.
        2. Бюджет неопределенности.
        3. Расширенную неопределенность.
        4. Проверку полноты цепочки прослеживаемости.
        5. Проверку срока действия калибровки.
        6. Цифровой сертификат измерения в формате JSON.
        7. SHA-256 хеш цифрового документа.
        """
    )


# ============================================================
# Вкладка 2. Цепочка прослеживаемости
# ============================================================

with tabs[1]:
    st.header("2. Цепочка цифровой метрологической прослеживаемости")

    st.markdown(
        """
        Выберите элементы цепочки прослеживаемости, которые присутствуют
        в виртуальном измерительном процессе.
        """
    )

    chain_elements = st.multiselect(
        "Элементы цепочки прослеживаемости",
        [
            "Национальный эталон",
            "Государственная поверочная схема",
            "Эталон организации",
            "Калибратор температуры",
            "Калиброванный датчик температуры",
            "Средство регистрации данных",
            "Программное обеспечение обработки",
            "Цифровой сертификат результата"
        ],
        default=[
            "Национальный эталон",
            "Эталон организации",
            "Калибратор температуры",
            "Калиброванный датчик температуры",
            "Программное обеспечение обработки",
            "Цифровой сертификат результата"
        ]
    )

    st.markdown("### Условная схема")

    # Чтобы избежать возможных проблем с graphviz на облаке,
    # схема дана в markdown-формате.
    st.markdown(
        """
        ```text
        Национальный эталон
                ↓
        Эталон организации
                ↓
        Калибратор температуры
                ↓
        Калиброванный датчик температуры
                ↓
        Средство регистрации / ПО обработки
                ↓
        Цифровой сертификат результата
        ```
        """
    )

    required = [
        "Национальный эталон",
        "Эталон организации",
        "Калибратор температуры",
        "Калиброванный датчик температуры",
        "Цифровой сертификат результата"
    ]

    chain_ok = all(item in chain_elements for item in required)

    if chain_ok:
        st.success("Цепочка прослеживаемости содержит основные необходимые элементы.")
    else:
        st.warning(
            "Цепочка прослеживаемости неполная. "
            "Проверьте наличие эталона, калибратора, датчика и цифрового сертификата."
        )


# ============================================================
# Вкладка 3. Исходные данные
# ============================================================

with tabs[2]:
    st.header("3. Исходные данные и параметры калибровки")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Измерительное средство")

        instrument_id = st.text_input("ID датчика", "TEMP-SENSOR-001")
        manufacturer = st.text_input("Производитель", "Учебный датчик")
        measurand = st.text_input("Измеряемая величина", "Температура")
        unit = st.text_input("Единица измерения", "°C")

        resolution = st.number_input(
            "Разрешение датчика, °C",
            min_value=0.0001,
            value=0.01,
            step=0.01,
            format="%.4f"
        )

        calibration_date = st.date_input(
            "Дата последней калибровки",
            value=date.today() - timedelta(days=120)
        )

        calibration_interval_months = st.number_input(
            "Межкалибровочный интервал, месяцев",
            min_value=1,
            max_value=60,
            value=12,
            step=1
        )

    with col2:
        st.subheader("Калибровочные коэффициенты")

        k = st.number_input(
            "Коэффициент масштаба k",
            value=1.002,
            step=0.001,
            format="%.6f"
        )

        b = st.number_input(
            "Поправка смещения b, °C",
            value=-0.12,
            step=0.01,
            format="%.4f"
        )

        u_k = st.number_input(
            "Стандартная неопределенность k",
            value=0.0005,
            step=0.0001,
            format="%.6f"
        )

        u_b = st.number_input(
            "Стандартная неопределенность b, °C",
            value=0.03,
            step=0.01,
            format="%.4f"
        )

        u_ref = st.number_input(
            "Стандартная неопределенность эталона/калибратора, °C",
            value=0.04,
            step=0.01,
            format="%.4f"
        )

    st.subheader("Серия измерений")

    readings_text = st.text_area(
        "Введите показания датчика, °C",
        value="24.91 24.94 24.93 24.95 24.92 24.96 24.94 24.93 24.95 24.94",
        height=100
    )

    col3, col4 = st.columns(2)

    with col3:
        drift_limit = st.number_input(
            "Предел дрейфа между калибровками, °C",
            value=0.05,
            step=0.01,
            format="%.4f"
        )

    with col4:
        env_limit = st.number_input(
            "Предел влияния условий окружающей среды, °C",
            value=0.04,
            step=0.01,
            format="%.4f"
        )

    max_allowed_U = st.number_input(
        "Максимально допустимая расширенная неопределенность, °C",
        value=0.20,
        step=0.01,
        format="%.4f"
    )

    st.info(
        """
        Совет: попробуйте изменить дату калибровки, разрешение датчика,
        предел дрейфа или разброс измерений и посмотрите, как изменится
        итоговая неопределенность и статус прослеживаемости.
        """
    )


# ============================================================
# Общие расчеты
# ============================================================

readings = parse_readings(readings_text)

if len(readings) > 0:
    mean_I = float(np.mean(readings))
    std_I = float(np.std(readings, ddof=1)) if len(readings) > 1 else 0.0
    corrected_T = float(k * mean_I + b)

    components, uc, U = uncertainty_budget(
        mean_I,
        len(readings),
        std_I,
        resolution,
        u_k,
        u_b,
        u_ref,
        drift_limit,
        env_limit
    )

    valid_until = calibration_date + timedelta(days=int(30 * int(calibration_interval_months)))
    cert_valid = bool(date.today() <= valid_until)
    uncertainty_ok = bool(U <= float(max_allowed_U))
else:
    mean_I = None
    std_I = None
    corrected_T = None
    components = {}
    uc = None
    U = None
    valid_until = None
    cert_valid = False
    uncertainty_ok = False


# ============================================================
# Вкладка 4. Расчет
# ============================================================

with tabs[3]:
    st.header("4. Расчёт результата измерения и неопределенности")

    if len(readings) == 0:
        st.error("Введите хотя бы одно числовое значение измерения.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Количество измерений", f"{len(readings)}")

        with col2:
            st.metric("Среднее показание I, °C", f"{mean_I:.4f}")

        with col3:
            st.metric("СКО показаний, °C", f"{std_I:.4f}")

        st.markdown("### Исправленный результат")

        st.latex(r"T = k \cdot I + b")

        st.success(
            f"Исправленное значение температуры: **T = {corrected_T:.3f} {unit}**"
        )

        st.markdown("### Бюджет стандартной неопределенности")

        budget_df = pd.DataFrame({
            "Составляющая": list(components.keys()),
            "Стандартная неопределенность, °C": [float(v) for v in components.values()]
        })

        st.dataframe(budget_df, use_container_width=True)

        chart_df = budget_df.set_index("Составляющая")
        st.bar_chart(chart_df)

        st.markdown("### Итоговая неопределенность")

        col4, col5 = st.columns(2)

        with col4:
            st.metric(
                "Суммарная стандартная неопределенность uc, °C",
                f"{uc:.4f}"
            )

        with col5:
            st.metric(
                "Расширенная неопределенность U, °C при k=2",
                f"{U:.4f}"
            )

        st.info(
            f"Результат измерения: **T = ({corrected_T:.3f} ± {U:.3f}) {unit}, k = 2**"
        )

        st.markdown("### Проверка пригодности результата")

        if uncertainty_ok:
            st.success("Расширенная неопределенность не превышает заданный предел.")
        else:
            st.error("Расширенная неопределенность превышает заданный предел.")

        if cert_valid:
            st.success(f"Калибровка действительна до {valid_until}.")
        else:
            st.error(f"Срок действия калибровки истёк: {valid_until}.")


# ============================================================
# Вкладка 5. Цифровой сертификат
# ============================================================

with tabs[4]:
    st.header("5. Цифровой сертификат измерения")

    if len(readings) == 0:
        st.error("Невозможно сформировать сертификат без данных измерений.")
    else:
        dcc = {
            "document_type": "Educational Digital Measurement Certificate",
            "version": "1.0",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "instrument": {
                "instrument_id": instrument_id,
                "manufacturer": manufacturer,
                "measurand": measurand,
                "unit": unit,
                "resolution": float(resolution)
            },
            "calibration": {
                "calibration_date": str(calibration_date),
                "valid_until": str(valid_until),
                "scale_coefficient_k": float(k),
                "offset_b": float(b),
                "standard_uncertainty_k": float(u_k),
                "standard_uncertainty_b": float(u_b),
                "standard_uncertainty_reference": float(u_ref),
                "traceability_chain": chain_elements
            },
            "measurement": {
                "raw_readings": [float(x) for x in readings.tolist()],
                "mean_indication": float(mean_I),
                "standard_deviation": float(std_I),
                "corrected_result": float(corrected_T),
                "unit": unit
            },
            "uncertainty_budget": {
                str(name): float(value)
                for name, value in components.items()
            },
            "uncertainty": {
                "combined_standard_uncertainty": float(uc),
                "coverage_factor": 2,
                "expanded_uncertainty": float(U)
            },
            "quality_checks": {
                "traceability_chain_complete": bool(chain_ok),
                "calibration_valid": bool(cert_valid),
                "uncertainty_within_limit": bool(uncertainty_ok)
            }
        }

        dcc = to_native(dcc)
        dcc_hash = canonical_hash(dcc)
        dcc["sha256_hash"] = dcc_hash

        st.markdown("### Цифровой документ")

        st.json(dcc)

        st.markdown("### SHA-256 хеш документа")

        st.code(dcc_hash)

        json_data = json.dumps(
            dcc,
            ensure_ascii=False,
            indent=4
        )

        st.download_button(
            label="Скачать цифровой сертификат JSON",
            data=json_data.encode("utf-8"),
            file_name="digital_measurement_certificate.json",
            mime="application/json"
        )

        st.markdown("### Итоговая проверка цифровой прослеживаемости")

        if chain_ok and cert_valid and uncertainty_ok:
            st.success(
                "Результат можно считать цифрово прослеживаемым в рамках учебной модели."
            )
        else:
            st.warning(
                """
                Результат не полностью удовлетворяет требованиям цифровой прослеживаемости.
                Проверьте полноту цепочки, срок действия калибровки и неопределенность.
                """
            )


# ============================================================
# Вкладка 6. Вопросы и вывод
# ============================================================

with tabs[5]:
    st.header("6. Контрольные вопросы и вывод")

    st.markdown(
        """
        Ответьте на вопросы в отчёте по практической работе.

        1. Что означает метрологическая прослеживаемость результата измерения?
        2. Почему одного числового значения результата недостаточно?
        3. Какие элементы должны входить в цепочку прослеживаемости?
        4. Чем отличается стандартная неопределенность от расширенной?
        5. Какие составляющие вошли в бюджет неопределенности в данной работе?
        6. Почему важно учитывать срок действия калибровки?
        7. Для чего используется цифровой сертификат?
        8. Как хеш документа связан с обеспечением целостности данных?
        9. Какие данные необходимо добавить, чтобы цифровой сертификат стал ближе к реальному DCC?
        10. Какие риски возникают при использовании непрослеживаемых измерительных данных?
        """
    )

    st.markdown("### Шаблон вывода")

    st.info(
        """
        В выводе необходимо указать:

        - была ли сформирована полная цепочка прослеживаемости;
        - какое исправленное значение измеряемой величины получено;
        - чему равна расширенная неопределенность;
        - пригоден ли результат по критерию допустимой неопределенности;
        - действителен ли калибровочный сертификат;
        - можно ли считать результат цифрово прослеживаемым.
        """
    )

    st.markdown("### Автоматически сформированный краткий итог")

    if len(readings) > 0:
        if chain_ok and cert_valid and uncertainty_ok:
            status = "результат удовлетворяет условиям цифровой прослеживаемости в рамках учебной модели"
        else:
            status = "результат требует проверки, так как не все условия цифровой прослеживаемости выполнены"

        st.write(
            f"""
            По результатам виртуального измерения получено исправленное значение:

            **T = ({corrected_T:.3f} ± {U:.3f}) {unit}, k = 2.**

            Цепочка прослеживаемости полная: **{chain_ok}**.  
            Калибровка действительна: **{cert_valid}**.  
            Неопределенность в допустимых пределах: **{uncertainty_ok}**.  

            Следовательно, {status}.
            """
        )
    else:
        st.warning("Для автоматического вывода необходимо ввести измерительные данные.")
