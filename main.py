"""
حاسبة الدخل - نسخة حديثة
تحسينات التصميم:
  1. Material You / M3 مع دعم الوضع الليلي
  2. AppBar حديث مع زر الإعدادات
  3. ListTile بدلاً من أزرار القائمة
  4. SegmentedButton بدلاً من RadioGroup
  5. TextField مع أيقونات
  6. Card مع ظلال ناعمة للنتائج
  7. Material Icons بدلاً من الإيموجي
  8. ألوان هادئة للنتائج
"""

import flet as ft
import math
import json
import os
from datetime import datetime, date

# ══════════════════════════════════════
#  ثوابت الحماية
# ══════════════════════════════════════
MAX_VALUE        = 999_999_999_999
MAX_BRACKETS     = 20
MAX_MIHNA        = 500
MAX_STR_LEN      = 200
MAX_SEARCH_QUERY = 100


# ══════════════════════════════════════
#  الإعدادات الافتراضية
# ══════════════════════════════════════
DEFAULT_SETTINGS = {
    "nafaqat_default": 3,
    "idara_default": 10,
    "rawatib_default": 10,
    "rasm_idara_pct": 0.10,
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
    "rea3_faida_pct": 10,
    "rea3_rasm_pct":  10,
    "rea3_idara_pct": 10,
    "mihna_list": [],
    "dark_mode": False,
}


# ══════════════════════════════════════
#  دوال التحقق والتنظيف
# ══════════════════════════════════════
def _is_valid_bracket(b):
    if not isinstance(b, list) or len(b) != 3:
        return False
    try:
        lower = float(b[0])
        nisba = float(b[2])
        if lower < 0 or not (0 < nisba <= 1):
            return False
        if b[1] is not None:
            upper = float(b[1])
            if upper <= lower:
                return False
    except (TypeError, ValueError):
        return False
    return True


def _sanitize_brackets(raw, default_key):
    if not isinstance(raw, list) or len(raw) == 0:
        return DEFAULT_SETTINGS[default_key]
    valid = [b for b in raw if _is_valid_bracket(b)]
    if not valid:
        return DEFAULT_SETTINGS[default_key]
    result = []
    for b in valid[:MAX_BRACKETS]:
        result.append([
            float(b[0]),
            float(b[1]) if b[1] is not None else None,
            float(b[2]),
        ])
    return result


def _sanitize_mihna_list(raw):
    if not isinstance(raw, list):
        return []
    clean = []
    for m in raw[:MAX_MIHNA]:
        try:
            if not isinstance(m, dict):
                continue
            ism   = str(m.get("ism",   "")).strip()[:MAX_STR_LEN]
            ramz  = int(float(m.get("ramz",  0)))
            ayam  = int(float(m.get("ayam",  0)))
            nisba = float(m.get("nisba", 0))
            if not ism or ramz <= 0 or ayam <= 0 or not (0 < nisba <= 100):
                continue
            clean.append({"ism": ism, "ramz": ramz, "ayam": ayam, "nisba": nisba})
        except (TypeError, ValueError, KeyError):
            continue
    return clean


def _sanitize_float(val, default, min_val=0, max_val=MAX_VALUE):
    try:
        v = float(val)
        if not math.isfinite(v):
            return default
        return max(min_val, min(max_val, v))
    except (TypeError, ValueError):
        return default


# ══════════════════════════════════════
#  تحميل وحفظ البيانات
# ══════════════════════════════════════
def load_data(page):
    data_file = _get_data_file()
    if not os.path.exists(data_file):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return DEFAULT_SETTINGS.copy()
        merged = DEFAULT_SETTINGS.copy()
        merged.update(raw)
        merged["nafaqat_default"] = _sanitize_float(merged.get("nafaqat_default", 3),   3,  0, 100)
        merged["idara_default"]   = _sanitize_float(merged.get("idara_default",   10), 10,  0, 100)
        merged["rawatib_default"] = _sanitize_float(merged.get("rawatib_default", 10), 10,  0, 100)
        merged["rasm_idara_pct"]  = _sanitize_float(merged.get("rasm_idara_pct",  0.10), 0.10, 0, 1)
        merged["rea3_faida_pct"]  = _sanitize_float(merged.get("rea3_faida_pct", 10), 10, 0, 100)
        merged["rea3_rasm_pct"]   = _sanitize_float(merged.get("rea3_rasm_pct",  10), 10, 0, 100)
        merged["rea3_idara_pct"]  = _sanitize_float(merged.get("rea3_idara_pct", 10), 10, 0, 100)
        merged["arbah_old_exempt"] = _sanitize_float(merged.get("arbah_old_exempt", 3000000), 3000000, 0)
        merged["arbah_new_exempt"] = _sanitize_float(merged.get("arbah_new_exempt", 30000),   30000,   0)
        merged["maqtou3_exempt"]   = _sanitize_float(merged.get("maqtou3_exempt",   30000),   30000,   0)
        merged["arbah_old_brackets"] = _sanitize_brackets(merged.get("arbah_old_brackets"), "arbah_old_brackets")
        merged["arbah_new_brackets"] = _sanitize_brackets(merged.get("arbah_new_brackets"), "arbah_new_brackets")
        merged["maqtou3_brackets"]   = _sanitize_brackets(merged.get("maqtou3_brackets"),   "maqtou3_brackets")
        merged["mihna_list"] = _sanitize_mihna_list(merged.get("mihna_list", []))
        return merged
    except Exception as ex:
        print(f"[load_data] خطأ: {ex}")
        return DEFAULT_SETTINGS.copy()


def save_data(data, page):
    data_file = _get_data_file()
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print(f"[save_data] خطأ: {ex}")


def _get_data_file():
    app_storage = os.getenv("FLET_APP_STORAGE_DATA")
    if not app_storage:
        app_storage = os.path.join(os.path.expanduser("~"), ".hasiba")
    try:
        os.makedirs(app_storage, exist_ok=True)
    except Exception:
        app_storage = os.path.expanduser("~")
    return os.path.join(app_storage, "hasiba_data.json")


# ══════════════════════════════════════
#  دوال الحساب الآمنة
# ══════════════════════════════════════
def safe_ceil(val):
    try:
        if not math.isfinite(val):
            return 0
        return math.ceil(val)
    except (TypeError, OverflowError):
        return 0


def calc_maqtou3_tax(ribh_safi, brackets, exempt):
    tafaseel    = []
    dariba_klia = 0
    if not brackets or ribh_safi <= 0:
        return tafaseel, dariba_klia
    for bracket in brackets:
        try:
            lower     = float(bracket[0])
            nisba     = float(bracket[2])
            upper_val = float(bracket[1]) if bracket[1] is not None else float("inf")
            if not math.isfinite(lower) or not (0 < nisba <= 1):
                continue
            if ribh_safi <= lower:
                break
            wia3 = min(ribh_safi, upper_val) - lower
            if wia3 <= 0:
                continue
            if lower <= 1:
                wia3_taxable = max(0, min(ribh_safi, upper_val) - exempt)
            else:
                wia3_taxable = wia3
            sh_d = safe_ceil(round(wia3_taxable * nisba, 8)) if wia3_taxable > 0 else 0
            dariba_klia += sh_d
            tafaseel.append({
                "pct": nisba * 100, "lower": lower, "upper": upper_val,
                "wia3": wia3, "wia3_taxable": wia3_taxable, "dariba": sh_d,
            })
        except (TypeError, ValueError, IndexError):
            continue
    return tafaseel, dariba_klia


def calc_arbah_brackets(mablagh, brackets):
    tafaseel    = []
    dariba_klia = 0
    if not brackets or mablagh <= 0:
        return tafaseel, dariba_klia
    for bracket in brackets:
        try:
            lower     = float(bracket[0])
            nisba     = float(bracket[2])
            upper_val = float(bracket[1]) if bracket[1] is not None else float("inf")
            if not math.isfinite(lower) or not (0 < nisba <= 1):
                continue
            if mablagh <= lower:
                break
            wia3 = min(mablagh, upper_val) - lower
            if wia3 <= 0:
                continue
            sh_d = safe_ceil(round(wia3 * nisba, 8))
            dariba_klia += sh_d
            tafaseel.append({
                "pct": nisba * 100, "lower": lower, "upper": upper_val,
                "wia3": wia3, "dariba": sh_d,
            })
        except (TypeError, ValueError, IndexError):
            continue
    return tafaseel, dariba_klia


