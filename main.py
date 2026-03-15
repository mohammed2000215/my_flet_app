"""
حاسبة الدخل - نسخة متطورة
- قسم جديد: حساب ضريبة الدخل المقطوع مع إدارة المهن
- حفظ دائم للمهن والإعدادات
- إمكانية تعديل النسب والشرائح
"""

import flet as ft
import math
import json
import os
from datetime import datetime, date

# ══════════════════════════════════════
#  مسار ملف الحفظ
# ══════════════════════════════════════



DEFAULT_SETTINGS = {
    "nafaqat_default": 3,
    "idara_default": 10,
    "rawatib_default": 10,
    "rasm_idara_pct": 0.10,
    "color_green": "#2E7D32",
    "color_blue": "#1565C0",
    "color_red": "#C62828",
    "color_dark_green": "#006400",
    "color_purple": "#6A1B9A",
    "color_teal": "#00695C",
    "color_orange": "#E65100",
    "arbah_old_exempt": 3000000,
    "arbah_old_brackets": [
        [3000000,   10000000,  0.10],
        [10000000,  30000000,  0.14],
        [30000000,  100000000, 0.18],
        [100000000, 500000000, 0.22],
        [500000000, None,      0.25],
    ],
    "arbah_new_exempt": 30000,
    "arbah_new_brackets": [
        [30000,    100000,   0.10],
        [100000,   300000,   0.14],
        [300000,   1000000,  0.18],
        [1000000,  5000000,  0.22],
        [5000000,  None,     0.25],
    ],
    "maqtou3_exempt": 30000,
    "maqtou3_brackets": [
        [1,       100000,   0.10],
        [100000,  300000,   0.14],
        [300000,  1000000,  0.18],
        [1000000, 5000000,  0.22],
        [5000000, None,     0.25],
    ],
    "mihna_list": [],
}


def load_data(page):
    data_file = _get_data_file()
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(saved)
            return merged
        except Exception as ex:
            print(f"خطأ في التحميل: {ex}")
    return DEFAULT_SETTINGS.copy()


def save_data(data, page):
    data_file = _get_data_file()
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"خطأ في الحفظ: {ex}")


def _get_data_file():
    # المسار الخاص بتطبيق Flet
    app_storage = os.getenv("FLET_APP_STORAGE_DATA")

    if not app_storage:
        # fallback ثابت يعمل على Android و Desktop
        app_storage = os.path.join(os.path.expanduser("~"), ".hasiba")

    os.makedirs(app_storage, exist_ok=True)

    return os.path.join(app_storage, "hasiba_data.json")


def make_card(content, color):
    return ft.Container(
        content=content,
        bgcolor=color,
        padding=15,
        border_radius=12,
        margin=ft.margin.symmetric(vertical=5),
    )


def result_row(label, value, size=16):
    return ft.Text(f"{label}: {int(value):,}", color="white", size=size)


def section_title(text, color):
    return ft.Text(text, size=22, weight="bold", color=color, text_align="center")


def num_field(label, value="", hint="", width=None):
    kwargs = dict(
        label=label,
        value=str(value),
        hint_text=hint,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        text_size=16,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=14),
    )
    if width:
        kwargs["width"] = width
    return ft.TextField(**kwargs)


def text_field(label, value="", hint="", width=None):
    kwargs = dict(
        label=label,
        value=str(value),
        hint_text=hint,
        border_radius=10,
        text_size=16,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=14),
    )
    if width:
        kwargs["width"] = width
    return ft.TextField(**kwargs)


def validate_number(field, label="القيمة"):
    raw = (field.value or "").strip()
    if not raw:
        field.error_text = f"يرجى ادخال {label}"
        field.update()
        return None
    try:
        val = float(raw)
        if val <= 0:
            field.error_text = "يجب ان يكون الرقم اكبر من صفر"
            field.update()
            return None
        field.error_text = None
        field.update()
        return val
    except ValueError:
        field.error_text = "ارقام فقط"
        field.update()
        return None


def calc_maqtou3_tax(ribh_safi, brackets, exempt):
    """حساب ضريبة الدخل المقطوع بالشرائح مع الإعفاء في الشريحة الأولى"""
    tafaseel = []
    dariba_klia = 0
    for bracket in brackets:
        lower = bracket[0]
        upper = bracket[1]
        nisba = bracket[2]
        upper_val = upper if upper is not None else float("inf")

        if ribh_safi <= lower:
            break

        wia3 = min(ribh_safi, upper_val) - lower

        # الشريحة الأولى: طرح الإعفاء
        if lower <= 1:
            wia3_taxable = max(0, min(ribh_safi, upper_val) - exempt)
        else:
            wia3_taxable = wia3

        sh_d = math.ceil(round(wia3_taxable * nisba, 8)) if wia3_taxable > 0 else 0
        dariba_klia += sh_d
        tafaseel.append({
            "pct": nisba * 100,
            "lower": lower,
            "upper": upper_val,
            "wia3": wia3,
            "wia3_taxable": wia3_taxable,
            "dariba": sh_d,
        })
    return tafaseel, dariba_klia


