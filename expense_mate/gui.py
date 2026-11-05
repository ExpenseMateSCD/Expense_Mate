"""
ExpenseMate - Premium Desktop GUI
Built with tkinter. Follows Controller -> Services -> Repository -> Database architecture.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from typing import Optional

from .controllers import ExpenseMateController


# ─────────────────────────── COLOUR PALETTE ───────────────────────────
BG          = "#0f172a"   # page background (very dark navy)
SIDEBAR_BG  = "#1e293b"   # sidebar / nav background
CARD_BG     = "#1e293b"   # card surface
CARD2_BG    = "#263347"   # slightly lighter card
HEADER_BG   = "#0f172a"
BORDER      = "#334155"   # subtle border / separator
TEXT        = "#f1f5f9"   # primary text
MUTED       = "#94a3b8"   # secondary / muted text
ACCENT      = "#6366f1"   # indigo accent (buttons, tabs)
ACCENT_HVR  = "#4f46e5"
SUCCESS     = "#22c55e"
DANGER      = "#ef4444"
WARNING_C   = "#f59e0b"
INFO        = "#38bdf8"

FONT_H1  = ("Segoe UI", 20, "bold")
FONT_H2  = ("Segoe UI", 13, "bold")
FONT_H3  = ("Segoe UI", 11, "bold")
FONT_B   = ("Segoe UI", 10, "bold")
FONT_N   = ("Segoe UI", 10)
FONT_S   = ("Segoe UI", 9)
FONT_MONO= ("Consolas", 9)


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def blend(c1, c2, t=0.5):
    r1,g1,b1 = hex_to_rgb(c1)
    r2,g2,b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t)


# ───────────────────── REUSABLE WIDGET HELPERS ─────────────────────────

class StyledButton(tk.Button):
    def __init__(self, master, text, command=None, color=ACCENT, fg=TEXT,
                 width=None, padx=18, pady=8, **kw):
        super().__init__(master, text=text, command=command,
                         bg=color, fg=fg, activebackground=blend(color,"#000000",0.15),
                         activeforeground=fg, relief="flat", cursor="hand2",
                         font=FONT_B, padx=padx, pady=pady,
                         **({"width": width} if width else {}), **kw)
        self.default_bg = color
        self.bind("<Enter>", lambda e: self.config(bg=blend(color,"#ffffff",0.08)))
        self.bind("<Leave>", lambda e: self.config(bg=color))


class Label(tk.Label):
    def __init__(self, master, text="", font=FONT_N, fg=TEXT, bg=None, **kw):
        super().__init__(master, text=text, font=font, fg=fg,
                         bg=bg or master.cget("bg"), **kw)


class Card(tk.Frame):
    def __init__(self, master, bg=CARD_BG, padx=16, pady=14, **kw):
        super().__init__(master, bg=bg, padx=padx, pady=pady, **kw)


class Separator(tk.Frame):
    def __init__(self, master, orient="h", **kw):
        if orient == "h":
            super().__init__(master, height=1, bg=BORDER, **kw)
        else:
            super().__init__(master, width=1, bg=BORDER, **kw)


class StyledEntry(tk.Entry):
    def __init__(self, master, textvariable=None, width=22, placeholder="", **kw):
        self._ph = placeholder
        self._var = textvariable or tk.StringVar()
        super().__init__(master, textvariable=self._var, width=width,
                         bg=CARD2_BG, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=FONT_N,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, **kw)
        if placeholder:
            self._show_placeholder()
            self.bind("<FocusIn>",  self._clear_placeholder)
            self.bind("<FocusOut>", self._show_placeholder_if_empty)

    def _show_placeholder(self, *_):
        if not self._var.get():
            self._var.set(self._ph)
            self.config(fg=MUTED)

    def _clear_placeholder(self, *_):
        if self._var.get() == self._ph:
            self._var.set("")
            self.config(fg=TEXT)

    def _show_placeholder_if_empty(self, *_):
        if not self._var.get():
            self._show_placeholder()

    def get_value(self):
        v = self._var.get()
        return "" if v == self._ph else v


class StyledCombo(ttk.Combobox):
    def __init__(self, master, textvariable=None, values=(), width=20, **kw):
        super().__init__(master, textvariable=textvariable, values=values,
                         width=width, font=FONT_N, state="readonly", **kw)


# ─────────────────────────── MAIN GUI CLASS ────────────────────────────

class ExpenseMateGUI:
    """Premium dark-themed desktop GUI for ExpenseMate."""

    def __init__(self, db_path="expense_mate.db",
                 controller: Optional[ExpenseMateController] = None):
        self.controller = controller or ExpenseMateController(db_path=db_path)
        self._active_nav = None

        self.root = tk.Tk()
        self.root.title("ExpenseMate  ·  Personal Finance Manager")
        self.root.geometry("1150x720")
        self.root.minsize(900, 640)
        self.root.configure(bg=BG)
        self.root.option_add("*TCombobox*Listbox*Background", CARD2_BG)
        self.root.option_add("*TCombobox*Listbox*Foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox*selectBackground", ACCENT)

        self._configure_ttk()
        self._build_layout()
        self._show_page("dashboard")

    # ──────────────── TTK THEME ────────────────

    def _configure_ttk(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")

        # Treeview
        s.configure("Dark.Treeview",
                     background=CARD_BG, foreground=TEXT,
                     fieldbackground=CARD_BG, rowheight=30,
                     font=FONT_N, borderwidth=0)
        s.configure("Dark.Treeview.Heading",
                     background=CARD2_BG, foreground=MUTED,
                     font=FONT_B, relief="flat", borderwidth=0)
        s.map("Dark.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", TEXT)])
        s.map("Dark.Treeview.Heading",
              background=[("active", BORDER)])

        # Scrollbar
        s.configure("Dark.Vertical.TScrollbar",
                     background=CARD2_BG, troughcolor=CARD_BG,
                     arrowcolor=MUTED, borderwidth=0, relief="flat")

        # Combobox
        s.configure("TCombobox", fieldbackground=CARD2_BG, background=CARD2_BG,
                     foreground=TEXT, arrowcolor=MUTED, borderwidth=0)
        s.map("TCombobox", fieldbackground=[("readonly", CARD2_BG)],
              foreground=[("readonly", TEXT)])

        # Progressbar
        s.configure("Green.Horizontal.TProgressbar",
                     troughcolor=CARD2_BG, background=SUCCESS, borderwidth=0)
        s.configure("Amber.Horizontal.TProgressbar",
                     troughcolor=CARD2_BG, background=WARNING_C, borderwidth=0)
        s.configure("Red.Horizontal.TProgressbar",
                     troughcolor=CARD2_BG, background=DANGER, borderwidth=0)

    # ──────────────── TOP-LEVEL LAYOUT ────────────────

    def _build_layout(self):
        # ── Topbar ──
        self.topbar = tk.Frame(self.root, bg=SIDEBAR_BG, height=56)
        self.topbar.pack(side="top", fill="x")
        self.topbar.pack_propagate(False)
        self._build_topbar()

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──
        self.sidebar = tk.Frame(body, bg=SIDEBAR_BG, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # ── Page container ──
        self.page_frame = tk.Frame(body, bg=BG)
        self.page_frame.pack(side="left", fill="both", expand=True)

        # ── Statusbar ──
        self.status_var = tk.StringVar(value="Ready")
        sb = tk.Frame(self.root, bg=SIDEBAR_BG, height=26)
        sb.pack(side="bottom", fill="x")
        sb.pack_propagate(False)
        tk.Label(sb, textvariable=self.status_var, font=FONT_S,
                 fg=MUTED, bg=SIDEBAR_BG, anchor="w", padx=12).pack(fill="x", pady=4)

        # Build all pages (hidden initially)
        self.pages = {}
        self._build_page_dashboard()
        self._build_page_add()
        self._build_page_history()
        self._build_page_budgets()
        self._build_page_analytics()
        self._build_page_tools()

    # ──────────────── TOPBAR ────────────────

    def _build_topbar(self):
        # Logo / title
        tk.Label(self.topbar, text="  💰 ExpenseMate",
                 font=("Segoe UI", 14, "bold"), fg=TEXT,
                 bg=SIDEBAR_BG).pack(side="left", padx=10, pady=10)

        Separator(self.topbar, orient="v").pack(side="left", fill="y", pady=8)

        # Date badge
        tk.Label(self.topbar,
                 text=f"  {datetime.today().strftime('%A, %d %B %Y')}",
                 font=FONT_S, fg=MUTED, bg=SIDEBAR_BG).pack(side="left", padx=12)

        # Quick action buttons on the right
        StyledButton(self.topbar, "＋ Add Transaction",
                     command=lambda: self._show_page("add"),
                     color=ACCENT, pady=5).pack(side="right", padx=12, pady=10)

    # ──────────────── SIDEBAR NAV ────────────────

    NAV_ITEMS = [
        ("dashboard", "🏠  Dashboard"),
        ("add",       "➕  Add Transaction"),
        ("history",   "📋  History"),
        ("budgets",   "🎯  Budgets & Alerts"),
        ("analytics", "📈  Analytics"),
        ("tools",     "⚙️  Tools & Backup"),
    ]

    def _build_sidebar(self):
        tk.Frame(self.sidebar, bg=SIDEBAR_BG, height=12).pack()
        self._nav_btns = {}
        for key, label in self.NAV_ITEMS:
            btn = tk.Button(self.sidebar, text=label, font=FONT_N,
                            fg=MUTED, bg=SIDEBAR_BG, activebackground=BORDER,
                            activeforeground=TEXT, relief="flat",
                            anchor="w", padx=20, pady=11,
                            cursor="hand2",
                            command=lambda k=key: self._show_page(k))
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BORDER, fg=TEXT)
                     if b is not self._active_nav else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=SIDEBAR_BG, fg=MUTED)
                     if b is not self._active_nav else None)
            self._nav_btns[key] = btn

        Separator(self.sidebar).pack(fill="x", pady=12, padx=16)

        # Version badge
        tk.Label(self.sidebar, text="v2.0 — Assignment 02",
                 font=("Segoe UI", 8), fg=BORDER, bg=SIDEBAR_BG).pack(side="bottom", pady=10)

    def _show_page(self, key):
        # Deactivate old nav btn
        if self._active_nav:
            self._active_nav.config(bg=SIDEBAR_BG, fg=MUTED)

        self._active_nav = self._nav_btns[key]
        self._active_nav.config(bg=ACCENT, fg=TEXT)

        # Hide all pages
        for f in self.pages.values():
            f.pack_forget()

        # Show requested page
        self.pages[key].pack(fill="both", expand=True)

        # Refresh data
        refreshers = {
            "dashboard": self._refresh_dashboard,
            "history":   self._refresh_history,
            "budgets":   self._refresh_budgets,
            "analytics": self._refresh_analytics,
        }
        if key in refreshers:
            refreshers[key]()

    # ──────────────────────────────────────────────
    #  PAGE 1 — DASHBOARD
    # ──────────────────────────────────────────────

    def _build_page_dashboard(self):
        p = tk.Frame(self.page_frame, bg=BG)
        self.pages["dashboard"] = p

        # Page title row
        title_bar = tk.Frame(p, bg=BG)
        title_bar.pack(fill="x", padx=24, pady=(20, 4))
        Label(title_bar, "Dashboard", font=FONT_H1).pack(side="left")
        Label(title_bar, "Financial overview at a glance",
              font=FONT_S, fg=MUTED).pack(side="left", padx=12, pady=4)

        # Month filter
        flt = tk.Frame(p, bg=BG)
        flt.pack(fill="x", padx=24, pady=(0, 16))
        Label(flt, "Period:", fg=MUTED).pack(side="left")
        self._dash_month = tk.StringVar(value=datetime.today().strftime("%Y-%m"))
        StyledEntry(flt, textvariable=self._dash_month, width=10).pack(side="left", padx=8)
        StyledButton(flt, "Refresh", command=self._refresh_dashboard,
                     color=CARD2_BG, pady=5).pack(side="left")
        StyledButton(flt, "All Time",
                     command=lambda: (self._dash_month.set(""), self._refresh_dashboard()),
                     color=CARD2_BG, pady=5).pack(side="left", padx=6)

        # KPI cards row
        kpi_row = tk.Frame(p, bg=BG)
        kpi_row.pack(fill="x", padx=24, pady=(0, 20))

        self._kpi_income = self._make_kpi_card(kpi_row, "Total Income",
                                                "PKR 0.00", SUCCESS, "↑")
        self._kpi_expense= self._make_kpi_card(kpi_row, "Total Expense",
                                                "PKR 0.00", DANGER, "↓")
        self._kpi_net    = self._make_kpi_card(kpi_row, "Net Balance",
                                                "PKR 0.00", ACCENT, "≡")
        self._kpi_txn    = self._make_kpi_card(kpi_row, "Transactions",
                                                "0", INFO, "#")

        # Bottom section: alerts + recent transactions side by side
        bottom = tk.Frame(p, bg=BG)
        bottom.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Recent Transactions
        rc = Card(bottom, padx=0, pady=0)
        rc.pack(side="left", fill="both", expand=True, padx=(0, 10))
        hdr = tk.Frame(rc, bg=CARD_BG)
        hdr.pack(fill="x", padx=16, pady=12)
        Label(hdr, "Recent Transactions", font=FONT_H3, bg=CARD_BG).pack(side="left")

        cols = ("Date", "Category", "Type", "Amount")
        self._dash_tree = ttk.Treeview(rc, columns=cols, show="headings",
                                        height=10, style="Dark.Treeview")
        for col, w in zip(cols, [100, 140, 90, 110]):
            self._dash_tree.heading(col, text=col)
            anch = "e" if col == "Amount" else "w"
            self._dash_tree.column(col, width=w, anchor=anch)
        self._dash_tree.tag_configure("income",  foreground=SUCCESS)
        self._dash_tree.tag_configure("expense", foreground=DANGER)
        self._dash_tree.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # Budget Alerts panel
        ac = Card(bottom, padx=0, pady=0, bg=CARD_BG)
        ac.pack(side="left", fill="both", expand=True)
        ahdr = tk.Frame(ac, bg=CARD_BG)
        ahdr.pack(fill="x", padx=16, pady=12)
        Label(ahdr, "🔔 Budget Alerts", font=FONT_H3, bg=CARD_BG).pack(side="left")

        self._dash_alerts = tk.Frame(ac, bg=CARD_BG)
        self._dash_alerts.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _make_kpi_card(self, parent, title, value_txt, color, icon):
        card = tk.Frame(parent, bg=CARD_BG, padx=20, pady=16)
        card.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Accent stripe
        stripe = tk.Frame(card, bg=color, width=4)
        stripe.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(side="left", fill="both", expand=True, padx=14)

        icon_lbl = tk.Label(inner, text=icon, font=("Segoe UI", 22, "bold"),
                             fg=color, bg=CARD_BG)
        icon_lbl.pack(anchor="w")

        val_lbl = tk.Label(inner, text=value_txt,
                           font=("Segoe UI", 15, "bold"), fg=TEXT, bg=CARD_BG)
        val_lbl.pack(anchor="w", pady=(2, 0))

        tk.Label(inner, text=title, font=FONT_S, fg=MUTED, bg=CARD_BG).pack(anchor="w")

        return val_lbl  # reference to update later

    def _refresh_dashboard(self):
        month = self._dash_month.get().strip() or None
        try:
            s = self.controller.get_financial_summary(month)
            self._kpi_income.config(text=f"PKR {s['total_income']:,.0f}")
            self._kpi_expense.config(text=f"PKR {s['total_expense']:,.0f}")
            net = s["net_savings"]
            self._kpi_net.config(text=f"PKR {net:,.0f}",
                                  fg=SUCCESS if net >= 0 else DANGER)

            txns = self.controller.list_transactions()
            self._kpi_txn.config(text=str(len(txns)))

            # Recent 20
            for c in self._dash_tree.get_children():
                self._dash_tree.delete(c)
            for t in txns[:20]:
                self._dash_tree.insert("", "end",
                    values=(t.date, t.category, t.trans_type.upper(),
                            f"{t.amount:,.2f}"),
                    tags=(t.trans_type,))

            # Alerts
            for w in self._dash_alerts.winfo_children():
                w.destroy()
            eval_month = month or datetime.today().strftime("%Y-%m")
            statuses = self.controller.get_budget_statuses(eval_month)
            if not statuses:
                Label(self._dash_alerts, "No budgets set for this period.",
                      fg=MUTED, bg=CARD_BG).pack(pady=20)
            for st in statuses:
                self._make_alert_row(self._dash_alerts, st)

            self.status_var.set(f"Dashboard refreshed  ·  {datetime.now().strftime('%H:%M:%S')}")
        except Exception as err:
            messagebox.showerror("Dashboard Error", str(err))

    def _make_alert_row(self, parent, st):
        color = {
            "CRITICAL": DANGER,
            "WARNING":  WARNING_C,
            "NORMAL":   SUCCESS,
        }.get(st.level, INFO)

        row = tk.Frame(parent, bg=CARD2_BG, pady=10, padx=12)
        row.pack(fill="x", pady=4)

        badge = tk.Frame(row, bg=color, width=6)
        badge.pack(side="left", fill="y")

        inner = tk.Frame(row, bg=CARD2_BG)
        inner.pack(side="left", fill="x", expand=True, padx=12)

        top_row = tk.Frame(inner, bg=CARD2_BG)
        top_row.pack(fill="x")
        tk.Label(top_row, text=st.category, font=FONT_B, fg=TEXT, bg=CARD2_BG).pack(side="left")
        tk.Label(top_row, text=st.level, font=FONT_S, fg=color, bg=CARD2_BG).pack(side="right")

        # Progress bar
        pct = min(st.percentage, 100)
        prog_style = ("Red" if st.level == "CRITICAL" else
                      "Amber" if st.level == "WARNING" else "Green")
        bar = ttk.Progressbar(inner, length=240, maximum=100,
                               value=pct,
                               style=f"{prog_style}.Horizontal.TProgressbar")
        bar.pack(fill="x", pady=4)

        tk.Label(inner,
                 text=f"PKR {st.spent:,.0f} / {st.limit:,.0f}  ({st.percentage:.1f}%)",
                 font=FONT_S, fg=MUTED, bg=CARD2_BG).pack(anchor="w")

    # ──────────────────────────────────────────────
    #  PAGE 2 — ADD TRANSACTION
    # ──────────────────────────────────────────────

    def _build_page_add(self):
        p = tk.Frame(self.page_frame, bg=BG)
        self.pages["add"] = p

        # Title
        title_bar = tk.Frame(p, bg=BG)
        title_bar.pack(fill="x", padx=24, pady=(20, 16))
        Label(title_bar, "Add Transaction", font=FONT_H1).pack(side="left")

        # Centered form card
        wrapper = tk.Frame(p, bg=BG)
        wrapper.pack(expand=True)

        form = Card(wrapper, bg=CARD_BG, padx=40, pady=36)
        form.pack(padx=60, pady=20, ipadx=20)

        Label(form, "Record a new income or expense entry",
              fg=MUTED, bg=CARD_BG).pack(pady=(0, 20))
        Separator(form).pack(fill="x", pady=(0, 24))

        def field_row(label, widget_fn):
            row = tk.Frame(form, bg=CARD_BG)
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label, font=FONT_B, fg=MUTED, bg=CARD_BG,
                     width=20, anchor="w").pack(side="left")
            w = widget_fn(row)
            w.pack(side="left", fill="x", expand=True)
            return w

        # Transaction Type (radio buttons)
        type_row = tk.Frame(form, bg=CARD_BG)
        type_row.pack(fill="x", pady=8)
        tk.Label(type_row, text="Transaction Type", font=FONT_B, fg=MUTED,
                 bg=CARD_BG, width=20, anchor="w").pack(side="left")
        self._add_type = tk.StringVar(value="expense")
        for val, label, color in [("expense","💸  Expense",DANGER),
                                   ("income", "💰  Income", SUCCESS)]:
            rb = tk.Radiobutton(type_row, text=label, variable=self._add_type,
                                value=val, bg=CARD_BG, fg=TEXT,
                                activebackground=CARD_BG, activeforeground=TEXT,
                                selectcolor=CARD2_BG, font=FONT_N,
                                indicatoron=False, padx=16, pady=8,
                                relief="flat", cursor="hand2",
                                bd=1)
            rb.pack(side="left", padx=5)
            rb.bind("<ButtonRelease-1>", lambda e, r=rb, c=color: r.config(fg=c))

        # Amount
        self._add_amount = tk.StringVar()
        field_row("Amount (PKR)", lambda p:
            StyledEntry(p, textvariable=self._add_amount,
                        placeholder="e.g. 5000", width=28))

        # Category
        self._add_cat = tk.StringVar(value="Food")
        field_row("Category", lambda p:
            StyledCombo(p, textvariable=self._add_cat, width=26,
                        values=["Food","Groceries","Rent","Salary","Utilities",
                                "Travel","Shopping","Entertainment","Freelance",
                                "Healthcare","Education","Transport","Other"]))

        # Date
        self._add_date = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        field_row("Date (YYYY-MM-DD)", lambda p:
            StyledEntry(p, textvariable=self._add_date, width=28))

        # Description
        self._add_desc = tk.StringVar()
        field_row("Description", lambda p:
            StyledEntry(p, textvariable=self._add_desc,
                        placeholder="Optional note…", width=28))

        Separator(form).pack(fill="x", pady=24)

        btn_row = tk.Frame(form, bg=CARD_BG)
        btn_row.pack()
        StyledButton(btn_row, "  💾  Save Transaction  ",
                     command=self._submit_add, color=ACCENT, pady=10).pack(side="left", padx=8)
        StyledButton(btn_row, "Clear",
                     command=self._clear_add, color=CARD2_BG, pady=10).pack(side="left")

        # Result label
        self._add_result_var = tk.StringVar()
        self._add_result_lbl = tk.Label(form, textvariable=self._add_result_var,
                                         font=FONT_B, fg=SUCCESS, bg=CARD_BG)
        self._add_result_lbl.pack(pady=8)

    def _clear_add(self):
        self._add_amount.set("")
        self._add_desc.set("")
        self._add_date.set(datetime.today().strftime("%Y-%m-%d"))
        self._add_result_var.set("")

    def _submit_add(self):
        self._add_result_var.set("")
        try:
            amt_raw = self._add_amount.get().strip()
            result = self.controller.add_transaction(
                amount=amt_raw,
                category=self._add_cat.get().strip(),
                trans_type=self._add_type.get(),
                date=self._add_date.get().strip(),
                description=self._add_desc.get().strip(),
            )
            tid = result["transaction_id"]
            self._add_result_var.set(f"✔  Transaction #{tid} saved successfully!")
            self._add_result_lbl.config(fg=SUCCESS)

            alert = result.get("alert")
            if alert and alert.level in ("WARNING", "CRITICAL"):
                messagebox.showwarning(
                    f"Budget {alert.level}",
                    f"{alert.message}"
                )
            self._clear_add()
        except Exception as err:
            self._add_result_var.set(f"✘  {err}")
            self._add_result_lbl.config(fg=DANGER)

    # ──────────────────────────────────────────────
    #  PAGE 3 — HISTORY
    # ──────────────────────────────────────────────

    def _build_page_history(self):
        p = tk.Frame(self.page_frame, bg=BG)
        self.pages["history"] = p

        title_bar = tk.Frame(p, bg=BG)
        title_bar.pack(fill="x", padx=24, pady=(20, 10))
        Label(title_bar, "Transactions History", font=FONT_H1).pack(side="left")

        # Filter bar
        flt = Card(p, bg=CARD_BG, padx=16, pady=12)
        flt.pack(fill="x", padx=24, pady=(0, 12))
        Label(flt, "Type:", fg=MUTED, bg=CARD_BG).pack(side="left")
        self._hist_type = tk.StringVar(value="All")
        StyledCombo(flt, textvariable=self._hist_type, width=10,
                    values=["All","income","expense"]).pack(side="left", padx=8)
        Label(flt, "Category:", fg=MUTED, bg=CARD_BG).pack(side="left")
        self._hist_cat = tk.StringVar()
        StyledEntry(flt, textvariable=self._hist_cat, width=16).pack(side="left", padx=8)
        StyledButton(flt, "Apply Filter", command=self._refresh_history,
                     color=ACCENT, pady=5).pack(side="left", padx=8)
        StyledButton(flt, "Reset",
                     command=lambda: (self._hist_type.set("All"),
                                      self._hist_cat.set(""),
                                      self._refresh_history()),
                     color=CARD2_BG, pady=5).pack(side="left")

        # Count badge
        self._hist_count_var = tk.StringVar(value="0 records")
        tk.Label(flt, textvariable=self._hist_count_var,
                 font=FONT_S, fg=MUTED, bg=CARD_BG).pack(side="right", padx=8)

        # Table
        table_frame = Card(p, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        cols = ("ID","Date","Type","Category","Amount (PKR)","Description")
        self._hist_tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                        style="Dark.Treeview")
        widths = [55, 110, 90, 150, 130, 400]
        anchors = ["c","c","c","w","e","w"]
        for col, w, a in zip(cols, widths, anchors):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w, anchor=a, minwidth=w)

        self._hist_tree.tag_configure("income",  foreground=SUCCESS)
        self._hist_tree.tag_configure("expense", foreground=DANGER)
        self._hist_tree.tag_configure("alt", background="#222d3d")

        sb = ttk.Scrollbar(table_frame, orient="vertical",
                           command=self._hist_tree.yview,
                           style="Dark.Vertical.TScrollbar")
        self._hist_tree.configure(yscrollcommand=sb.set)
        self._hist_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _refresh_history(self):
        for c in self._hist_tree.get_children():
            self._hist_tree.delete(c)
        tt   = self._hist_type.get()
        cat  = self._hist_cat.get().strip() or None
        txns = self.controller.list_transactions(
            trans_type=None if tt == "All" else tt,
            category=cat
        )
        self._hist_count_var.set(f"{len(txns)} records")
        for i, t in enumerate(txns):
            tags = (t.trans_type,) + (("alt",) if i % 2 else ())
            self._hist_tree.insert("", "end", tags=tags,
                values=(t.id, t.date, t.trans_type.upper(),
                        t.category, f"{t.amount:,.2f}", t.description))
        self.status_var.set(f"Loaded {len(txns)} transactions")

    # ──────────────────────────────────────────────
    #  PAGE 4 — BUDGETS & ALERTS
    # ──────────────────────────────────────────────

    def _build_page_budgets(self):
        p = tk.Frame(self.page_frame, bg=BG)
        self.pages["budgets"] = p

        title_bar = tk.Frame(p, bg=BG)
        title_bar.pack(fill="x", padx=24, pady=(20, 16))
        Label(title_bar, "Budgets & Alerts", font=FONT_H1).pack(side="left")

        # Set budget card
        sb_card = Card(p, bg=CARD_BG, padx=24, pady=20)
        sb_card.pack(fill="x", padx=24, pady=(0, 16))
        Label(sb_card, "Set / Update Monthly Budget", font=FONT_H3, bg=CARD_BG).pack(anchor="w")
        Separator(sb_card).pack(fill="x", pady=12)

        row = tk.Frame(sb_card, bg=CARD_BG)
        row.pack(fill="x")
        for lbl, var_name, widget_fn in [
            ("Category",          "_b_cat",   lambda p: StyledCombo(p, textvariable=self._b_cat, width=16,
                                                values=["Food","Rent","Groceries","Utilities","Travel",
                                                        "Shopping","Entertainment","Healthcare","Other"])),
            ("Monthly Limit (PKR)", "_b_limit", lambda p: StyledEntry(p, textvariable=self._b_limit, width=16)),
            ("Month (YYYY-MM)",   "_b_month", lambda p: StyledEntry(p, textvariable=self._b_month, width=12)),
        ]:
            tk.Label(row, text=lbl, font=FONT_S, fg=MUTED, bg=CARD_BG).pack(side="left", padx=(0,4))
        # Create vars
        self._b_cat   = tk.StringVar(value="Food")
        self._b_limit = tk.StringVar()
        self._b_month = tk.StringVar(value=datetime.today().strftime("%Y-%m"))

        # Rebuild row properly
        for w in row.winfo_children():
            w.destroy()
        for lbl, var, wfn in [
            ("Category",          self._b_cat,   lambda p: StyledCombo(p, textvariable=self._b_cat, width=16,
                                                    values=["Food","Rent","Groceries","Utilities","Travel",
                                                            "Shopping","Entertainment","Healthcare","Other"])),
            ("Limit (PKR)",        self._b_limit, lambda p: StyledEntry(p, textvariable=self._b_limit, width=14,
                                                    placeholder="e.g. 10000")),
            ("Month (YYYY-MM)",   self._b_month, lambda p: StyledEntry(p, textvariable=self._b_month, width=12)),
        ]:
            tk.Label(row, text=lbl, font=FONT_S, fg=MUTED, bg=CARD_BG).pack(side="left", padx=(12,4))
            wfn(row).pack(side="left")

        StyledButton(row, "  💾 Save Budget  ", command=self._submit_budget,
                     color=ACCENT, pady=5).pack(side="left", padx=16)

        self._budget_msg = tk.StringVar()
        tk.Label(sb_card, textvariable=self._budget_msg,
                 font=FONT_S, fg=SUCCESS, bg=CARD_BG).pack(anchor="w", pady=(8,0))

        # Status table
        st_card = Card(p, padx=0, pady=0)
        st_card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        st_hdr = tk.Frame(st_card, bg=CARD_BG, padx=16, pady=12)
        st_hdr.pack(fill="x")
        Label(st_hdr, "Live Budget Monitor", font=FONT_H3, bg=CARD_BG).pack(side="left")
        StyledButton(st_hdr, "↻ Refresh", command=self._refresh_budgets,
                     color=CARD2_BG, pady=4).pack(side="right")

        cols = ("Category","Limit","Spent","Remaining","% Used","Status")
        self._bud_tree = ttk.Treeview(st_card, columns=cols, show="headings",
                                       height=12, style="Dark.Treeview")
        for col, w, a in zip(cols, [140,120,120,120,80,300],
                             ["w","e","e","e","c","w"]):
            self._bud_tree.heading(col, text=col)
            self._bud_tree.column(col, width=w, anchor=a)

        self._bud_tree.tag_configure("CRITICAL", foreground=DANGER)
        self._bud_tree.tag_configure("WARNING",  foreground=WARNING_C)
        self._bud_tree.tag_configure("NORMAL",   foreground=SUCCESS)

        sb2 = ttk.Scrollbar(st_card, orient="vertical",
                            command=self._bud_tree.yview,
                            style="Dark.Vertical.TScrollbar")
        self._bud_tree.configure(yscrollcommand=sb2.set)
        self._bud_tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb2.pack(side="right", fill="y")

    def _submit_budget(self):
        self._budget_msg.set("")
        try:
            limit = float(self._b_limit.get().strip())
            self.controller.set_budget(self._b_cat.get(), limit, self._b_month.get().strip())
            self._budget_msg.set(f"✔  Budget saved: {self._b_cat.get()} = PKR {limit:,.2f}")
            self._b_limit.set("")
            self._refresh_budgets()
        except Exception as err:
            self._budget_msg.set(f"✘  {err}")

    def _refresh_budgets(self):
        for c in self._bud_tree.get_children():
            self._bud_tree.delete(c)
        try:
            my = self._b_month.get().strip() or datetime.today().strftime("%Y-%m")
            statuses = self.controller.get_budget_statuses(my)
            for st in statuses:
                rem = max(0.0, st.limit - st.spent)
                self._bud_tree.insert("", "end",
                    values=(st.category, f"{st.limit:,.2f}", f"{st.spent:,.2f}",
                            f"{rem:,.2f}", f"{st.percentage:.1f}%", st.message),
                    tags=(st.level,))
            self.status_var.set(f"Loaded {len(statuses)} budgets for {my}")
        except Exception as err:
            messagebox.showerror("Error", str(err))

    # ──────────────────────────────────────────────
    #  PAGE 5 — ANALYTICS
    # ──────────────────────────────────────────────

    def _build_page_analytics(self):
        p = tk.Frame(self.page_frame, bg=BG)
        self.pages["analytics"] = p

        title_bar = tk.Frame(p, bg=BG)
        title_bar.pack(fill="x", padx=24, pady=(20, 10))
        Label(title_bar, "Visual Analytics", font=FONT_H1).pack(side="left")

        flt = tk.Frame(p, bg=BG)
        flt.pack(fill="x", padx=24, pady=(0, 12))
        Label(flt, "Filter Month (YYYY-MM):", fg=MUTED).pack(side="left")
        self._ana_month = tk.StringVar()
        StyledEntry(flt, textvariable=self._ana_month, width=12,
                    placeholder="Leave blank = all").pack(side="left", padx=8)
        StyledButton(flt, "Generate ↗", command=self._refresh_analytics,
                     color=ACCENT, pady=5).pack(side="left")

        # Two-column layout
        cols_frame = tk.Frame(p, bg=BG)
        cols_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # LEFT: Trends table
        left = Card(cols_frame, padx=0, pady=0)
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        tk.Frame(left, bg=CARD_BG, height=10).pack()
        Label(left, "  Monthly Trends", font=FONT_H3, bg=CARD_BG).pack(anchor="w", padx=16)
        Separator(left).pack(fill="x", padx=16, pady=8)

        cols = ("Month","Income","Expense","Net Savings")
        self._ana_tree = ttk.Treeview(left, columns=cols, show="headings",
                                       style="Dark.Treeview")
        for col, w, a in zip(cols, [100,120,120,120], ["c","e","e","e"]):
            self._ana_tree.heading(col, text=col)
            self._ana_tree.column(col, width=w, anchor=a)
        self._ana_tree.tag_configure("pos", foreground=SUCCESS)
        self._ana_tree.tag_configure("neg", foreground=DANGER)
        self._ana_tree.pack(fill="both", expand=True, padx=1, pady=1)

        # RIGHT: ASCII chart in dark text box
        right = Card(cols_frame, padx=0, pady=0)
        right.pack(side="left", fill="both", expand=True)

        tk.Frame(right, bg=CARD_BG, height=10).pack()
        Label(right, "  Expense Category Breakdown", font=FONT_H3, bg=CARD_BG).pack(anchor="w", padx=16)
        Separator(right).pack(fill="x", padx=16, pady=8)

        self._chart_txt = tk.Text(right, font=FONT_MONO,
                                   bg="#0d1117", fg="#c9d1d9",
                                   insertbackground=TEXT,
                                   relief="flat", wrap="none",
                                   state="disabled")
        self._chart_txt.pack(fill="both", expand=True, padx=1, pady=1)

        # Tag colors for chart
        self._chart_txt.tag_configure("header", foreground=ACCENT,
                                       font=("Consolas", 9, "bold"))
        self._chart_txt.tag_configure("bar",    foreground=INFO)
        self._chart_txt.tag_configure("pct",    foreground=WARNING_C)

    def _refresh_analytics(self):
        month = self._ana_month.get().strip() or None
        try:
            # Trends
            for c in self._ana_tree.get_children():
                self._ana_tree.delete(c)
            trends = self.controller.get_monthly_trends()
            for my, v in trends.items():
                tag = "pos" if v["savings"] >= 0 else "neg"
                self._ana_tree.insert("", "end", tags=(tag,),
                    values=(my, f"{v['income']:,.0f}",
                            f"{v['expense']:,.0f}",
                            f"{v['savings']:,.0f}"))

            # Category chart
            res = self.controller.get_category_analytics("expense", month)
            self._chart_txt.config(state="normal")
            self._chart_txt.delete("1.0", "end")
            chart = res["chart"]
            for line in chart.split("\n"):
                if "===" in line:
                    self._chart_txt.insert("end", line + "\n", "header")
                elif "█" in line:
                    # Colour bar segments differently
                    idx = line.find("█")
                    self._chart_txt.insert("end", line[:idx], "")
                    idx2 = line.rfind("█") + 1
                    self._chart_txt.insert("end", line[idx:idx2], "bar")
                    self._chart_txt.insert("end", line[idx2:] + "\n", "pct")
                else:
                    self._chart_txt.insert("end", line + "\n")
            self._chart_txt.config(state="disabled")

            self.status_var.set("Analytics refreshed")
        except Exception as err:
            messagebox.showerror("Analytics Error", str(err))

    # ──────────────────────────────────────────────
    #  PAGE 6 — TOOLS & BACKUP
    # ──────────────────────────────────────────────

    def _build_page_tools(self):
        p = tk.Frame(self.page_frame, bg=BG)
        self.pages["tools"] = p

        title_bar = tk.Frame(p, bg=BG)
        title_bar.pack(fill="x", padx=24, pady=(20, 16))
        Label(title_bar, "Tools & Backup", font=FONT_H1).pack(side="left")

        # Currency converter
        curr_card = Card(p, bg=CARD_BG, padx=24, pady=24)
        curr_card.pack(fill="x", padx=24, pady=(0, 16))
        Label(curr_card, "💱  Multi-Currency Converter", font=FONT_H2, bg=CARD_BG).pack(anchor="w")
        Separator(curr_card).pack(fill="x", pady=12)

        row = tk.Frame(curr_card, bg=CARD_BG)
        row.pack(fill="x")

        self._c_amt   = tk.StringVar(value="100")
        self._c_from  = tk.StringVar(value="USD")
        self._c_to    = tk.StringVar(value="PKR")
        CURRENCIES    = ["PKR","USD","EUR","GBP","AED","SAR"]

        for lbl, widget_fn in [
            ("Amount",   lambda f: StyledEntry(f, textvariable=self._c_amt, width=14)),
            ("From",     lambda f: StyledCombo(f, textvariable=self._c_from, width=8, values=CURRENCIES)),
            ("To",       lambda f: StyledCombo(f, textvariable=self._c_to,   width=8, values=CURRENCIES)),
        ]:
            tk.Label(row, text=lbl, font=FONT_S, fg=MUTED, bg=CARD_BG).pack(side="left", padx=(12,4))
            widget_fn(row).pack(side="left")

        StyledButton(row, "Convert →", command=self._convert_currency,
                     color=ACCENT, pady=5).pack(side="left", padx=16)

        self._c_result = tk.StringVar(value="Result will appear here")
        tk.Label(curr_card, textvariable=self._c_result,
                 font=("Segoe UI", 13, "bold"), fg=INFO, bg=CARD_BG).pack(anchor="w", pady=(12,0))

        # Data management
        data_card = Card(p, bg=CARD_BG, padx=24, pady=24)
        data_card.pack(fill="x", padx=24, pady=(0, 16))
        Label(data_card, "📂  Data Management", font=FONT_H2, bg=CARD_BG).pack(anchor="w")
        Separator(data_card).pack(fill="x", pady=12)

        btns = tk.Frame(data_card, bg=CARD_BG)
        btns.pack(fill="x")

        for text, icon, color, cmd in [
            ("Export to CSV",          "📥", SUCCESS,  self._export_csv),
            ("Import from CSV",         "📤", WARNING_C, self._import_csv),
            ("Backup Database",         "🗄️", INFO,     self._backup_db),
        ]:
            f = tk.Frame(btns, bg=CARD2_BG, padx=20, pady=20)
            f.pack(side="left", padx=8, pady=4, ipadx=10)
            tk.Label(f, text=icon, font=("Segoe UI", 24), bg=CARD2_BG).pack()
            tk.Label(f, text=text, font=FONT_B, fg=TEXT, bg=CARD2_BG).pack(pady=4)
            StyledButton(f, "Launch", command=cmd, color=color, pady=5).pack()

        self._tool_msg = tk.StringVar()
        tk.Label(data_card, textvariable=self._tool_msg,
                 font=FONT_B, fg=SUCCESS, bg=CARD_BG).pack(anchor="w", pady=(12,0))

    def _convert_currency(self):
        try:
            amt = float(self._c_amt.get())
            res = self.controller.convert_currency(amt, self._c_from.get(), self._c_to.get())
            self._c_result.config(fg=INFO)
            self._c_result.set(
                f"{amt:,.4f} {self._c_from.get()}  =  {res:,.4f} {self._c_to.get()}"
            )
        except Exception as err:
            self._c_result.set(f"Error: {err}")
            self._c_result.config(fg=DANGER)

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
            initialfile="expenses_export.csv",
        )
        if path:
            try:
                n = self.controller.export_csv(path)
                self._tool_msg.set(f"✔  Exported {n} transactions → {path}")
            except Exception as err:
                messagebox.showerror("Export Error", str(err))

    def _import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if path:
            try:
                s, e, msgs = self.controller.import_csv(path)
                self._tool_msg.set(f"✔  Imported {s} records, {e} errors")
                if e:
                    messagebox.showwarning("Import Issues",
                                           f"{e} row(s) failed:\n" + "\n".join(msgs[:5]))
            except Exception as err:
                messagebox.showerror("Import Error", str(err))

    def _backup_db(self):
        try:
            path = self.controller.backup_database()
            self._tool_msg.set(f"✔  Backup saved → {path}")
        except Exception as err:
            messagebox.showerror("Backup Error", str(err))

    # ──────────────── RUN ────────────────

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ExpenseMateGUI()
    app.run()