# ══════════════════════════════════════
#  دوال UI مساعدة حديثة
# ══════════════════════════════════════
def result_row(label, value, size=15):
    try:
        val_int = int(value)
    except (TypeError, ValueError, OverflowError):
        val_int = 0
    return ft.Row([
        ft.Text(label, size=size - 1, color=None),
        ft.Text(f"{val_int:,}", size=size, weight="bold", color=None),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def result_row_white(label, value, size=15):
    """نسخة بيضاء لبطاقات ملونة"""
    try:
        val_int = int(value)
    except (TypeError, ValueError, OverflowError):
        val_int = 0
    return ft.Row([
        ft.Text(label, size=size - 1, color="#ffffffcc"),
        ft.Text(f"{val_int:,}", size=size, weight="bold", color="white"),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def make_result_card(content, color=None, elevation=2):
    """بطاقة نتائج حديثة"""
    if color:
        return ft.Container(
            content=content,
            bgcolor=color,
            padding=ft.padding.all(16),
            border_radius=16,
            margin=ft.margin.symmetric(vertical=5),
        )
    return ft.Card(
        content=ft.Container(
            content=content,
            padding=ft.padding.all(16),
        ),
        elevation=elevation,
        margin=ft.margin.symmetric(vertical=5),
    )


def num_field(label, value="", hint="", width=None, icon=None, read_only=False):
    kwargs = dict(
        label=label,
        value=str(value),
        hint_text=hint,
        keyboard_type=ft.KeyboardType.NUMBER,
        border=ft.InputBorder.OUTLINE,
        border_radius=14,
        text_size=15,
        filled=True,
        read_only=read_only,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
    )
    if width:
        kwargs["width"] = width
    if icon:
        kwargs["prefix_icon"] = icon
    return ft.TextField(**kwargs)


def text_field(label, value="", hint="", width=None, icon=None):
    kwargs = dict(
        label=label,
        value=str(value),
        hint_text=hint,
        border=ft.InputBorder.OUTLINE,
        border_radius=14,
        text_size=15,
        filled=True,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
    )
    if width:
        kwargs["width"] = width
    if icon:
        kwargs["prefix_icon"] = icon
    return ft.TextField(**kwargs)


def validate_number(field, label="القيمة", min_val=0.001, max_val=MAX_VALUE,
                    allow_zero=False):
    raw = (field.value or "").strip()
    if not raw:
        field.error_text = f"يرجى إدخال {label}"
        field.update()
        return None
    try:
        val = float(raw)
    except ValueError:
        field.error_text = "أرقام فقط"
        field.update()
        return None
    if not math.isfinite(val):
        field.error_text = "رقم غير صالح"
        field.update()
        return None
    if allow_zero:
        if val < 0:
            field.error_text = "يجب أن يكون صفراً أو أكبر"
            field.update()
            return None
    else:
        if val <= 0:
            field.error_text = "يجب أن يكون أكبر من صفر"
            field.update()
            return None
    if val > max_val:
        field.error_text = f"الحد الأقصى {int(max_val):,}"
        field.update()
        return None
    field.error_text = None
    field.update()
    return val


def section_divider(text):
    return ft.Row([
        ft.Container(height=1, expand=True, bgcolor="#E0E0E0"),
        ft.Text(f"  {text}  ", size=12, color=None),
        ft.Container(height=1, expand=True, bgcolor="#E0E0E0"),
    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)


def primary_btn(label, handler, icon=None, width=360):
    return ft.FilledButton(
        content=ft.Row([
            ft.Icon(icon, size=18) if icon else ft.Container(width=0),
            ft.Text(label, size=15, weight="bold"),
        ], tight=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        on_click=handler,
        width=width,
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
    )


def tonal_btn(label, handler, icon=None, width=360):
    return ft.FilledTonalButton(
        content=ft.Row([
            ft.Icon(icon, size=18) if icon else ft.Container(width=0),
            ft.Text(label, size=14),
        ], tight=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        on_click=handler,
        width=width,
        height=46,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )


# ══════════════════════════════════════
#  دالة main
# ══════════════════════════════════════
def main(page: ft.Page):
    page.title      = "حاسبة الدخل"
    page.rtl        = True
    page.theme = ft.Theme(
        color_scheme_seed="#00695C",
        use_material3=True,
    )
    page.padding = ft.padding.only(left=16, right=16, top=0, bottom=16)
    page.window_width  = 420
    page.window_height = 820

    SETTINGS = load_data(page)

    # ── تتبع الصفحة الحالية لزر الرجوع في Android ──
    nav_stack = []

    def push_page(fn):
        """أضف صفحة للمكدس"""
        nav_stack.append(fn)

    def go_back(e=None):
        """زر الرجوع في Android"""
        if len(nav_stack) > 1:
            nav_stack.pop()
            nav_stack[-1]()
        else:
            nav_stack.clear()
            show_home()

    def handle_back(e):
        """يمنع الخروج من التطبيق ويتنقل للخلف بدلاً من ذلك"""
        if len(nav_stack) > 1:
            nav_stack.pop()
            nav_stack[-1]()
        else:
            def exit_app(ev):
                page.window_close()
            confirm_dialog(
                "الخروج",
                "هل تريد الخروج من التطبيق؟",
                exit_app,
            )
        # منع الخروج الافتراضي
        if hasattr(e, 'prevent_default'):
            e.prevent_default()

    page.on_back_button_click = handle_back
    page.theme_mode = ft.ThemeMode.DARK if SETTINGS.get("dark_mode", False) else ft.ThemeMode.LIGHT

    # ── فهرس البحث ──
    _mihna_index = {}

    def rebuild_index():
        _mihna_index.clear()
        try:
            for m in SETTINGS.get("mihna_list", []):
                if not isinstance(m, dict):
                    continue
                _mihna_index[str(m.get("ramz", ""))] = m
                for word in str(m.get("ism", "")).lower().split():
                    if word:
                        _mihna_index.setdefault(word, [])
                        if isinstance(_mihna_index[word], list):
                            _mihna_index[word].append(m)
        except Exception as ex:
            print(f"[rebuild_index] {ex}")

    def search_mihna(query):
        try:
            query = str(query).strip().lower()[:MAX_SEARCH_QUERY]
            if not query:
                return []
            seen, results = set(), []
            for m in SETTINGS.get("mihna_list", []):
                if not isinstance(m, dict):
                    continue
                key = m.get("ramz")
                if key in seen:
                    continue
                if query in str(m.get("ism", "")).lower() or query in str(m.get("ramz", "")):
                    seen.add(key)
                    results.append(m)
                    if len(results) >= 5:
                        break
            return results
        except Exception as ex:
            print(f"[search_mihna] {ex}")
            return []

    rebuild_index()

    def confirm_dialog(title, message, on_confirm):
        def close(e):
            dlg.open = False
            page.update()
        def confirm(e):
            dlg.open = False
            page.update()
            on_confirm()
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="#E65100", size=24),
                ft.Text(title, size=16, weight="bold"),
            ], spacing=8),
            content=ft.Text(message, size=14),
            actions=[
                ft.TextButton("الغاء", on_click=close,
                              style=ft.ButtonStyle(color="#6B7280")),
                ft.FilledButton("تاكيد", on_click=confirm,
                                style=ft.ButtonStyle(
                                    bgcolor="#C62828",
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                )),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ══════════════════════════════════════
    #  AppBar مشترك
    # ══════════════════════════════════════
    def make_appbar(title, show_back=True, show_settings_icon=False, back_fn=None):
        """ينشئ AppBar لاستخدامه في View"""
        actions = []
        if show_settings_icon:
            actions.append(
                ft.IconButton(
                    ft.Icons.SETTINGS_OUTLINED,
                    on_click=show_settings,
                    tooltip="الإعدادات",
                    icon_color="white",
                )
            )
        back_handler = back_fn if back_fn else show_home
        return ft.AppBar(
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                on_click=back_handler,
                icon_color="white",
                tooltip="رجوع",
            ) if show_back else None,
            leading_width=48,
            title=ft.Text(title, size=18, weight="bold", color="white"),
            center_title=True,
            bgcolor="#00695C",
            elevation=0,
            actions=actions,
        )

    def set_appbar(title, show_back=True, show_settings_icon=False, back_fn=None):
        """للتوافق مع الكود القديم"""
        page.appbar = make_appbar(title, show_back, show_settings_icon, back_fn)

    def push_view(route, controls, title, show_back=True, back_fn=None,
                  show_settings_icon=False, scroll=ft.ScrollMode.AUTO):
        """يضيف View جديد مع دعم زر الرجوع في Android"""
        back_handler = back_fn if back_fn else show_home

        def on_confirm_pop(e):
            e.confirm = True
            back_handler()
            page.update()

        view = ft.View(
            route=route,
            controls=[
                ft.Column(
                    controls=controls,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    expand=True,
                    scroll=scroll,
                )
            ],
            appbar=make_appbar(title, show_back, show_settings_icon, back_fn),
            padding=ft.padding.only(left=16, right=16, top=0, bottom=16),
            bgcolor=None,
            scroll=None,
            can_pop=show_back,
            on_confirm_pop=on_confirm_pop if show_back else None,
            rtl=True,
        )
        page.views.append(view)
        page.update()

    def pop_view():
        """يرجع للـ View السابق"""
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    def on_view_pop(e):
        """معالج زر الرجوع في Android"""
        if len(nav_stack) > 1:
            nav_stack.pop()
            nav_stack[-1]()
        page.update()

    page.on_view_pop = on_view_pop

    # ══════════════════════════════════════
    #  الصفحة الرئيسية
    # ══════════════════════════════════════
    def show_home(e=None):
        page.controls.clear()
        nav_stack.clear()
        nav_stack.append(show_home)
        page.appbar = ft.AppBar(
            title=ft.Text("حاسبة الدخل", size=20, weight="bold", color="white"),
            center_title=True,
            bgcolor="#00695C",
            elevation=0,
            actions=[
                ft.IconButton(
                    ft.Icons.SETTINGS_OUTLINED,
                    icon_color="white",
                    on_click=show_settings,
                    tooltip="الإعدادات",
                )
            ],
        )

        def menu_tile(title, subtitle, icon, color, handler):
            return ft.Card(
                content=ft.ListTile(
                    leading=ft.Container(
                        content=ft.Icon(icon, color="white", size=22),
                        bgcolor=color,
                        width=44, height=44,
                        border_radius=12,
                        alignment=ft.Alignment.CENTER,
                    ),
                    title=ft.Text(title, weight="bold", size=14, color=None),
                    subtitle=ft.Text(subtitle, size=12,
                                     color=None),
                    trailing=ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                     size=14, color=None),
                    on_click=handler,
                ),
                elevation=1,
                margin=ft.margin.symmetric(vertical=4),
                shape=ft.RoundedRectangleBorder(radius=16),
            )

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CALCULATE_ROUNDED,
                                color="white", size=40),
                        ft.Text("حاسبة الدخل", size=22, weight="bold",
                                color="white"),
                        ft.Text("اختر العملية المراد حسابها",
                                size=13, color="#ffffffcc"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       spacing=6),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=["#00695C", "#004D40"],
                    ),
                    padding=ft.padding.symmetric(horizontal=24, vertical=28),
                    border_radius=20,
                    width=400,
                ),
                ft.Container(height=16),
                menu_tile("تحققات الدخل المقطوع",
                          "احتساب الدخل مع النفقات والرواتب",
                          ft.Icons.RECEIPT_LONG_OUTLINED, "#2E7D32", show_maqtou3),
                menu_tile("ضريبة الدخل المقطوع",
                          "حساب الضريبة حسب المهنة",
                          ft.Icons.WORK_OUTLINE_ROUNDED, "#E65100", show_dariba_maqtou3),
                menu_tile("ريع رؤوس الاموال المتداولة",
                          "حساب ريع السندات والأوراق المالية",
                          ft.Icons.TRENDING_UP_ROUNDED, "#1565C0", show_rea3),
                menu_tile("الارباح الحقيقية",
                          "احتساب ضريبة الأرباح بالشرائح",
                          ft.Icons.ACCOUNT_BALANCE_OUTLINED, "#6A1B9A", show_arbah),
                ft.Container(height=8),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        ))
        page.update()

    # ══════════════════════════════════════
    #  1) حساب تحققات الدخل المقطوع
    # ══════════════════════════════════════
    def show_maqtou3(e=None):
        page.controls.clear()
        push_page(show_maqtou3)
        set_appbar("تحققات الدخل المقطوع")

        def fmt(v):
            try:
                fv = float(v)
                return str(int(fv)) if fv == int(fv) else str(fv)
            except Exception:
                return str(v)

        income_f  = num_field("القيمة المراد حسابها",
                               hint="مثال: 500,000",
                               icon=ft.Icons.MONETIZATION_ON_OUTLINED)
        nafaqat_f = num_field("النفقات %",
                               value=fmt(SETTINGS["nafaqat_default"]), width=110, read_only=True)
        idara_f   = num_field("إدارة محلية %",
                               value=fmt(SETTINGS["idara_default"]),   width=110, read_only=True)
        rawatib_f = num_field("رواتب وأجور %",
                               value=fmt(SETTINGS["rawatib_default"]), width=110, read_only=True)

        years_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value="1", label=ft.Text("سنة واحدة"),
                           icon=ft.Icon(ft.Icons.LOOKS_ONE_OUTLINED)),
                ft.Segment(value="2", label=ft.Text("سنتين"),
                           icon=ft.Icon(ft.Icons.LOOKS_TWO_OUTLINED)),
            ],
            selected=["1"],
            allow_multiple_selection=False,
        )
        mult_dd = ft.Dropdown(
            label="مضاعف السنة الثانية",
            value="1",
            visible=False,
            border_radius=14,
            filled=True,
            options=[ft.DropdownOption(key=str(i), text=f"x {i}")
                     for i in range(1, 6)],
        )
        results_col = ft.Column(spacing=8)

        def on_seg_change(e):
            mult_dd.visible = ("2" in years_seg.selected)
            page.update()
        years_seg.on_change = on_seg_change

        def calc(e):
            val = validate_number(income_f, "القيمة")
            if val is None:
                page.update()
                return
            np_r = _sanitize_float(nafaqat_f.value, SETTINGS["nafaqat_default"], 0, 100) / 100
            ip_r = _sanitize_float(idara_f.value,   SETTINGS["idara_default"],   0, 100) / 100
            rp_r = _sanitize_float(rawatib_f.value, SETTINGS["rawatib_default"], 0, 100) / 100

            d1 = safe_ceil(val)
            n1 = safe_ceil(d1 * np_r)
            i1 = safe_ceil(d1 * ip_r)
            r1 = safe_ceil(d1 * rp_r)
            t1 = d1 + n1 + i1 + r1

            results_col.controls.clear()

            # بطاقة السنة الأولى
            results_col.controls.append(make_result_card(ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOOKS_ONE_ROUNDED, color="#2E7D32", size=20),
                    ft.Text("السنة الأولى", weight="bold", size=16,
                            color="#2E7D32"),
                ], spacing=6),
                ft.Divider(height=12),
                result_row("الدخل المقطوع", d1),
                result_row("النفقات", n1),
                result_row("الادارة", i1),
                result_row("الرواتب", r1),
                ft.Divider(height=12),
                ft.Row([
                    ft.Text("المجموع", weight="bold", size=15),
                    ft.Text(f"{t1:,}", weight="bold", size=17,
                            color="#2E7D32"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ])))

            grand = t1
            if "2" in years_seg.selected:
                try:
                    mult = int(mult_dd.value or 1)
                    mult = max(1, min(5, mult))
                except (TypeError, ValueError):
                    mult = 1
                d2 = safe_ceil(d1 * mult)
                n2 = safe_ceil(d2 * np_r)
                i2 = safe_ceil(d2 * ip_r)
                r2 = safe_ceil(d2 * rp_r)
                t2 = d2 + n2 + i2 + r2
                grand += t2
                results_col.controls.append(make_result_card(ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.LOOKS_TWO_ROUNDED, color="#1565C0", size=20),
                        ft.Text("السنة الثانية", weight="bold", size=16,
                                color="#1565C0"),
                    ], spacing=6),
                    ft.Divider(height=12),
                    result_row("الدخل المقطوع", d2),
                    result_row("النفقات", n2),
                    result_row("الادارة", i2),
                    result_row("الرواتب", r2),
                    ft.Divider(height=12),
                    ft.Row([
                        ft.Text("المجموع", weight="bold", size=15),
                        ft.Text(f"{t2:,}", weight="bold", size=17,
                                color="#1565C0"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ])))

            # بطاقة الإجمالي
            if "2" in years_seg.selected:
                results_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SUMMARIZE_ROUNDED, color="white", size=22),
                            ft.Column([
                                ft.Text("المجموع النهائي", color="#ffffffcc", size=13),
                                ft.Text(f"{grand:,}", color="white",
                                        size=22, weight="bold"),
                            ], spacing=2),
                        ], spacing=14),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=["#C62828", "#B71C1C"],
                        ),
                        padding=ft.padding.symmetric(horizontal=20, vertical=18),
                        border_radius=16,
                        margin=ft.margin.symmetric(vertical=5),
                    )
                )
            page.update()

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.PERCENT_ROUNDED,
                                        color="#00695C", size=18),
                                ft.Text("النسب", weight="bold", size=14),
                            ], spacing=8),
                            ft.Container(height=4),
                            ft.Row([nafaqat_f, idara_f],
                                   alignment=ft.MainAxisAlignment.CENTER,
                                   spacing=8),
                            ft.Row([rawatib_f],
                                   alignment=ft.MainAxisAlignment.CENTER),
                        ], spacing=8),
                        padding=ft.padding.all(16),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=16),
                ),
                ft.Container(height=4),
                income_f,
                ft.Container(height=4),
                ft.Text("عدد السنوات", size=13,
                        color=None),
                years_seg,
                mult_dd,
                ft.Container(height=4),
                primary_btn("احسب", calc,
                            icon=ft.Icons.CALCULATE_ROUNDED),
                ft.Container(height=4),
                results_col,
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10, expand=True, scroll=ft.ScrollMode.AUTO,
        ))
        page.update()

    # ══════════════════════════════════════
    #  2) ضريبة الدخل المقطوع
    # ══════════════════════════════════════
    def show_dariba_maqtou3(e=None):
        page.controls.clear()
        push_page(show_dariba_maqtou3)
        set_appbar("ضريبة الدخل المقطوع")

        search_f        = text_field("ابحث باسم أو رمز المهنة",
                                     hint="مثال: محامي أو 101",
                                     icon=ft.Icons.SEARCH_ROUNDED)
        suggestions_col = ft.ListView(spacing=4, expand=False, visible=False)
        selected_mihna  = {"data": None}
        mihna_info      = ft.Container(visible=False)
        daily_f         = num_field("الدخل اليومي",
                                    hint="مثال: 50,000",
                                    icon=ft.Icons.TODAY_OUTLINED)
        results_col     = ft.Column(spacing=8)

        def update_suggestions(e):
            try:
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
                            def handler(ev):
                                select_mihna(mihna)
                            return handler
                        try:
                            suggestions_col.controls.append(
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.WORK_OUTLINE_ROUNDED,
                                                    color="#00695C"),
                                    title=ft.Text(f"{m['ism']}  ({m['ramz']})",
                                                  size=14, weight="bold"),
                                    subtitle=ft.Text(
                                        f"أيام: {int(m.get('ayam',0))}  |  ربح: {m.get('nisba',0)}%",
                                        size=12),
                                    on_click=make_handler(m),
                                )
                            )
                        except (KeyError, TypeError):
                            continue
                else:
                    suggestions_col.visible = False
            except Exception as ex:
                print(f"[update_suggestions] {ex}")
            suggestions_col.update()

        search_f.on_change = update_suggestions

        def select_mihna(m):
            try:
                selected_mihna["data"] = m
                search_f.value         = f"{m['ism']} ({m['ramz']})"
                search_f.error_text    = None
                suggestions_col.visible = False
                mihna_info.content = ft.Card(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        color="white", size=18),
                                ft.Text("المهنة المختارة",
                                        weight="bold", size=14, color="white"),
                            ], spacing=8),
                            bgcolor="#00695C",
                            padding=ft.padding.symmetric(
                                horizontal=16, vertical=10),
                            border_radius=ft.border_radius.only(
                                top_left=12, top_right=12),
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.WORK_ROUNDED,
                                            color="#00695C", size=20),
                                    ft.Text(m['ism'],
                                            weight="bold", size=17),
                                ], spacing=10),
                                ft.Row([
                                    ft.Icon(ft.Icons.TAG_ROUNDED,
                                            color=None, size=15),
                                    ft.Text("رمز المهنة:", size=13),
                                    ft.Text(str(m['ramz']), size=13,
                                            weight="bold", color="#00695C"),
                                ], spacing=6),
                                ft.Divider(height=10),
                                ft.Row([
                                    ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED,
                                            color="#00695C", size=16),
                                    ft.Text("أيام العمل:", size=13),
                                    ft.Text(f"{int(m['ayam'])} يوم",
                                            size=13, weight="bold",
                                            color="#00695C"),
                                ], spacing=6),
                                ft.Row([
                                    ft.Icon(ft.Icons.PERCENT_ROUNDED,
                                            color="#1565C0", size=16),
                                    ft.Text("نسبة الربح:", size=13),
                                    ft.Text(f"{m['nisba']}%",
                                            size=13, weight="bold",
                                            color="#1565C0"),
                                ], spacing=6),
                            ], spacing=8),
                            padding=ft.padding.all(14),
                        ),
                    ], spacing=0),
                    elevation=2,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    margin=ft.margin.symmetric(vertical=6),
                )
                mihna_info.visible = True
                results_col.controls.clear()
            except Exception as ex:
                print(f"[select_mihna] {ex}")
            search_f.update()
            mihna_info.update()
            results_col.update()

        def calc(e):
            if selected_mihna["data"] is None:
                search_f.error_text = "يرجى اختيار مهنة من القائمة"
                search_f.update()
                return
            daily = validate_number(daily_f, "الدخل اليومي")
            if daily is None:
                page.update()
                return
            try:
                m          = selected_mihna["data"]
                ayam       = int(float(m["ayam"]))
                nisba_ribh = float(m["nisba"]) / 100
                if ayam <= 0 or not (0 < nisba_ribh <= 1):
                    results_col.controls.clear()
                    results_col.controls.append(make_result_card(
                        ft.Text("بيانات المهنة غير صحيحة", size=15)))
                    page.update()
                    return

                dakhl_sanawi = safe_ceil(daily * ayam)
                ribh_safi    = safe_ceil(dakhl_sanawi * nisba_ribh)
                exempt       = SETTINGS["maqtou3_exempt"]
                brackets     = SETTINGS["maqtou3_brackets"]
                tafaseel, dariba = calc_maqtou3_tax(ribh_safi, brackets, exempt)

                results_col.controls.clear()

                # بطاقة الملخص
                ribh_khadi3 = max(0, ribh_safi - int(exempt))
                results_col.controls.append(make_result_card(ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SUMMARIZE_OUTLINED,
                                color="#00695C", size=20),
                        ft.Text("ملخص الحساب", weight="bold", size=15,
                                color="#00695C"),
                    ], spacing=8),
                    ft.Divider(height=12),
                    result_row("الدخل اليومي",              safe_ceil(daily)),
                    result_row("أيام العمل السنوي",          ayam),
                    result_row("الدخل السنوي الإجمالي",      dakhl_sanawi),
                    result_row(f"الربح الصافي ({m['nisba']}%)", ribh_safi),
                    result_row("الحد المعفى",                int(exempt)),
                    ft.Divider(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Text("الربح الخاضع للضريبة",
                                    size=13, weight="bold"),
                            ft.Text(f"{ribh_khadi3:,}",
                                    size=15, weight="bold",
                                    color="#E65100"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        border=ft.border.all(1.5, "#E65100"),
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    ),
                ])))

                # بطاقة الشرائح
                if tafaseel:
                    sh_rows = [
                        ft.Row([
                            ft.Icon(ft.Icons.LAYERS_OUTLINED,
                                    color="#1565C0", size=18),
                            ft.Text("تفصيل الشرائح", weight="bold", size=14,
                                    color="#1565C0"),
                        ], spacing=8),
                        ft.Divider(height=10),
                    ]
                    for i, sh in enumerate(tafaseel, 1):
                        upper_str = (f"{int(sh['upper']):,}"
                                     if sh["upper"] != float("inf") else "فما فوق")
                        sh_rows.append(ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    f"الشريحة {i}  ·  {sh['pct']:.0f}%"
                                    f"  ·  {int(sh['lower']):,} — {upper_str}",
                                    size=12, color=None,
                                ),
                                ft.Row([
                                    ft.Text("الوعاء الخاضع:", size=12),
                                    ft.Text(f"{int(sh['wia3_taxable']):,}",
                                            size=13, weight="bold"),
                                    ft.Container(expand=True),
                                    ft.Text("الضريبة:", size=12),
                                    ft.Text(f"{int(sh['dariba']):,}",
                                            size=13, weight="bold",
                                            color="#C62828"),
                                ]),
                            ], spacing=4),
                            bgcolor=None,
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            border_radius=10,
                            border=ft.border.all(1, "#00695C33"),
                            margin=ft.margin.symmetric(vertical=3),
                        ))
                    results_col.controls.append(make_result_card(ft.Column(sh_rows)))

                # بطاقة الإجمالي
                results_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.RECEIPT_ROUNDED, color="white", size=24),
                            ft.Column([
                                ft.Text("مجموع الضريبة النهائي",
                                        color="#ffffffcc", size=13),
                                ft.Text(f"{int(dariba):,}", color="white",
                                        size=24, weight="bold"),
                            ], spacing=2),
                        ], spacing=14),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=["#E65100", "#BF360C"],
                        ),
                        padding=ft.padding.symmetric(horizontal=20, vertical=18),
                        border_radius=16,
                        margin=ft.margin.symmetric(vertical=5),
                    )
                )
            except Exception as ex:
                print(f"[dariba calc] {ex}")
                results_col.controls.clear()
                results_col.controls.append(make_result_card(
                    ft.Text("حدث خطأ، يرجى التحقق من البيانات", size=14)))
            page.update()

        def show_manage_mihna(ev):
            page.controls.clear()
            set_appbar("إدارة المهن", back_fn=show_dariba_maqtou3)

            mihna_list_col = ft.ListView(spacing=6, expand=True, auto_scroll=True)
            ism_f   = text_field("اسم المهنة",       hint="مثال: محامي",
                                  icon=ft.Icons.PERSON_OUTLINE_ROUNDED)
            ramz_f  = num_field("رمز المهنة",          hint="مثال: 101",
                                 icon=ft.Icons.TAG_ROUNDED)
            ayam_f  = num_field("أيام العمل السنوي",   hint="مثال: 270",
                                 icon=ft.Icons.CALENDAR_MONTH_OUTLINED)
            nisba_f = num_field("نسبة الربح %",        hint="مثال: 70",
                                 icon=ft.Icons.PERCENT_ROUNDED)
            add_msg    = ft.Text("", size=13)
            edit_index = {"i": None}

            def refresh_list():
                mihna_list_col.controls.clear()
                for idx, m in enumerate(SETTINGS["mihna_list"]):
                    try:
                        def make_edit(i):
                            def do_edit(ev2):
                                def confirmed():
                                    try:
                                        m2 = SETTINGS["mihna_list"][i]
                                        ism_f.value   = str(m2.get("ism",   ""))
                                        ramz_f.value  = str(int(m2.get("ramz",  0)))
                                        ayam_f.value  = str(int(m2.get("ayam",  0)))
                                        nisba_f.value = str(m2.get("nisba", 0))
                                        edit_index["i"] = i
                                        add_msg.value = "جاري التعديل... اضغط حفظ"
                                        add_msg.color = "#E65100"
                                    except (IndexError, KeyError, TypeError) as ex:
                                        print(f"[edit] {ex}")
                                    page.update()
                                confirm_dialog(
                                    "تعديل المهنة",
                                    "هل انت متاكد من تعديل بيانات هذه المهنة؟",
                                    confirmed,
                                )
                            return do_edit

                        def make_delete(i):
                            def do_delete(ev2):
                                def confirmed():
                                    try:
                                        SETTINGS["mihna_list"].pop(i)
                                        save_data(SETTINGS, page)
                                        rebuild_index()
                                        refresh_list()
                                    except IndexError:
                                        pass
                                    page.update()
                                confirm_dialog("حذف المهنة",
                                    "هل انت متاكد من حذف هذه المهنة؟",
                                    confirmed)
                            return do_delete

                        mihna_list_col.controls.append(
                            ft.Card(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.WORK_OUTLINE_ROUNDED,
                                                    color="#00695C"),
                                    title=ft.Text(
                                        f"{m.get('ism','?')}  [{m.get('ramz','?')}]",
                                        weight="bold", size=14),
                                    subtitle=ft.Text(
                                        f"أيام: {m.get('ayam','?')}"
                                        f"  ·  ربح: {m.get('nisba','?')}%",
                                        size=12),
                                    trailing=ft.Row([
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            on_click=make_edit(idx),
                                            icon_color="#00695C",
                                            tooltip="تعديل",
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE_ROUNDED,
                                            on_click=make_delete(idx),
                                            icon_color="#C62828",
                                            tooltip="حذف",
                                        ),
                                    ], tight=True, spacing=0),
                                ),
                                elevation=1,
                                margin=ft.margin.symmetric(vertical=3),
                                shape=ft.RoundedRectangleBorder(radius=14),
                            )
                        )
                    except Exception as ex:
                        print(f"[refresh row {idx}] {ex}")
                page.update()

            def save_mihna(ev2):
                ism = (ism_f.value or "").strip()[:MAX_STR_LEN]
                if not ism:
                    ism_f.error_text = "يرجى إدخال اسم المهنة"
                    ism_f.update()
                    return
                ramz  = validate_number(ramz_f,  "رمز المهنة")
                ayam  = validate_number(ayam_f,  "أيام العمل", max_val=366)
                nisba = validate_number(nisba_f, "نسبة الربح", max_val=100)
                if not all([ramz, ayam, nisba]):
                    page.update()
                    return
                new_m = {"ism": ism, "ramz": int(ramz),
                         "ayam": int(ayam), "nisba": nisba}
                if edit_index["i"] is not None:
                    try:
                        SETTINGS["mihna_list"][edit_index["i"]] = new_m
                        add_msg.value = "تم التعديل بنجاح"
                    except IndexError:
                        SETTINGS["mihna_list"].append(new_m)
                        add_msg.value = "تم إضافة المهنة بنجاح"
                    edit_index["i"] = None
                else:
                    if len(SETTINGS["mihna_list"]) >= MAX_MIHNA:
                        add_msg.value = f"الحد الأقصى {MAX_MIHNA} مهنة"
                        add_msg.color = "#E65100"
                        page.update()
                        return
                    SETTINGS["mihna_list"].append(new_m)
                    add_msg.value = "تم إضافة المهنة بنجاح"
                add_msg.color = "#00695C"
                save_data(SETTINGS, page)
                rebuild_index()
                ism_f.value = ramz_f.value = ayam_f.value = nisba_f.value = ""
                if edit_index["i"] is not None:
                    edit_index["i"] = None
                    refresh_list()
                else:
                    # إضافة بطاقة المهنة الجديدة فقط بدون إعادة بناء القائمة
                    idx = len(SETTINGS["mihna_list"]) - 1
                    m = SETTINGS["mihna_list"][idx]

                    def make_edit_new(i):
                        def do_edit(ev2):
                            def confirmed():
                                try:
                                    m2 = SETTINGS["mihna_list"][i]
                                    ism_f.value   = str(m2.get("ism",   ""))
                                    ramz_f.value  = str(int(m2.get("ramz",  0)))
                                    ayam_f.value  = str(int(m2.get("ayam",  0)))
                                    nisba_f.value = str(m2.get("nisba", 0))
                                    edit_index["i"] = i
                                    add_msg.value = "جاري التعديل... اضغط حفظ"
                                    add_msg.color = "#E65100"
                                except Exception as ex:
                                    print(f"[edit] {ex}")
                                page.update()
                            confirm_dialog("تعديل المهنة",
                                "هل انت متاكد من تعديل بيانات هذه المهنة؟",
                                confirmed)
                        return do_edit

                    def make_delete_new(i):
                        def do_delete(ev2):
                            def confirmed():
                                try:
                                    SETTINGS["mihna_list"].pop(i)
                                    save_data(SETTINGS, page)
                                    rebuild_index()
                                    refresh_list()
                                except IndexError:
                                    pass
                                page.update()
                            confirm_dialog("حذف المهنة",
                                "هل انت متاكد من حذف هذه المهنة؟",
                                confirmed)
                        return do_delete

                    mihna_list_col.controls.append(
                        ft.Card(
                            content=ft.ListTile(
                                leading=ft.Icon(ft.Icons.WORK_OUTLINE_ROUNDED,
                                                color="#00695C"),
                                title=ft.Text(
                                    f"{m.get('ism','?')}  [{m.get('ramz','?')}]",
                                    weight="bold", size=14),
                                subtitle=ft.Text(
                                    f"أيام: {m.get('ayam','?')}"
                                    f"  ·  ربح: {m.get('nisba','?')}%",
                                    size=12),
                                trailing=ft.Row([
                                    ft.IconButton(
                                        ft.Icons.EDIT_OUTLINED,
                                        on_click=make_edit_new(idx),
                                        icon_color="#00695C",
                                        tooltip="تعديل",
                                    ),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE_ROUNDED,
                                        on_click=make_delete_new(idx),
                                        icon_color="#C62828",
                                        tooltip="حذف",
                                    ),
                                ], tight=True, spacing=0),
                            ),
                            elevation=1,
                            margin=ft.margin.symmetric(vertical=3),
                            shape=ft.RoundedRectangleBorder(radius=14),
                        )
                    )
                    mihna_list_col.update()
                add_msg.update()
                ism_f.update()
                ramz_f.update()
                ayam_f.update()
                nisba_f.update()

            refresh_list()

            page.add(ft.Column(
                controls=[
                    ft.Container(height=8),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                                            color="#00695C"),
                                    ft.Text("إضافة / تعديل مهنة",
                                            weight="bold", size=14),
                                ], spacing=8),
                                ft.Divider(height=10),
                                ism_f, ramz_f, ayam_f, nisba_f,
                                primary_btn("حفظ المهنة", save_mihna,
                                            icon=ft.Icons.SAVE_OUTLINED),
                                add_msg,
                            ], spacing=10),
                            padding=ft.padding.all(16),
                        ),
                        elevation=1,
                        shape=ft.RoundedRectangleBorder(radius=16),
                    ),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Icon(ft.Icons.LIST_ROUNDED,
                                color=None, size=16),
                        ft.Text("المهن المحفوظة", size=13,
                                color=None),
                    ], spacing=6),
                    mihna_list_col,
                    ft.Container(height=16),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8, expand=True, scroll=ft.ScrollMode.AUTO,
            ))
            page.update()

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                search_f,
                ft.Card(
                    content=suggestions_col,
                    elevation=2,
                    visible=True,
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
                mihna_info,
                ft.Container(height=4),
                daily_f,
                primary_btn("احسب الضريبة", calc,
                            icon=ft.Icons.CALCULATE_ROUNDED),
                results_col,
                ft.Container(height=10),
                tonal_btn("إدارة المهن", show_manage_mihna,
                          icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10, expand=True, scroll=ft.ScrollMode.AUTO,
        ))
        page.update()

    # ══════════════════════════════════════
    #  3) ريع رؤوس الاموال المتداولة
    # ══════════════════════════════════════
    def show_rea3(e=None):
        page.controls.clear()
        push_page(show_rea3)
        set_appbar("ريع رؤوس الاموال")

        currency_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value="old", label=ft.Text("عملة قديمة"),
                           icon=ft.Icon(ft.Icons.HISTORY_ROUNDED)),
                ft.Segment(value="new", label=ft.Text("عملة جديدة"),
                           icon=ft.Icon(ft.Icons.FIBER_NEW_ROUNDED)),
            ],
            selected=["old"],
            allow_multiple_selection=False,
        )
        bond_f = num_field("قيمة السند",
                           hint="مثال: 1,000,000",
                           icon=ft.Icons.ACCOUNT_BALANCE_OUTLINED)

        dur_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value="1year",  label=ft.Text("سنة واحدة"),
                           icon=ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED)),
                ft.Segment(value="custom", label=ft.Text("تحديد تاريخين"),
                           icon=ft.Icon(ft.Icons.DATE_RANGE_OUTLINED)),
            ],
            selected=["1year"],
            allow_multiple_selection=False,
        )

        selected_dates = {"bond": None, "today": date.today()}
        date1_btn = ft.OutlinedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=16),
                ft.Text("اختر تاريخ السند", size=13),
            ], tight=True, spacing=8),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        )
        date2_btn = ft.OutlinedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.TODAY_ROUNDED, size=16),
                ft.Text(f"التاريخ الحالي: {date.today().strftime('%Y-%m-%d')}",
                        size=13),
            ], tight=True, spacing=8),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
        )
        date_error  = ft.Text("", color="#C62828", size=13, visible=False)

        def on_bond_date_picked(e):
            try:
                if e.control.value:
                    selected_dates["bond"] = e.control.value.date()
                    date1_btn.content = ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                                size=16, color="#00695C"),
                        ft.Text(f"تاريخ السند: {selected_dates['bond'].strftime('%Y-%m-%d')}",
                                size=13, color="#00695C"),
                    ], tight=True, spacing=8)
                    date_error.visible = False
            except Exception as ex:
                print(f"[bond date] {ex}")
            page.update()

        def on_today_date_picked(e):
            try:
                if e.control.value:
                    selected_dates["today"] = e.control.value.date()
                    date2_btn.content = ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                                size=16, color="#00695C"),
                        ft.Text(f"التاريخ الحالي: {selected_dates['today'].strftime('%Y-%m-%d')}",
                                size=13, color="#00695C"),
                    ], tight=True, spacing=8)
                    date_error.visible = False
            except Exception as ex:
                print(f"[today date] {ex}")
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

        date1_btn.on_click = lambda e: setattr(bond_date_picker,  "open", True) or page.update()
        date2_btn.on_click = lambda e: setattr(today_date_picker, "open", True) or page.update()

        dates_section = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.DATE_RANGE_OUTLINED,
                                color="#00695C", size=18),
                        ft.Text("تحديد تاريخ السند والتاريخ الحالي",
                                weight="bold", size=13),
                    ], spacing=8),
                    ft.Divider(height=10),
                    date1_btn,
                    date2_btn,
                    date_error,
                ], spacing=10),
                padding=ft.padding.all(14),
            ),
            elevation=1,
            visible=False,
            shape=ft.RoundedRectangleBorder(radius=14),
        )
        results_col = ft.Column(spacing=8)

        def on_dur_change(e):
            dates_section.visible = ("custom" in dur_seg.selected)
            page.update()
        dur_seg.on_change = on_dur_change

        def calc(e):
            try:
                qima_raw = validate_number(bond_f, "قيمة السند")
                if qima_raw is None:
                    page.update()
                    return

                omla  = list(currency_seg.selected)[0]
                qima  = qima_raw * 100 if omla == "new" else qima_raw

                faida_pct = _sanitize_float(SETTINGS.get("rea3_faida_pct", 10), 10, 0.001, 100) / 100
                rasm_pct  = _sanitize_float(SETTINGS.get("rea3_rasm_pct",  10), 10, 0.001, 100) / 100
                idara_pct = _sanitize_float(SETTINGS.get("rea3_idara_pct", 10), 10, 0.001, 100) / 100

                faida = qima * faida_pct
                rasm  = safe_ceil(faida * rasm_pct)
                div   = 100 if omla == "new" else 1

                def v(x):
                    try:
                        return safe_ceil(x / div)
                    except (ZeroDivisionError, TypeError):
                        return 0

                omla_label = "عملة قديمة" if omla == "old" else "عملة جديدة"
                results_col.controls.clear()

                if "1year" in dur_seg.selected:
                    idara = safe_ceil(rasm * idara_pct)
                    total = v(safe_ceil(rasm + idara))

                    rows = [
                        ft.Row([
                            ft.Icon(ft.Icons.TRENDING_UP_ROUNDED,
                                    color="#00695C", size=20),
                            ft.Text("ريع رأس المال - سنة واحدة",
                                    weight="bold", size=15, color="#00695C"),
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(omla_label, size=11, color="white"),
                            bgcolor="#00695C",
                            padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            border_radius=20,
                        ),
                        ft.Divider(height=12),
                        result_row("قيمة السند",         safe_ceil(qima_raw)),
                        result_row(f"الفائدة ({int(SETTINGS.get('rea3_faida_pct',10))}%)", v(safe_ceil(faida))),
                        result_row(f"الرسم ({int(SETTINGS.get('rea3_rasm_pct',10))}%)",    v(rasm)),
                        result_row(f"رسم الإدارة ({int(SETTINGS.get('rea3_idara_pct',10))}%)", v(idara)),
                        ft.Divider(height=12),
                        ft.Row([
                            ft.Text("المجموع الكلي", weight="bold", size=15),
                            ft.Text(f"{total:,}", weight="bold", size=18,
                                    color="#00695C"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]
                    if omla == "old":
                        rows.append(ft.Row([
                            ft.Text("بالعملة الجديدة", size=13,
                                    color=None),
                            ft.Text(f"{safe_ceil(total/100):,}", size=14,
                                    weight="bold",
                                    color="#1565C0"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                    results_col.controls.append(make_result_card(ft.Column(rows)))

                else:
                    if selected_dates["bond"] is None:
                        date_error.value   = "يرجى اختيار تاريخ السند"
                        date_error.visible = True
                        page.update()
                        return
                    d1, d2 = selected_dates["bond"], selected_dates["today"]
                    if d2 <= d1:
                        date_error.value   = "التاريخ الحالي يجب أن يكون بعد تاريخ السند"
                        date_error.visible = True
                        page.update()
                        return
                    date_error.visible = False
                    delta  = (d2 - d1).days
                    sana   = delta // 365
                    ashhur = (delta % 365) // 30
                    ayam   = (delta % 365) % 30
                    rs     = rasm * sana
                    ra     = safe_ceil((rasm * ashhur) / 12)  if ashhur > 0 else 0
                    rd     = safe_ceil((rasm * ayam)   / 365) if ayam   > 0 else 0
                    tr     = rs + ra + rd
                    idara  = safe_ceil(tr * idara_pct)
                    total  = v(safe_ceil(tr + idara))

                    rows = [
                        ft.Row([
                            ft.Icon(ft.Icons.TRENDING_UP_ROUNDED,
                                    color="#00695C", size=20),
                            ft.Text("ريع رأس المال - مدة مخصصة",
                                    weight="bold", size=15, color="#00695C"),
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(omla_label, size=11, color="white"),
                            bgcolor="#00695C",
                            padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            border_radius=20,
                        ),
                        ft.Divider(height=12),
                        result_row("قيمة السند", safe_ceil(qima_raw)),
                        result_row(f"الفائدة ({int(SETTINGS.get('rea3_faida_pct',10))}%)", v(safe_ceil(faida))),
                        ft.Container(
                            content=ft.Text(
                                f"المدة: {sana} سنة  /  {ashhur} شهر  /  {ayam} يوم",
                                size=13, color=None),
                            bgcolor="#F5F5F5",
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            border_radius=10,
                        ),
                        ft.Divider(height=8),
                        result_row("رسم السنوات", v(rs)),
                        result_row("رسم الأشهر",  v(ra)),
                        result_row("رسم الأيام",  v(rd)),
                        result_row("مجموع الرسوم", v(tr)),
                        result_row("رسم الإدارة", v(idara)),
                        ft.Divider(height=12),
                        ft.Row([
                            ft.Text("المجموع الكلي", weight="bold", size=15),
                            ft.Text(f"{total:,}", weight="bold", size=18,
                                    color="#00695C"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]
                    if omla == "old":
                        rows.append(ft.Row([
                            ft.Text("بالعملة الجديدة", size=13,
                                    color=None),
                            ft.Text(f"{safe_ceil(total/100):,}", size=14,
                                    weight="bold", color="#1565C0"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                    results_col.controls.append(make_result_card(ft.Column(rows)))

            except Exception as ex:
                print(f"[rea3 calc] {ex}")
                results_col.controls.clear()
                results_col.controls.append(make_result_card(
                    ft.Text("حدث خطأ، يرجى التحقق من البيانات", size=14)))
            page.update()

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Text("نوع العملة المدخلة", size=13,
                        color=None),
                currency_seg,
                ft.Container(height=4),
                bond_f,
                ft.Container(height=4),
                ft.Text("مدة السند", size=13,
                        color=None),
                dur_seg,
                dates_section,
                ft.Container(height=4),
                primary_btn("احسب", calc, icon=ft.Icons.CALCULATE_ROUNDED),
                ft.Container(height=4),
                results_col,
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10, expand=True, scroll=ft.ScrollMode.AUTO,
        ))
        page.update()

    # ══════════════════════════════════════
    #  4) الارباح الحقيقية
    # ══════════════════════════════════════
    def show_arbah(e=None):
        page.controls.clear()
        push_page(show_arbah)
        set_appbar("الارباح الحقيقية")

        currency_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value="new", label=ft.Text("عملة جديدة"),
                           icon=ft.Icon(ft.Icons.FIBER_NEW_ROUNDED)),
                ft.Segment(value="old", label=ft.Text("عملة قديمة"),
                           icon=ft.Icon(ft.Icons.HISTORY_ROUNDED)),
            ],
            selected=["new"],
            allow_multiple_selection=False,
        )
        income_f    = num_field("القيمة المراد حسابها",
                                hint="مثال: 17,000,000",
                                icon=ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED)
        results_col = ft.Column(spacing=8)

        def calc(e):
            try:
                mablagh = validate_number(income_f, "القيمة")
                if mablagh is None:
                    page.update()
                    return

                omla    = list(currency_seg.selected)[0]
                maffy   = (SETTINGS["arbah_old_exempt"]
                           if omla == "old" else SETTINGS["arbah_new_exempt"])
                sharaeh = (SETTINGS["arbah_old_brackets"]
                           if omla == "old" else SETTINGS["arbah_new_brackets"])
                rasm_idara_pct = _sanitize_float(SETTINGS["rasm_idara_pct"], 0.10, 0, 1)

                results_col.controls.clear()

                if mablagh <= maffy:
                    results_col.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                                                color="#00695C", size=28),
                                        ft.Column([
                                            ft.Text("ضمن حد الإعفاء",
                                                    weight="bold", size=15,
                                                    color="#00695C"),
                                            ft.Text("لا ضريبة مستحقة",
                                                    size=13,
                                                    color=None),
                                        ], spacing=2),
                                    ], spacing=12),
                                    ft.Divider(height=12),
                                    result_row(f"المبلغ المدخل", safe_ceil(mablagh)),
                                    result_row(f"الحد المعفى",   int(maffy)),
                                ], spacing=8),
                                padding=ft.padding.all(16),
                            ),
                            elevation=2,
                            shape=ft.RoundedRectangleBorder(radius=16),
                        )
                    )
                    page.update()
                    return

                tafaseel, dariba_klia = calc_arbah_brackets(mablagh, sharaeh)
                rasm_idara  = safe_ceil(dariba_klia * rasm_idara_pct)
                total_qabla = dariba_klia + rasm_idara
                total_nihai = (safe_ceil(total_qabla / 100)
                               if omla == "old" else total_qabla)

                # بطاقة الملخص
                results_col.controls.append(make_result_card(ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SUMMARIZE_OUTLINED,
                                color="#00695C", size=20),
                        ft.Text("ملخص الحساب", weight="bold", size=15,
                                color="#00695C"),
                    ], spacing=8),
                    ft.Divider(height=12),
                    result_row("المبلغ الكلي", safe_ceil(mablagh)),
                    result_row("الحد المعفى",  int(maffy)),
                ])))

                # بطاقة الشرائح
                sh_rows = [
                    ft.Row([
                        ft.Icon(ft.Icons.LAYERS_OUTLINED,
                                color="#1565C0", size=18),
                        ft.Text("تفصيل الشرائح", weight="bold", size=14,
                                color="#1565C0"),
                    ], spacing=8),
                    ft.Divider(height=10),
                ]
                for i, sh in enumerate(tafaseel, 1):
                    upper_str = (f"{int(sh['upper']):,}"
                                 if sh["upper"] != float("inf") else "فما فوق")
                    sh_rows.append(ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"الشريحة {i}  ·  {sh['pct']:.0f}%"
                                f"  ·  {int(sh['lower']):,} — {upper_str}",
                                size=12, color=None),
                            ft.Row([
                                ft.Text("الوعاء:", size=12),
                                ft.Text(f"{int(sh['wia3']):,}",
                                        size=13, weight="bold"),
                                ft.Container(expand=True),
                                ft.Text("الضريبة:", size=12),
                                ft.Text(f"{int(sh['dariba']):,}",
                                        size=13, weight="bold",
                                        color="#C62828"),
                            ]),
                        ], spacing=4),
                        bgcolor=None,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=10,
                        border=ft.border.all(1, "#1565C033"),
                        margin=ft.margin.symmetric(vertical=3),
                    ))
                results_col.controls.append(make_result_card(ft.Column(sh_rows)))

                # بطاقة الإجمالي
                total_rows = [
                    ft.Row([
                        ft.Icon(ft.Icons.RECEIPT_ROUNDED,
                                color="#00695C", size=20),
                        ft.Text("الإجمالي النهائي", weight="bold", size=15,
                                color="#00695C"),
                    ], spacing=8),
                    ft.Divider(height=12),
                    result_row("مجموع الضريبة",   dariba_klia),
                    result_row(f"رسم الإدارة ({int(rasm_idara_pct*100)}%)",
                               rasm_idara),
                ]
                if omla == "old":
                    total_rows += [
                        result_row("المجموع قبل التحويل", total_qabla),
                        ft.Text("÷ 100 تحويل للعملة الجديدة",
                                size=12, color=None,
                                italic=True),
                    ]
                total_rows += [
                    ft.Divider(height=12),
                    ft.Row([
                        ft.Text("المجموع النهائي", weight="bold", size=16),
                        ft.Text(f"{total_nihai:,}", weight="bold", size=20,
                                color="#00695C"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ]
                results_col.controls.append(make_result_card(ft.Column(total_rows)))

            except Exception as ex:
                print(f"[arbah calc] {ex}")
                results_col.controls.clear()
                results_col.controls.append(make_result_card(
                    ft.Text("حدث خطأ، يرجى التحقق من البيانات", size=14)))
            page.update()

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Text("نوع العملة", size=13,
                        color=None),
                currency_seg,
                ft.Container(height=4),
                income_f,
                primary_btn("احسب", calc, icon=ft.Icons.CALCULATE_ROUNDED),
                ft.Container(height=4),
                results_col,
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10, expand=True, scroll=ft.ScrollMode.AUTO,
        ))
        page.update()

    # ══════════════════════════════════════
    #  5) الإعدادات
    # ══════════════════════════════════════
    def show_settings(e=None):
        page.controls.clear()
        push_page(show_settings)
        set_appbar("الإعدادات والنسب", show_back=True, back_fn=show_home)

        def settings_tile(title, subtitle, icon, color, handler):
            return ft.Card(
                content=ft.ListTile(
                    leading=ft.Container(
                        content=ft.Icon(icon, color="white", size=20),
                        bgcolor=color,
                        width=40, height=40,
                        border_radius=10,
                        alignment=ft.Alignment.CENTER,
                    ),
                    title=ft.Text(title, weight="bold", size=14, color=None),
                    subtitle=ft.Text(subtitle, size=11,
                                     color=None),
                    trailing=ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                     size=14, color=None),
                    on_click=handler,
                ),
                elevation=1,
                margin=ft.margin.symmetric(vertical=4),
                shape=ft.RoundedRectangleBorder(radius=14),
            )

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                settings_tile("تحققات الدخل المقطوع", "تعديل نسب النفقات والرواتب",
                              ft.Icons.RECEIPT_LONG_OUTLINED, "#2E7D32",
                              lambda e: show_settings_maqtou3()),
                settings_tile("ضريبة الدخل المقطوع", "تعديل الشرائح الضريبية",
                              ft.Icons.WORK_OUTLINE_ROUNDED, "#E65100",
                              lambda e: show_settings_dariba()),
                settings_tile("ريع رؤوس الأموال", "تعديل نسب الفائدة والرسوم",
                              ft.Icons.TRENDING_UP_ROUNDED, "#1565C0",
                              lambda e: show_settings_rea3()),
                settings_tile("الارباح الحقيقية", "تعديل الشرائح والحدود المعفاة",
                              ft.Icons.ACCOUNT_BALANCE_OUTLINED, "#6A1B9A",
                              lambda e: show_settings_arbah()),
                settings_tile("إعدادات عامة", "رسم الإدارة وإعادة التعيين",
                              ft.Icons.TUNE_ROUNDED, "#00695C",
                              lambda e: show_settings_general()),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        ))
        page.update()

    def _brackets_editor(brackets_key, exempt_key, title, color, back_fn):
        page.controls.clear()
        set_appbar(title, back_fn=back_fn)

        save_msg = ft.Text("", size=13)

        try:
            ev = SETTINGS[exempt_key]
            exempt_val = int(ev) if float(ev) == int(float(ev)) else ev
        except (TypeError, ValueError):
            exempt_val = 0
        exempt_f = num_field("حد الإعفاء", value=exempt_val,
                              icon=ft.Icons.SHIELD_OUTLINED)

        brackets_col = ft.Column(spacing=6)

        def fmt(v):
            try:
                fv = float(v)
                return str(int(fv)) if fv == int(fv) else str(fv)
            except (TypeError, ValueError):
                return "0"

        def build_bracket_row(idx, bracket):
            try:
                lower = bracket[0]
                upper = bracket[1] if bracket[1] is not None else ""
                nisba = float(bracket[2]) * 100
            except (IndexError, TypeError, ValueError):
                lower, upper, nisba = 0, "", 10

            lower_f = num_field("من",       value=fmt(lower), width=95)
            upper_f = ft.TextField(
                label="إلى",
                value=fmt(upper) if upper != "" else "∞",
                hint_text="∞",
                border=ft.InputBorder.OUTLINE,
                border_radius=12,
                filled=True,
                text_size=14, width=95,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=14),
            )
            nisba_f = num_field("النسبة %", value=fmt(nisba), width=85)

            def make_edit_bracket(i, lf, uf, nf):
                def do_edit(ev):
                    def confirmed():
                        try:
                            lower_raw = (lf.value or "0").strip()
                            upper_raw = (uf.value or "").strip()
                            nisba_raw = (nf.value or "0").strip()
                            lower = float(lower_raw) if lower_raw else 0
                            upper = (None if upper_raw in ["", "∞", "inf"] else float(upper_raw))
                            nisba = float(nisba_raw) / 100 if nisba_raw else 0
                            if not math.isfinite(lower) or lower < 0:
                                save_msg.value = "قيمة البداية غير صحيحة"
                                save_msg.color = "#C62828"
                                page.update()
                                return
                            if upper is not None and (not math.isfinite(upper) or upper <= lower):
                                save_msg.value = "قيمة النهاية يجب أن تكون أكبر من البداية"
                                save_msg.color = "#C62828"
                                page.update()
                                return
                            if not (0 < nisba <= 1):
                                save_msg.value = "النسبة يجب أن تكون بين 0 و 100"
                                save_msg.color = "#C62828"
                                page.update()
                                return
                            SETTINGS[brackets_key][i] = [lower, upper, nisba]
                            save_data(SETTINGS, page)
                            save_msg.value = f"تم تعديل الشريحة {i+1} بنجاح"
                            save_msg.color = "#00695C"
                            page.update()
                        except Exception as ex:
                            save_msg.value = f"خطأ: {ex}"
                            save_msg.color = "#C62828"
                            page.update()
                    confirm_dialog(f"تعديل الشريحة {i+1}", "هل انت متاكد من حفظ التعديلات؟", confirmed)
                return do_edit

            def make_delete(i):
                def do_delete(ev):
                    def confirmed():
                        try:
                            SETTINGS[brackets_key].pop(i)
                            save_data(SETTINGS, page)
                            _brackets_editor(brackets_key, exempt_key,
                                             title, color, back_fn)
                        except (IndexError, KeyError) as ex:
                            print(f"[delete bracket] {ex}")
                    confirm_dialog("حذف الشريحة",
                        "هل انت متاكد من حذف هذه الشريحة؟",
                        confirmed)
                return do_delete

            return ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(f"الشريحة {idx+1}", size=11, color="white", weight="bold"),
                                bgcolor=color,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                border_radius=20,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                on_click=make_edit_bracket(idx, lower_f, upper_f, nisba_f),
                                icon_color="#00695C",
                                icon_size=18,
                                tooltip="تعديل الشريحة",
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE_ROUNDED,
                                on_click=make_delete(idx),
                                icon_color="#C62828",
                                icon_size=18,
                                tooltip="حذف الشريحة",
                            ),
                        ]),
                        ft.Row([lower_f, upper_f, nisba_f], spacing=6),
                    ], spacing=4),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),
                elevation=1,
                margin=ft.margin.symmetric(vertical=3),
                shape=ft.RoundedRectangleBorder(radius=12),
                data={"lower_f": lower_f, "upper_f": upper_f,
                      "nisba_f": nisba_f},
            )

        try:
            for i, b in enumerate(SETTINGS.get(brackets_key, [])):
                brackets_col.controls.append(build_bracket_row(i, b))
        except Exception as ex:
            print(f"[brackets editor build] {ex}")

        def save_brackets(e):
            try:
                raw_exempt = (exempt_f.value or "0").strip()
                new_exempt = float(raw_exempt) if raw_exempt not in ("", "∞") else 0
                if not math.isfinite(new_exempt) or new_exempt < 0:
                    new_exempt = 0
                new_brackets = []
                for row in brackets_col.controls:
                    try:
                        d = row.data
                        lower_raw = (d["lower_f"].value or "0").strip()
                        upper_raw = (d["upper_f"].value or "").strip()
                        nisba_raw = (d["nisba_f"].value or "0").strip()
                        lower = float(lower_raw) if lower_raw else 0
                        upper = (None if upper_raw in ["", "∞", "inf"]
                                 else float(upper_raw))
                        nisba = float(nisba_raw) / 100 if nisba_raw else 0
                        if not math.isfinite(lower) or lower < 0:
                            continue
                        if upper is not None and (not math.isfinite(upper)
                                                   or upper <= lower):
                            continue
                        if not (0 < nisba <= 1):
                            continue
                        new_brackets.append([lower, upper, nisba])
                    except (TypeError, ValueError, KeyError, AttributeError):
                        continue
                if not new_brackets:
                    save_msg.value = "لا توجد شرائح صحيحة للحفظ"
                    save_msg.color = "#E65100"
                    page.update()
                    return
                SETTINGS[exempt_key]   = new_exempt
                SETTINGS[brackets_key] = new_brackets
                save_data(SETTINGS, page)
                save_msg.value = "تم حفظ الشرائح بنجاح"
                save_msg.color = "#00695C"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "#C62828"
            page.update()

        def add_bracket(e):
            try:
                if len(SETTINGS.get(brackets_key, [])) >= MAX_BRACKETS:
                    save_msg.value = f"الحد الأقصى {MAX_BRACKETS} شريحة"
                    save_msg.color = "#E65100"
                    page.update()
                    return
                SETTINGS[brackets_key].append([0, None, 0.10])
                save_data(SETTINGS, page)
                _brackets_editor(brackets_key, exempt_key, title, color, back_fn)
            except Exception as ex:
                print(f"[add bracket] {ex}")

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.SHIELD_OUTLINED,
                                        color="#00695C", size=18),
                                ft.Text("حد الإعفاء", weight="bold", size=14),
                            ], spacing=8),
                            exempt_f,
                        ], spacing=10),
                        padding=ft.padding.all(14),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
                ft.Container(height=8),
                ft.Row([
                    ft.Icon(ft.Icons.LAYERS_OUTLINED,
                            color=None, size=16),
                    ft.Text("الشرائح الضريبية", size=13, weight="bold",
                            color=None),
                    ft.Text("  (∞ = بلا حد)", size=11,
                            color=None, italic=True),
                ], spacing=4),
                brackets_col,
                tonal_btn("إضافة شريحة جديدة", add_bracket,
                          icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED),
                ft.Container(height=8),
                primary_btn("حفظ الشرائح", save_brackets,
                            icon=ft.Icons.SAVE_OUTLINED),
                save_msg,
                ft.Container(height=8),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=8, expand=True,
        ))
        page.update()

    def show_settings_maqtou3():
        page.controls.clear()
        set_appbar("إعدادات تحققات الدخل", back_fn=show_settings)
        save_msg = ft.Text("", size=13)

        def fmt(v):
            try:
                fv = float(v)
                return str(int(fv)) if fv == int(fv) else str(fv)
            except Exception:
                return str(v)

        nafaqat_f = num_field("النفقات %",
                               value=fmt(SETTINGS["nafaqat_default"]),
                               icon=ft.Icons.PERCENT_ROUNDED)
        idara_f   = num_field("إدارة محلية %",
                               value=fmt(SETTINGS["idara_default"]),
                               icon=ft.Icons.PERCENT_ROUNDED)
        rawatib_f = num_field("رواتب وأجور %",
                               value=fmt(SETTINGS["rawatib_default"]),
                               icon=ft.Icons.PERCENT_ROUNDED)

        def save(e):
            v1 = validate_number(nafaqat_f, "نسبة النفقات", max_val=100)
            v2 = validate_number(idara_f,   "نسبة الادارة", max_val=100)
            v3 = validate_number(rawatib_f, "نسبة الرواتب", max_val=100)
            if not all([v1, v2, v3]):
                page.update()
                return
            try:
                SETTINGS["nafaqat_default"] = int(v1) if v1 == int(v1) else v1
                SETTINGS["idara_default"]   = int(v2) if v2 == int(v2) else v2
                SETTINGS["rawatib_default"] = int(v3) if v3 == int(v3) else v3
                save_data(SETTINGS, page)
                save_msg.value = "تم الحفظ بنجاح"
                save_msg.color = "#00695C"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "#C62828"
            page.update()

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            nafaqat_f, idara_f, rawatib_f,
                            primary_btn("حفظ", save,
                                        icon=ft.Icons.SAVE_OUTLINED),
                            save_msg,
                        ], spacing=12),
                        padding=ft.padding.all(16),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=16),
                ),
                ft.Container(height=8),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8, expand=True,
        ))
        page.update()

    def show_settings_dariba():
        _brackets_editor("maqtou3_brackets", "maqtou3_exempt",
                         "شرائح الدخل المقطوع", "#E65100", show_settings)

    def show_settings_rea3():
        page.controls.clear()
        set_appbar("إعدادات ريع رؤوس الأموال", back_fn=show_settings)
        save_msg = ft.Text("", size=13)

        def fmt(v):
            try:
                fv = float(v)
                return str(int(fv)) if fv == int(fv) else str(fv)
            except Exception:
                return str(v)

        faida_f = num_field("نسبة الفائدة %",
                             value=fmt(SETTINGS.get("rea3_faida_pct", 10)),
                             icon=ft.Icons.PERCENT_ROUNDED)
        rasm_f  = num_field("نسبة الرسم %",
                             value=fmt(SETTINGS.get("rea3_rasm_pct",  10)),
                             icon=ft.Icons.PERCENT_ROUNDED)
        idara_f = num_field("نسبة رسم الإدارة %",
                             value=fmt(SETTINGS.get("rea3_idara_pct", 10)),
                             icon=ft.Icons.PERCENT_ROUNDED)

        def save(e):
            v1 = validate_number(faida_f, "نسبة الفائدة", max_val=100)
            v2 = validate_number(rasm_f,  "نسبة الرسم",   max_val=100)
            v3 = validate_number(idara_f, "نسبة الإدارة", max_val=100)
            if not all([v1, v2, v3]):
                page.update()
                return
            try:
                SETTINGS["rea3_faida_pct"] = v1
                SETTINGS["rea3_rasm_pct"]  = v2
                SETTINGS["rea3_idara_pct"] = v3
                save_data(SETTINGS, page)
                save_msg.value = "تم الحفظ بنجاح"
                save_msg.color = "#00695C"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "#C62828"
            page.update()

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            faida_f, rasm_f, idara_f,
                            primary_btn("حفظ", save,
                                        icon=ft.Icons.SAVE_OUTLINED),
                            save_msg,
                        ], spacing=12),
                        padding=ft.padding.all(16),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=16),
                ),
                ft.Container(height=8),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8, expand=True,
        ))
        page.update()

    def show_settings_arbah():
        page.controls.clear()
        set_appbar("إعدادات الارباح الحقيقية", back_fn=show_settings)

        omla_seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value="new", label=ft.Text("عملة جديدة")),
                ft.Segment(value="old", label=ft.Text("عملة قديمة")),
            ],
            selected=["new"],
            allow_multiple_selection=False,
        )

        def go_edit(e):
            if "new" in omla_seg.selected:
                _brackets_editor("arbah_new_brackets", "arbah_new_exempt",
                                 "أرباح - عملة جديدة", "#6A1B9A",
                                 show_settings_arbah)
            else:
                _brackets_editor("arbah_old_brackets", "arbah_old_exempt",
                                 "أرباح - عملة قديمة", "#6A1B9A",
                                 show_settings_arbah)

        page.add(ft.Column(
            controls=[
                ft.Container(height=8),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.LAYERS_OUTLINED,
                                        color="#00695C"),
                                ft.Text("اختر العملة لتعديل شرائحها",
                                        weight="bold", size=14),
                            ], spacing=8),
                            ft.Divider(height=10),
                            omla_seg,
                            primary_btn("تعديل الشرائح", go_edit,
                                        icon=ft.Icons.EDIT_OUTLINED),
                        ], spacing=12),
                        padding=ft.padding.all(16),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=16),
                ),
                ft.Container(height=8),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8, expand=True,
        ))
        page.update()

    def toggle_dark_mode(e):
        SETTINGS["dark_mode"] = e.control.value
        save_data(SETTINGS, page)
        page.theme_mode = ft.ThemeMode.DARK if SETTINGS["dark_mode"] else ft.ThemeMode.LIGHT
        page.update()

    def show_settings_general():
        page.controls.clear()
        set_appbar("إعدادات عامة", back_fn=show_settings)
        save_msg = ft.Text("", size=13)

        def fmt(v):
            try:
                fv = float(v)
                return str(int(fv)) if fv == int(fv) else str(fv)
            except Exception:
                return str(v)

        rasm_f = num_field("رسم الادارة المحلية %",
                            value=fmt(SETTINGS["rasm_idara_pct"] * 100),
                            icon=ft.Icons.PERCENT_ROUNDED)

        def save(e):
            v = validate_number(rasm_f, "رسم الادارة", max_val=100)
            if v is None:
                page.update()
                return
            try:
                SETTINGS["rasm_idara_pct"] = v / 100
                save_data(SETTINGS, page)
                save_msg.value = "تم الحفظ بنجاح"
                save_msg.color = "#00695C"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "#C62828"
            page.update()

        def reset(e):
            try:
                for key, val in DEFAULT_SETTINGS.items():
                    if key != "mihna_list":
                        SETTINGS[key] = val
                save_data(SETTINGS, page)
                save_msg.value = "تم إعادة التعيين للقيم الافتراضية"
                save_msg.color = "#E65100"
            except Exception as ex:
                save_msg.value = f"خطأ: {ex}"
                save_msg.color = "#C62828"
            page.update()
            show_settings_general()

        page.add(ft.Column(
            controls=[
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DARK_MODE_OUTLINED, color="#00695C"),
                            ft.Text("الوضع الليلي", weight="bold", size=14),
                            ft.Container(expand=True),
                            ft.Switch(
                                value=SETTINGS.get("dark_mode", False),
                                active_color="#00695C",
                                on_change=lambda e: toggle_dark_mode(e),
                            ),
                        ], spacing=8),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
                ft.Container(height=8),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            rasm_f,
                            primary_btn("حفظ", save,
                                        icon=ft.Icons.SAVE_OUTLINED),
                            save_msg,
                        ], spacing=12),
                        padding=ft.padding.all(16),
                    ),
                    elevation=1,
                    shape=ft.RoundedRectangleBorder(radius=16),
                ),
                ft.Container(height=8),
                ft.OutlinedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.RESTART_ALT_ROUNDED,
                                size=18, color="#C62828"),
                        ft.Text("إعادة تعيين كل الإعدادات",
                                size=14, color="#C62828"),
                    ], tight=True, spacing=8),
                    on_click=reset,
                    width=360,
                    height=46,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        side=ft.BorderSide(color="#C62828", width=1),
                    ),
                ),
                ft.Container(height=8),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8, expand=True,
        ))
        page.update()

    show_home()


if __name__ == "__main__":
    ft.app(target=main)