def calc_arbah_brackets(mablagh, brackets):
    tafaseel = []
    dariba_klia = 0
    for bracket in brackets:
        lower = bracket[0]
        upper = bracket[1]
        nisba = bracket[2]
        upper_val = upper if upper is not None else float("inf")
        if mablagh <= lower:
            break
        wia3 = min(mablagh, upper_val) - lower
        sh_d = math.ceil(round(wia3 * nisba, 8))
        dariba_klia += sh_d
        tafaseel.append({
            "pct": nisba * 100,
            "lower": lower,
            "upper": upper_val,
            "wia3": wia3,
            "dariba": sh_d,
        })
    return tafaseel, dariba_klia


def main(page: ft.Page):
    page.title = "حاسبة الدخل"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = ft.padding.symmetric(horizontal=16, vertical=12)
    page.bgcolor = "#F5F5F5"
    page.window_width = 420
    page.window_height = 820

    SETTINGS = load_data(page)

    # ── فهرس البحث السريع للمهن ──────────────────
    _mihna_index = {}

    def rebuild_index():
        _mihna_index.clear()
        for m in SETTINGS.get("mihna_list", []):
            _mihna_index[str(m["ramz"])] = m
            for word in m["ism"].lower().split():
                _mihna_index.setdefault(word, [])
                if isinstance(_mihna_index[word], list):
                    _mihna_index[word].append(m)

    def search_mihna(query):
        query = query.strip().lower()
        if not query:
            return []
        seen = set()
        results = []
        for m in SETTINGS.get("mihna_list", []):
            key = m["ramz"]
            if key in seen:
                continue
            if query in m["ism"].lower() or query in str(m["ramz"]):
                seen.add(key)
                results.append(m)
                if len(results) >= 5:
                    break
        return results

    rebuild_index()

    GREEN      = SETTINGS["color_green"]
    BLUE       = SETTINGS["color_blue"]
    RED        = SETTINGS["color_red"]
    DARK_GREEN = SETTINGS["color_dark_green"]
    PURPLE     = SETTINGS["color_purple"]
    TEAL       = SETTINGS["color_teal"]
    ORANGE     = SETTINGS["color_orange"]

    def back_btn(dest):
        return ft.OutlinedButton(
            "العودة للقائمة الرئيسية",
            on_click=dest, width=360, height=46,
            style=ft.ButtonStyle(color=DARK_GREEN),
        )

    def menu_btn(label, color, handler):
        return ft.ElevatedButton(
            label, bgcolor=color, color="white",
            on_click=handler, width=360, height=56,
        )

    def calc_btn(label, color, handler):
        return ft.ElevatedButton(
            label, bgcolor=color, color="white",
            width=360, height=50, on_click=handler,
        )

    # ══════════════════════════════════════
    #  الصفحة الرئيسية
    # ══════════════════════════════════════
    def show_home(e=None):
        page.controls.clear()
        page.add(ft.Column(
            controls=[
                ft.Container(height=20),
                ft.Text("حاسبة الدخل", size=30, weight="bold",
                        color=DARK_GREEN, text_align="center"),
                ft.Container(height=4),
                ft.Text("اختر نوع العملية المراد حسابها",
                        size=15, color="grey", text_align="center"),
                ft.Container(height=24),
                menu_btn("حساب تحققات الدخل المقطوع", GREEN,  show_maqtou3),
                ft.Container(height=10),
                menu_btn("ضريبة الدخل المقطوع",        ORANGE, show_dariba_maqtou3),
                ft.Container(height=10),
                menu_btn("ريع رؤوس الاموال المتداولة",  BLUE,   show_rea3),
                ft.Container(height=10),
                menu_btn("الارباح الحقيقية",             PURPLE, show_arbah),
                ft.Container(height=10),
                menu_btn("⚙️ الإعدادات والنسب",          TEAL,   show_settings),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  1) حساب تحققات الدخل المقطوع
    # ══════════════════════════════════════
    def show_maqtou3(e=None):
        page.controls.clear()

        income_f  = num_field("القيمة المراد حسابها", hint="مثال: 500000")
        nafaqat_f = num_field("نسبة النفقات %",  value=SETTINGS["nafaqat_default"], width=110)
        idara_f   = num_field("نسبة الادارة %",  value=SETTINGS["idara_default"],   width=110)
        rawatib_f = num_field("نسبة الرواتب %",  value=SETTINGS["rawatib_default"], width=110)

        years_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="1", label="سنة واحدة"),
                 ft.Radio(value="2", label="سنتين")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="1",
        )
        mult_dd = ft.Dropdown(
            label="مضاعف السنة الثانية", value="1", visible=False,
            options=[ft.dropdown.Option(str(i), f"x {i}") for i in range(1, 6)],
        )
        results_col = ft.Column(spacing=10)

        def on_years_change(e):
            mult_dd.visible = (years_rg.value == "2")
            page.update()
        years_rg.on_change = on_years_change

        def calc(e):
            val = validate_number(income_f, "القيمة")
            if val is None:
                page.update()
                return

            np_r = float(nafaqat_f.value or SETTINGS["nafaqat_default"]) / 100
            ip_r = float(idara_f.value   or SETTINGS["idara_default"])   / 100
            rp_r = float(rawatib_f.value or SETTINGS["rawatib_default"]) / 100

            d1 = math.ceil(val)
            n1 = math.ceil(d1 * np_r)
            i1 = math.ceil(d1 * ip_r)
            r1 = math.ceil(d1 * rp_r)
            t1 = d1 + n1 + i1 + r1

            results_col.controls.clear()
            results_col.controls.append(make_card(ft.Column([
                ft.Text("السنة الاولى", weight="bold", size=18, color="white"),
                result_row("الدخل",   d1),
                result_row("النفقات", n1),
                result_row("الادارة", i1),
                result_row("الرواتب", r1),
                ft.Divider(color="white54"),
                result_row("المجموع", t1, size=17),
            ]), GREEN))

            grand = t1
            if years_rg.value == "2":
                mult = int(mult_dd.value or 1)
                d2 = math.ceil(d1 * mult)
                n2 = math.ceil(d2 * np_r)
                i2 = math.ceil(d2 * ip_r)
                r2 = math.ceil(d2 * rp_r)
                t2 = d2 + n2 + i2 + r2
                grand += t2
                results_col.controls.append(make_card(ft.Column([
                    ft.Text("السنة الثانية", weight="bold", size=18, color="white"),
                    result_row("الدخل",   d2),
                    result_row("النفقات", n2),
                    result_row("الادارة", i2),
                    result_row("الرواتب", r2),
                    ft.Divider(color="white54"),
                    result_row("المجموع", t2, size=17),
                ]), BLUE))

            results_col.controls.append(make_card(
                ft.Text(f"الاجمالي الكلي: {int(grand):,}",
                        weight="bold", size=22, color="white", text_align="center"),
                RED,
            ))
            page.update()

        page.add(ft.Column(
            controls=[
                section_title("حساب تحققات الدخل المقطوع", DARK_GREEN),
                ft.Divider(),
                ft.Text("النسب (قابلة للتعديل):", weight="bold", color=DARK_GREEN),
                ft.Row([nafaqat_f, idara_f, rawatib_f], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                income_f,
                ft.Text("عدد السنوات:", weight="bold"),
                years_rg, mult_dd,
                calc_btn("احسب", DARK_GREEN, calc),
                results_col,
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  2) ضريبة الدخل المقطوع (قسم جديد)
    # ══════════════════════════════════════
    def show_dariba_maqtou3(e=None):
        page.controls.clear()

        search_f = text_field("ابحث باسم أو رمز المهنة", hint="مثال: محامي أو 101")
        suggestions_col = ft.Column(spacing=4, visible=False)
        selected_mihna = {"data": None}
        mihna_info = ft.Container(visible=False)
        daily_f = num_field("الدخل اليومي", hint="مثال: 50000")
        results_col = ft.Column(spacing=10)

        def update_suggestions(e):
            query = (search_f.value or "").strip()
            suggestions_col.controls.clear()
            if len(query) < 1:
                suggestions_col.visible = False
                page.update()
                return

            matches = search_mihna(query)

            if matches:
                suggestions_col.visible = True
                for m in matches[:5]:
                    def make_handler(mihna):
                        def handler(e):
                            select_mihna(mihna)
                        return handler
                    suggestions_col.controls.append(
                        ft.ListTile(
                            title=ft.Text(f"{m['ism']}  ({m['ramz']})", size=14),
                            subtitle=ft.Text(
                                f"أيام العمل: {m['ayam']} | نسبة الربح: {m['nisba']}%",
                                size=12,
                            ),
                            on_click=make_handler(m),
                            bgcolor="#E3F2FD",
                        )
                    )
            else:
                suggestions_col.visible = False
            page.update()

        search_f.on_change = update_suggestions

        def select_mihna(m):
            selected_mihna["data"] = m
            search_f.value = f"{m['ism']} ({m['ramz']})"
            search_f.error_text = None
            suggestions_col.visible = False
            mihna_info.content = ft.Container(
                content=ft.Column([
                    ft.Text("المهنة المختارة", weight="bold", size=15, color=ORANGE),
                    ft.Text(f"الاسم: {m['ism']}", size=14),
                    ft.Text(f"الرمز: {m['ramz']}", size=14),
                    ft.Text(f"أيام العمل السنوي: {m['ayam']}", size=14),
                    ft.Text(f"نسبة الربح: {m['nisba']}%", size=14),
                ]),
                bgcolor="#FFF3E0",
                padding=10,
                border_radius=10,
            )
            mihna_info.visible = True
            results_col.controls.clear()
            page.update()

        def calc(e):
            if selected_mihna["data"] is None:
                search_f.error_text = "يرجى اختيار مهنة من القائمة"
                search_f.update()
                return

            daily = validate_number(daily_f, "الدخل اليومي")
            if daily is None:
                page.update()
                return

            m = selected_mihna["data"]
            ayam       = m["ayam"]
            nisba_ribh = m["nisba"] / 100

            dakhl_sanawi = math.ceil(daily * ayam)
            ribh_safi    = math.ceil(dakhl_sanawi * nisba_ribh)

            exempt   = SETTINGS["maqtou3_exempt"]
            brackets = SETTINGS["maqtou3_brackets"]
            tafaseel, dariba = calc_maqtou3_tax(ribh_safi, brackets, exempt)

            results_col.controls.clear()

            rows = [
                ft.Text("نتيجة حساب ضريبة الدخل المقطوع",
                        weight="bold", size=17, color="white"),
                ft.Divider(color="white54"),
                result_row("الدخل اليومي",              math.ceil(daily)),
                result_row("أيام العمل السنوي",          ayam),
                result_row("الدخل السنوي الإجمالي",      dakhl_sanawi),
                result_row(f"نسبة الربح ({m['nisba']}%)", math.ceil(dakhl_sanawi * nisba_ribh)),
                result_row("الربح الصافي (وعاء الضريبة)", ribh_safi),
                result_row("الحد المعفى",                int(exempt)),
                ft.Divider(color="white54"),
                ft.Text("تفصيل الشرائح:", color="white70", size=13, weight="bold"),
            ]

            for i, sh in enumerate(tafaseel, 1):
                upper_str = f"{int(sh['upper']):,}" if sh["upper"] != float("inf") else "فما فوق"
                rows.append(ft.Text(
                    f"الشريحة {i} ({sh['pct']:.0f}%)  من {int(sh['lower']):,} إلى {upper_str}",
                    color="white70", size=13,
                ))
                rows.append(ft.Text(
                    f"    الوعاء الخاضع: {int(sh['wia3_taxable']):,}  |  الضريبة: {int(sh['dariba']):,}",
                    color="white", size=14,
                ))

            rows += [
                ft.Divider(color="white54"),
                ft.Text(f"مجموع الضريبة النهائي: {int(dariba):,}",
                        weight="bold", size=19, color="white"),
            ]

            results_col.controls.append(make_card(ft.Column(rows), ORANGE))
            page.update()

        # ── إدارة المهن ──
        def show_manage_mihna(e):
            page.controls.clear()
            mihna_list_col = ft.Column(spacing=8)
            ism_f   = text_field("اسم المهنة",           hint="مثال: محامي")
            ramz_f  = num_field("رمز المهنة",             hint="مثال: 101")
            ayam_f  = num_field("أيام العمل السنوي",      hint="مثال: 270")
            nisba_f = num_field("نسبة الربح %",           hint="مثال: 70")
            add_msg     = ft.Text("", color="green", size=13)
            edit_index  = {"i": None}

            def refresh_list():
                mihna_list_col.controls.clear()
                for idx, m in enumerate(SETTINGS["mihna_list"]):
                    def make_edit(i):
                        def do_edit(e):
                            m2 = SETTINGS["mihna_list"][i]
                            ism_f.value   = m2["ism"]
                            ramz_f.value  = str(m2["ramz"])
                            ayam_f.value  = str(m2["ayam"])
                            nisba_f.value = str(m2["nisba"])
                            edit_index["i"] = i
                            add_msg.value = "⚠️ جاري التعديل... اضغط حفظ بعد التعديل"
                            add_msg.color = "orange"
                            page.update()
                        return do_edit

                    def make_delete(i):
                        def do_delete(e):
                            SETTINGS["mihna_list"].pop(i)
                            save_data(SETTINGS, page)
                            rebuild_index()
                            refresh_list()
                            page.update()
                        return do_delete

                    mihna_list_col.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"{m['ism']}  [{m['ramz']}]",
                                            weight="bold", size=14),
                                    ft.Text(
                                        f"أيام: {m['ayam']}  |  نسبة الربح: {m['nisba']}%",
                                        size=12, color="grey",
                                    ),
                                ], expand=True, spacing=2),
                                ft.ElevatedButton("تعديل", bgcolor=BLUE, color="white",
                                              on_click=make_edit(idx), height=36),
                                ft.ElevatedButton("حذف", bgcolor=RED, color="white",
                                              on_click=make_delete(idx), height=36),
                            ]),
                            bgcolor="white", padding=10,
                            border_radius=10,
                            margin=ft.margin.symmetric(vertical=3),
                        )
                    )
                page.update()

            def save_mihna(e):
                ism = (ism_f.value or "").strip()
                if not ism:
                    ism_f.error_text = "يرجى إدخال اسم المهنة"
                    ism_f.update()
                    return
                ramz  = validate_number(ramz_f,  "رمز المهنة")
                ayam  = validate_number(ayam_f,  "أيام العمل")
                nisba = validate_number(nisba_f, "نسبة الربح")
                if not all([ramz, ayam, nisba]):
                    page.update()
                    return

                new_m = {
                    "ism":   ism,
                    "ramz":  int(ramz),
                    "ayam":  int(ayam),
                    "nisba": nisba,
                }

                if edit_index["i"] is not None:
                    SETTINGS["mihna_list"][edit_index["i"]] = new_m
                    add_msg.value = "✅ تم تعديل المهنة بنجاح"
                    edit_index["i"] = None
                else:
                    SETTINGS["mihna_list"].append(new_m)
                    add_msg.value = "✅ تم إضافة المهنة بنجاح"

                add_msg.color = "green"
                save_data(SETTINGS, page)
                rebuild_index()
                ism_f.value = ramz_f.value = ayam_f.value = nisba_f.value = ""
                refresh_list()
                page.update()

            refresh_list()

            page.add(ft.Column(
                controls=[
                    section_title("إدارة المهن", ORANGE),
                    ft.Divider(),
                    ft.Text("إضافة / تعديل مهنة:", weight="bold", color=ORANGE),
                    ism_f, ramz_f, ayam_f, nisba_f,
                    calc_btn("💾 حفظ المهنة", ORANGE, save_mihna),
                    add_msg,
                    ft.Divider(),
                    ft.Text("المهن المحفوظة:", weight="bold", color=ORANGE),
                    mihna_list_col,
                    ft.Container(height=16),
                    ft.OutlinedButton(
                        "العودة لحساب الضريبة",
                        on_click=show_dariba_maqtou3, width=360, height=46,
                        style=ft.ButtonStyle(color=ORANGE),
                    ),
                    back_btn(show_home),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12, expand=True,
            ))
            page.update()

        page.add(ft.Column(
            controls=[
                section_title("ضريبة الدخل المقطوع", ORANGE),
                ft.Divider(),
                ft.Text("ابحث عن المهنة:", weight="bold", color=ORANGE),
                search_f,
                suggestions_col,
                mihna_info,
                ft.Divider(),
                daily_f,
                calc_btn("احسب الضريبة", ORANGE, calc),
                results_col,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "⚙️ إدارة المهن (إضافة / تعديل / حذف)",
                    bgcolor="#BF360C", color="white",
                    width=360, height=46,
                    on_click=show_manage_mihna,
                ),
                ft.Container(height=6),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  3) ريع رؤوس الاموال المتداولة
    # ══════════════════════════════════════
    def show_rea3(e=None):
        page.controls.clear()

        currency_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="old", label="عملة قديمة"),
                 ft.Radio(value="new", label="عملة جديدة")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="old",
        )
        currency_note = ft.Text(
            "العملة القديمة = الأكبر  |  العملة الجديدة = القديمة ÷ 100",
            size=12, color="grey", italic=True, text_align="center",
        )

        bond_f = num_field("قيمة السند", hint="مثال: 1000000")

        dur_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="1year",  label="سنة واحدة"),
                 ft.Radio(value="custom", label="تحديد تاريخين")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="1year",
        )

        selected_dates = {"bond": None, "today": date.today()}
        date1_display = ft.Text("لم يتم الاختيار بعد", color="grey", size=14, italic=True)
        date2_display = ft.Text(
            f"التاريخ الحالي: {date.today().strftime('%Y-%m-%d')}",
            color=DARK_GREEN, size=14,
        )
        date_error = ft.Text("", color="red", size=13, visible=False)

        def on_bond_date_picked(e):
            if e.control.value:
                selected_dates["bond"] = e.control.value.date()
                date1_display.value  = f"تاريخ السند: {selected_dates['bond'].strftime('%Y-%m-%d')}"
                date1_display.color  = DARK_GREEN
                date1_display.italic = False
                date_error.visible   = False
            page.update()

        def on_today_date_picked(e):
            if e.control.value:
                selected_dates["today"] = e.control.value.date()
                date2_display.value = f"التاريخ الحالي: {selected_dates['today'].strftime('%Y-%m-%d')}"
                date_error.visible  = False
            page.update()

        bond_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=on_bond_date_picked,
        )
        today_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            value=datetime.today(),
            on_change=on_today_date_picked,
        )
        page.overlay.append(bond_date_picker)
        page.overlay.append(today_date_picker)

        def open_bond_picker(e):
            bond_date_picker.open = True
            page.update()

        def open_today_picker(e):
            today_date_picker.open = True
            page.update()

        dates_section = ft.Column(
            controls=[
                ft.Divider(),
                ft.Text("اختر تاريخ السند:", weight="bold", size=14),
                ft.Row([
                    ft.ElevatedButton("اختر التاريخ", bgcolor=TEAL, color="white",
                                      on_click=open_bond_picker, height=42),
                    date1_display,
                ], spacing=12),
                ft.Container(height=4),
                ft.Text("اختر التاريخ الحالي:", weight="bold", size=14),
                ft.Row([
                    ft.ElevatedButton("اختر التاريخ", bgcolor=TEAL, color="white",
                                      on_click=open_today_picker, height=42),
                    date2_display,
                ], spacing=12),
                date_error,
            ],
            visible=False, spacing=8,
        )
        results_col = ft.Column(spacing=10)

        def on_dur_change(e):
            dates_section.visible = (dur_rg.value == "custom")
            page.update()
        dur_rg.on_change = on_dur_change

        def _build_rea3_card(title_text, qima_orig, omla,
                              rasm, idara, faida,
                              tr=None, sana=None, ashhur=None, ayam=None,
                              rs=None, ra=None, rd=None,
                              is_multi=False):
            div = 100 if omla == "new" else 1

            def v(x):
                return math.ceil(x / div)

            total_nihai = v(math.ceil(tr + idara)) if is_multi else v(math.ceil(rasm + idara))
            omla_label  = "عملة قديمة" if omla == "old" else "عملة جديدة"
            subtitle = ft.Text(f"العملة المدخلة: {omla_label}", color="white70", size=13, italic=True)

            if is_multi:
                rows = [
                    ft.Text(title_text, weight="bold", size=17, color="white"),
                    subtitle,
                    result_row("قيمة السند",               math.ceil(qima_orig)),
                    result_row("الفائدة (10%)",             v(math.ceil(faida))),
                    result_row("الرسم الاساسي",             v(rasm)),
                    ft.Text(f"المدة: {sana} سنة  /  {ashhur} شهر  /  {ayam} يوم",
                            color="white", size=14),
                    ft.Divider(color="white54"),
                    result_row("رسم السنوات",               v(rs)),
                    result_row("رسم الاشهر",                v(ra)),
                    result_row("رسم الايام",                v(rd)),
                    result_row("مجموع الرسوم",              v(tr)),
                    result_row("رسم الادارة المحلية (10%)",  v(idara)),
                    ft.Divider(color="white54"),
                ]
            else:
                rows = [
                    ft.Text(title_text, weight="bold", size=17, color="white"),
                    subtitle,
                    result_row("قيمة السند",               math.ceil(qima_orig)),
                    result_row("الفائدة (10%)",             v(math.ceil(faida))),
                    result_row("الرسم (10% من الفائدة)",    v(rasm)),
                    result_row("رسم الادارة المحلية (10%)",  v(idara)),
                    ft.Divider(color="white54"),
                ]

            if omla == "old":
                rows.append(result_row("المجموع الكلي (عملة قديمة)", total_nihai, size=17))
                rows.append(result_row("المجموع الكلي (عملة جديدة)", math.ceil(total_nihai / 100), size=17))
            else:
                rows.append(result_row("المجموع الكلي (عملة جديدة)", total_nihai, size=17))

            return make_card(ft.Column(rows), TEAL)

        def calc(e):
            qima_raw = validate_number(bond_f, "قيمة السند")
            if qima_raw is None:
                page.update()
                return

            omla = currency_rg.value
            qima = qima_raw * 100 if omla == "new" else qima_raw

            faida = qima * 0.10
            rasm  = math.ceil(faida * 0.10)
            results_col.controls.clear()

            if dur_rg.value == "1year":
                idara = math.ceil(rasm * 0.10)
                results_col.controls.append(
                    _build_rea3_card(
                        "ريع راس المال - سنة واحدة",
                        qima_orig=qima_raw, omla=omla,
                        faida=faida, rasm=rasm, idara=idara,
                    )
                )
            else:
                if selected_dates["bond"] is None:
                    date_error.value   = "يرجى اختيار تاريخ السند"
                    date_error.visible = True
                    page.update()
                    return

                d1 = selected_dates["bond"]
                d2 = selected_dates["today"]

                if d2 <= d1:
                    date_error.value   = "يجب ان يكون التاريخ الحالي بعد تاريخ السند"
                    date_error.visible = True
                    page.update()
                    return

                date_error.visible = False
                delta  = (d2 - d1).days
                sana   = delta // 365
                ashhur = (delta % 365) // 30
                ayam   = (delta % 365) % 30
                rs     = rasm * sana
                ra     = math.ceil((rasm * ashhur) / 12)
                rd     = math.ceil((rasm * ayam) / 365)
                tr     = rs + ra + rd
                idara  = math.ceil(tr * 0.10)

                results_col.controls.append(
                    _build_rea3_card(
                        "ريع راس المال - مدة مخصصة",
                        qima_orig=qima_raw, omla=omla,
                        faida=faida, rasm=rasm, idara=idara,
                        tr=tr, sana=sana, ashhur=ashhur, ayam=ayam,
                        rs=rs, ra=ra, rd=rd, is_multi=True,
                    )
                )

            page.update()

        page.add(ft.Column(
            controls=[
                section_title("ريع رؤوس الاموال المتداولة", BLUE),
                ft.Divider(),
                ft.Text("نوع العملة المدخلة:", weight="bold", color=BLUE),
                currency_rg, currency_note,
                ft.Divider(),
                bond_f,
                ft.Text("مدة السند:", weight="bold"),
                dur_rg, dates_section,
                calc_btn("احسب", BLUE, calc),
                results_col,
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  4) الارباح الحقيقية
    # ══════════════════════════════════════
    def show_arbah(e=None):
        page.controls.clear()

        currency_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="new", label="عملة جديدة"),
                 ft.Radio(value="old", label="عملة قديمة")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="new",
        )
        income_f    = num_field("القيمة المراد حسابها", hint="مثال: 17000000")
        results_col = ft.Column(spacing=10)

        def calc(e):
            mablagh = validate_number(income_f, "القيمة")
            if mablagh is None:
                page.update()
                return

            omla    = currency_rg.value
            maffy   = SETTINGS["arbah_old_exempt"] if omla == "old" else SETTINGS["arbah_new_exempt"]
            sharaeh = SETTINGS["arbah_old_brackets"] if omla == "old" else SETTINGS["arbah_new_brackets"]
            rasm_idara_pct = SETTINGS["rasm_idara_pct"]

            results_col.controls.clear()

            if mablagh <= maffy:
                results_col.controls.append(make_card(
                    ft.Text(
                        f"المبلغ ({int(mablagh):,})\n"
                        f"ضمن الحد المعفى ({int(maffy):,})\n"
                        f"لا ضريبة مستحقة",
                        color="white", size=16, text_align="center",
                    ),
                    GREEN,
                ))
                page.update()
                return

            tafaseel, dariba_klia = calc_arbah_brackets(mablagh, sharaeh)
            rasm_idara  = math.ceil(dariba_klia * rasm_idara_pct)
            total_qabla = dariba_klia + rasm_idara
            total_nihai = math.ceil(total_qabla / 100) if omla == "old" else total_qabla

            rows = [
                ft.Text("الارباح الحقيقية - تفصيل الشرائح",
                        weight="bold", size=18, color="white"),
                result_row("المبلغ الكلي", math.ceil(mablagh)),
                result_row("الحد المعفى",  maffy),
                ft.Divider(color="white54"),
            ]

            for i, sh in enumerate(tafaseel, 1):
                upper_str = f"{int(sh['upper']):,}" if sh["upper"] != float("inf") else "فما فوق"
                rows.append(ft.Text(
                    f"الشريحة {i}  ({sh['pct']:.0f}%)  من {int(sh['lower']):,}  الى {upper_str}",
                    color="white70", size=13,
                ))
                rows.append(ft.Text(
                    f"    الوعاء: {int(sh['wia3']):,}  |  الضريبة: {int(sh['dariba']):,}",
                    color="white", size=14,
                ))

            rows += [
                ft.Divider(color="white54"),
                result_row("مجموع الضريبة", dariba_klia, size=17),
                result_row(f"رسم الادارة المحلية ({int(rasm_idara_pct * 100)}%)", rasm_idara, size=16),
            ]

            if omla == "old":
                rows.append(ft.Text(f"المجموع قبل التحويل: {int(total_qabla):,}", color="white70", size=14))
                rows.append(ft.Text("(مقسوم على 100 - تحويل للعملة الجديدة)", color="white60", size=13))

            rows.append(ft.Divider(color="white54"))
            rows.append(ft.Text(
                f"المجموع النهائي للضريبة: {int(total_nihai):,}",
                weight="bold", size=19, color="white",
            ))

            results_col.controls.append(make_card(ft.Column(rows), PURPLE))
            page.update()

        page.add(ft.Column(
            controls=[
                section_title("الارباح الحقيقية", PURPLE),
                ft.Divider(),
                ft.Text("نوع العملة:", weight="bold"),
                currency_rg,
                income_f,
                calc_btn("احسب", PURPLE, calc),
                results_col,
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  5) الإعدادات والنسب
    # ══════════════════════════════════════
    def show_settings(e=None):
        page.controls.clear()
        page.add(ft.Column(
            controls=[
                section_title("⚙️ الإعدادات والنسب", TEAL),
                ft.Divider(),
                ft.Text("اختر القسم الذي تريد تعديله:", weight="bold", color=TEAL),
                ft.Container(height=8),
                menu_btn("إعدادات تحققات الدخل المقطوع", GREEN,   lambda e: show_settings_maqtou3()),
                ft.Container(height=8),
                menu_btn("إعدادات ضريبة الدخل المقطوع",  ORANGE,  lambda e: show_settings_dariba()),
                ft.Container(height=8),
                menu_btn("إعدادات الارباح الحقيقية",      PURPLE,  lambda e: show_settings_arbah()),
                ft.Container(height=8),
                menu_btn("إعدادات عامة",                  TEAL,    lambda e: show_settings_general()),
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    def _brackets_editor(brackets_key, exempt_key, title, color, back_fn):
        """محرر الشرائح العام"""
        page.controls.clear()
        save_msg = ft.Text("", color="green", size=14)
        exempt_f = num_field("حد الإعفاء", value=int(SETTINGS[exempt_key]))

        brackets_col = ft.Column(spacing=6)

        def build_bracket_row(idx, bracket):
            lower = bracket[0]
            upper = bracket[1] if bracket[1] is not None else ""
            nisba = int(bracket[2] * 100)
            lower_f = num_field("من", value=int(lower), width=100)
            upper_f = ft.TextField(
                label="إلى", value=str(upper) if upper != "" else "∞",
                hint_text="∞ = بلا حد",
                border_radius=10, text_size=14, width=100,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=10),
            )
            nisba_f = num_field("النسبة %", value=nisba, width=90)

            def make_delete(i):
                def do_delete(e):
                    SETTINGS[brackets_key].pop(i)
                    save_data(SETTINGS, page)
                    _brackets_editor(brackets_key, exempt_key, title, color, back_fn)
                return do_delete

            return ft.Container(
                content=ft.Column([
                    ft.Text(f"الشريحة {idx+1}", size=13, color="grey"),
                    ft.Row([lower_f, upper_f, nisba_f,
                            ft.ElevatedButton("حذف", bgcolor=RED, color="white",
                                              on_click=make_delete(idx), height=40)
                            ], spacing=6),
                ]),
                bgcolor="white", padding=8, border_radius=10,
                margin=ft.margin.symmetric(vertical=3),
                data={"lower_f": lower_f, "upper_f": upper_f, "nisba_f": nisba_f},
            )

        bracket_rows = [build_bracket_row(i, b) for i, b in enumerate(SETTINGS[brackets_key])]
        for r in bracket_rows:
            brackets_col.controls.append(r)

        def save_brackets(e):
            try:
                new_exempt = float(exempt_f.value or 0)
                new_brackets = []
                for row in brackets_col.controls:
                    d = row.data
                    lower = float(d["lower_f"].value or 0)
                    upper_raw = (d["upper_f"].value or "").strip()
                    upper = None if upper_raw in ["", "∞", "inf"] else float(upper_raw)
                    nisba = float(d["nisba_f"].value or 0) / 100
                    new_brackets.append([lower, upper, nisba])
                SETTINGS[exempt_key]    = new_exempt
                SETTINGS[brackets_key] = new_brackets
                save_data(SETTINGS, page)
                save_msg.value = "✅ تم حفظ الشرائح بنجاح"
                save_msg.color = "green"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "red"
            page.update()

        def add_bracket(e):
            SETTINGS[brackets_key].append([0, None, 0.10])
            save_data(SETTINGS, page)
            _brackets_editor(brackets_key, exempt_key, title, color, back_fn)

        page.add(ft.Column(
            controls=[
                section_title(f"⚙️ {title}", color),
                ft.Divider(),
                exempt_f,
                ft.Divider(),
                ft.Text("الشرائح الضريبية:", weight="bold", color=color),
                ft.Text("(من / إلى / النسبة%) - اكتب ∞ في حقل إلى للشريحة الأخيرة",
                        size=12, color="grey", italic=True),
                brackets_col,
                ft.ElevatedButton("+ إضافة شريحة جديدة", bgcolor=color, color="white",
                                  on_click=add_bracket, width=360, height=44),
                ft.Divider(),
                calc_btn("💾 حفظ الشرائح", color, save_brackets),
                save_msg,
                ft.Container(height=16),
                ft.OutlinedButton(
                    "العودة للإعدادات",
                    on_click=lambda e: back_fn(), width=360, height=46,
                    style=ft.ButtonStyle(color=color),
                ),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    def show_settings_maqtou3():
        page.controls.clear()
        save_msg = ft.Text("", color="green", size=14)
        nafaqat_f = num_field("نسبة النفقات %",  value=SETTINGS["nafaqat_default"])
        idara_f   = num_field("نسبة الادارة %",   value=SETTINGS["idara_default"])
        rawatib_f = num_field("نسبة الرواتب %",   value=SETTINGS["rawatib_default"])

        def save(e):
            try:
                SETTINGS["nafaqat_default"] = float(nafaqat_f.value or 3)
                SETTINGS["idara_default"]   = float(idara_f.value   or 10)
                SETTINGS["rawatib_default"] = float(rawatib_f.value or 10)
                save_data(SETTINGS, page)
                save_msg.value = "✅ تم الحفظ"
                save_msg.color = "green"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "red"
            page.update()

        page.add(ft.Column(
            controls=[
                section_title("⚙️ إعدادات تحققات الدخل المقطوع", GREEN),
                ft.Divider(),
                nafaqat_f, idara_f, rawatib_f,
                calc_btn("💾 حفظ", GREEN, save),
                save_msg,
                ft.Container(height=16),
                ft.OutlinedButton("العودة للإعدادات", on_click=lambda e: show_settings(),
                                  width=360, height=46, style=ft.ButtonStyle(color=GREEN)),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    def show_settings_dariba():
        _brackets_editor("maqtou3_brackets", "maqtou3_exempt",
                         "إعدادات ضريبة الدخل المقطوع", ORANGE, show_settings)

    def show_settings_arbah():
        page.controls.clear()
        save_msg = ft.Text("", color="green", size=14)
        omla_rg = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="new", label="عملة جديدة"),
                ft.Radio(value="old", label="عملة قديمة"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            value="new",
        )
        edit_btn = ft.ElevatedButton(
            "تعديل شرائح العملة المختارة", bgcolor=PURPLE, color="white",
            width=360, height=46,
        )

        def go_edit(e):
            if omla_rg.value == "new":
                _brackets_editor("arbah_new_brackets", "arbah_new_exempt",
                                 "أرباح - عملة جديدة", PURPLE, show_settings_arbah)
            else:
                _brackets_editor("arbah_old_brackets", "arbah_old_exempt",
                                 "أرباح - عملة قديمة", PURPLE, show_settings_arbah)

        edit_btn.on_click = go_edit

        page.add(ft.Column(
            controls=[
                section_title("⚙️ إعدادات الارباح الحقيقية", PURPLE),
                ft.Divider(),
                ft.Text("اختر العملة:", weight="bold"),
                omla_rg,
                edit_btn,
                save_msg,
                ft.Container(height=16),
                ft.OutlinedButton("العودة للإعدادات", on_click=lambda e: show_settings(),
                                  width=360, height=46, style=ft.ButtonStyle(color=PURPLE)),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    def show_settings_general():
        page.controls.clear()
        save_msg = ft.Text("", color="green", size=14)
        rasm_f = num_field("رسم الادارة المحلية %", value=int(SETTINGS["rasm_idara_pct"] * 100))

        def save(e):
            try:
                SETTINGS["rasm_idara_pct"] = float(rasm_f.value or 10) / 100
                save_data(SETTINGS, page)
                save_msg.value = "✅ تم الحفظ"
                save_msg.color = "green"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "red"
            page.update()

        def reset(e):
            for key, val in DEFAULT_SETTINGS.items():
                if key != "mihna_list":
                    SETTINGS[key] = val
            save_data(SETTINGS, page)
            save_msg.value = "✅ تم إعادة التعيين للقيم الافتراضية"
            save_msg.color = "orange"
            page.update()
            show_settings_general()

        page.add(ft.Column(
            controls=[
                section_title("⚙️ إعدادات عامة", TEAL),
                ft.Divider(),
                rasm_f,
                calc_btn("💾 حفظ", TEAL, save),
                ft.OutlinedButton("🔄 إعادة تعيين كل الإعدادات للافتراضية",
                                  on_click=reset, width=360, height=46,
                                  style=ft.ButtonStyle(color=RED)),
                save_msg,
                ft.Container(height=16),
                ft.OutlinedButton("العودة للإعدادات", on_click=lambda e: show_settings(),
                                  width=360, height=46, style=ft.ButtonStyle(color=TEAL)),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    show_home()


if __name__ == "__main__":
    ft.app(target=main)
