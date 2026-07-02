"""
gui.py — Interfaz gráfica Mini CRM de servicio al cliente.
Arquitectura:
  root
   ├── header (fijo)
   ├── PANEL A — CLIENTE (fijo, fuera del scroll)
   ├── FILA 2 (fija, horizontal)
   │    ├── Panel C1 — Gestión PQRS activa (izquierda)
   │    └── Panel C2 — Bandeja global PQRS abiertas (derecha)
   ├── body_container (Canvas + Scrollbar)
   │    └── scrollable_frame
   │         ├── FILA 3 (horizontal)
   │         │    ├── Panel B — Historial PQRS del cliente (izquierda)
   │         │    └── Panel E — Nueva PQRS (derecha)
   │         └── FILA 4 — Panel D — Trazabilidad (ancho completo)
   └── pie (fijo)

Flujo:
  - Una sola PQRS activa a la vez.
  - Doble click en Treeview para cargar PQRS activa (evita cambios accidentales).
  - Confirmación solo al cambiar de cliente con gestión sin guardar.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ── PALETA CORPORATIVA ───────────────────────────────────────────────────────

C = {
    "bg":         "#F3F3F3",
    "surface":    "#FFFFFF",
    "surface2":   "#F8F8F8",
    "border":     "#DDDBDA",
    "accent":     "#0176D3",
    "accent_dk":  "#014486",
    "success":    "#2E844A",
    "warning":    "#C23934",
    "amber":      "#DD7A01",
    "purple":     "#7B2D8E",
    "lilac":      "#9B59B6",
    "text":       "#181818",
    "text_muted": "#706E6B",
    "header_bg":  "#F3F2F2",
    "row_alt":    "#FAFAF9",
    "sel":        "#D8EDFF",
}

PRIORIDAD_COLOR = {1: C["warning"], 2: C["amber"], 3: C["accent"], 4: C["text_muted"]}
ESTADO_COLOR = {
    "Abierta":    ("#D8EDFF", C["accent"]),
    "En_Proceso": ("#FFF3E0", C["amber"]),
    "Escalada":   ("#FFDEDE", C["warning"]),
    "Cerrada":    ("#EBF5EE", C["success"]),
}

FONT_TITLE  = ("Segoe UI", 15, "bold")
FONT_HEADER = ("Segoe UI", 10, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10, "bold")


def _apply_theme():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(".", background=C["bg"], foreground=C["text"],
                font=FONT_BODY, borderwidth=0, relief="flat")
    s.configure("Treeview",
        background=C["surface"], foreground=C["text"],
        fieldbackground=C["surface"], rowheight=26, font=FONT_BODY)
    s.configure("Treeview.Heading",
        background=C["header_bg"], foreground=C["text_muted"],
        font=("Segoe UI", 9, "bold"), relief="flat", padding=(8, 5))
    s.map("Treeview",
        background=[("selected", C["sel"])],
        foreground=[("selected", C["accent_dk"])])
    s.configure("Accent.TButton",
        background=C["accent"], foreground="#FFFFFF",
        font=("Segoe UI", 10, "bold"), padding=(14, 7))
    s.map("Accent.TButton", background=[("active", C["accent_dk"])])
    s.configure("Success.TButton",
        background=C["success"], foreground="#FFFFFF",
        font=("Segoe UI", 10, "bold"), padding=(14, 7))
    s.map("Success.TButton", background=[("active", "#1E5C33")])
    s.configure("Danger.TButton",
        background=C["warning"], foreground="#FFFFFF",
        font=("Segoe UI", 10, "bold"), padding=(14, 7))
    s.map("Danger.TButton", background=[("active", "#8E1A18")])
    s.configure("Purple.TButton",
        background=C["purple"], foreground="#FFFFFF",
        font=("Segoe UI", 10, "bold"), padding=(14, 7))
    s.map("Purple.TButton", background=[("active", "#5A1F6B")])
    s.configure("Lilac.TButton",
        background=C["lilac"], foreground="#FFFFFF",
        font=("Segoe UI", 10, "bold"), padding=(14, 7))
    s.map("Lilac.TButton", background=[("active", "#7D3C98")])
    s.configure("Ghost.TButton",
        background=C["surface"], foreground=C["accent"],
        font=("Segoe UI", 10, "bold"), padding=(12, 6),
        relief="solid", borderwidth=1)
    s.map("Ghost.TButton",
        background=[("active", C["sel"])],
        bordercolor=[("active", C["accent"])])
    s.configure("TCombobox",
        fieldbackground=C["surface"], background=C["surface"],
        foreground=C["text"], arrowcolor=C["accent"],
        padding=(7, 5), relief="solid", borderwidth=1)
    s.map("TCombobox",
        fieldbackground=[("readonly", C["surface"])],
        selectbackground=[("readonly", C["surface"])],
        selectforeground=[("readonly", C["text"])])
    s.configure("TCheckbutton", background=C["surface"], foreground=C["text"])
    s.configure("TSeparator", background=C["border"])
    s.configure("TScrollbar",
        background=C["border"], troughcolor=C["bg"],
        arrowcolor=C["text_muted"])


# ── WIDGETS REUTILIZABLES ────────────────────────────────────────────────────

def card(parent, **kw):
    return tk.Frame(parent, bg=C["surface"],
                    padx=kw.pop("padx", 16), pady=kw.pop("pady", 12),
                    highlightthickness=1, highlightbackground=C["border"], **kw)

def lbl(parent, text="", muted=False, header=False, **kw):
    font = FONT_HEADER if header else FONT_SMALL if muted else FONT_BODY
    fg = kw.pop("fg", C["text_muted"] if muted else C["text"])
    return tk.Label(parent, text=text, bg=C["surface"],
                    fg=fg, font=font, **kw)

def dark_entry(parent, **kw):
    return tk.Entry(parent, bg=C["surface"], fg=C["text"],
                    insertbackground=C["accent"], relief="solid",
                    font=FONT_BODY, highlightthickness=1,
                    highlightcolor=C["accent"], highlightbackground=C["border"], **kw)

def dark_text(parent, **kw):
    return tk.Text(parent, bg=C["surface2"], fg=C["text"],
                   insertbackground=C["accent"], relief="solid",
                   font=FONT_BODY, highlightthickness=1,
                   highlightcolor=C["accent"], highlightbackground=C["border"],
                   wrap="word", **kw)


# ── SCROLLABLE FRAME (general de la app) ─────────────────────────────────────

class ScrollableFrame(tk.Frame):
    """Contenedor con Canvas + Scrollbar vertical + bind de rueda del mouse."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)

        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=C["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            self._update_scrollregion
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw",
            tags="inner_frame"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel(self.canvas)

    def _update_scrollregion(self, event=None):
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig("inner_frame", width=event.width)

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel_up, add="+")
        widget.bind("<Button-5>", self._on_mousewheel_down, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_up(self, event):
        self.canvas.yview_scroll(-3, "units")

    def _on_mousewheel_down(self, event):
        self.canvas.yview_scroll(3, "units")


# ── HELPER: Treeview con scrollbars ──────────────────────────────────────────

def treeview_con_scroll(parent, columns, headers, height=6):
    frame = tk.Frame(parent, bg=C["surface"])
    vsb = ttk.Scrollbar(frame, orient="vertical")
    hsb = ttk.Scrollbar(frame, orient="horizontal")
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        selectmode="browse", height=height,
                        yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    for col, (label, w) in zip(columns, headers):
        tree.heading(col, text=label)
        tree.column(col, width=w, minwidth=40, anchor="center")
    return tree, frame


# ── VENTANA PRINCIPAL ────────────────────────────────────────────────────────

class VentanaPrincipal:
    def __init__(self, controlador):
        self._ctrl = controlador
        self._cliente_actual = None
        self._pqrs_activa = None       # dict de la PQRS activa actual
        self._gestion_sucia = False     # True si hay comentario sin guardar

        self._root = tk.Tk()
        self._root.title("SIGEC — Sistema Integral de Gestión de Experiencia del Cliente")
        self._root.geometry("1280x800")
        self._root.minsize(1024, 680)
        self._root.configure(bg=C["bg"])
        _apply_theme()
        self._build()

    # ── CONSTRUCCIÓN ──────────────────────────────────────────────────────

    def _build(self):
        # ── HEADER FIJO (Panel A + Panel C2) ──────────────────────────────
        header_fijo = tk.Frame(self._root, bg=C["bg"])
        header_fijo.pack(fill="x")

        # Cabecera decorativa
        cab = tk.Frame(header_fijo, bg=C["accent"], pady=10, padx=20)
        cab.pack(fill="x")
        tk.Label(cab, text="SIGEC — Gestión de Clientes y PQRS",
                 bg=C["accent"], fg="#FFFFFF", font=FONT_TITLE).pack(side="left")
        tk.Label(cab, text="Gestión PQRS  •  v4.0",
                 bg=C["accent"], fg="#D8EDFF", font=FONT_SMALL).pack(side="right")

        # ── ROW_FIXED: Panel A (izquierda) + Panel C2 (derecha) ───────────
        row_fixed = tk.Frame(header_fijo, bg=C["bg"])
        row_fixed.pack(fill="x", padx=14, pady=(0, 6))

        col_a = tk.Frame(row_fixed, bg=C["bg"])
        col_a.pack(side="left", fill="x", expand=True, padx=(0, 7))

        col_c2 = tk.Frame(row_fixed, bg=C["bg"])
        col_c2.pack(side="left", fill="x", expand=True, padx=(7, 0))

        self._build_panel_a(col_a)  # Cliente
        self._build_panel_c2(col_c2)  # Bandeja global PQRS abiertas

        # ── BODY SCROLLABLE (C1+E, B, D) ──────────────────────────────────
        self._scroll_frame = ScrollableFrame(self._root, bg=C["bg"])
        self._scroll_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        body = self._scroll_frame.scrollable_frame

        # ── FILA 1 BODY: C1 Gestión activa (izquierda) + E Nueva PQRS (derecha) ──
        row1_body = tk.Frame(body, bg=C["bg"])
        row1_body.pack(fill="x", pady=(0, 8))

        col_c1 = tk.Frame(row1_body, bg=C["bg"])
        col_c1.pack(side="left", fill="x", expand=True, padx=(0, 7), anchor="n")

        col_e = tk.Frame(row1_body, bg=C["bg"])
        col_e.pack(side="left", fill="x", expand=True, padx=(7, 0), anchor="n")

        self._build_panel_c1(col_c1)  # Gestión PQRS activa
        self._build_panel_e(col_e)    # Nueva PQRS

        # ── FILA 2 BODY: B Historial cliente ──────────────────────────────
        self._build_panel_b(body)

        # ── FILA 3 BODY: D Trazabilidad ───────────────────────────────────
        self._build_panel_d(body)

        # Forzar recálculo del scrollregion después de construir todo
        self._root.after(200, lambda: self._scroll_frame._update_scrollregion())

        # ── Pie ───────────────────────────────────────────────────────────
        pie = tk.Frame(self._root, bg=C["header_bg"], pady=4, padx=12)
        pie.pack(fill="x")
        tk.Label(pie, text="Busca un cliente por cédula para comenzar",
                 bg=C["header_bg"], fg=C["text_muted"], font=FONT_SMALL).pack(side="left")

    # ═══════════════════════════════════════════════════════════════════════
    # PANEL A — CLIENTE (fijo)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_panel_a(self, parent):
        c = card(parent)
        c.pack(fill="x", pady=(8, 6))

        lbl(c, "Cliente", header=True, fg=C["accent"]).pack(anchor="w", pady=(0, 6))

        # ── Fila 1: Cédula + Buscar + Crear ───────────────────────────────
        row1 = tk.Frame(c, bg=C["surface"])
        row1.pack(fill="x", pady=(0, 6))
        lbl(row1, "Cédula:", muted=True).pack(side="left", padx=(0, 6))
        self._ent_cedula = dark_entry(row1, width=16)
        self._ent_cedula.pack(side="left", padx=(0, 6))
        self._ent_cedula.bind("<Return>", lambda e: self._on_buscar_cliente())
        ttk.Button(row1, text="🔍 Buscar Cliente", style="Ghost.TButton",
                   command=self._on_buscar_cliente).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="+ Crear Cliente", style="Accent.TButton",
                   command=self._on_crear_cliente).pack(side="left")

        # ── Fila 2: Bloques CLIENTES | PQRS ───────────────────────────────
        row2 = tk.Frame(c, bg=C["surface"])
        row2.pack(fill="x", pady=(0, 6))

        # Bloque CLIENTES
        bloque_clientes = tk.Frame(row2, bg=C["surface"],
                                   highlightthickness=1, highlightbackground=C["border"],
                                   padx=10, pady=6)
        bloque_clientes.pack(side="left", padx=(0, 12))
        lbl(bloque_clientes, "CLIENTES", header=True,
            fg=C["success"]).pack(anchor="w", pady=(0, 4))
        btn_row_c = tk.Frame(bloque_clientes, bg=C["surface"])
        btn_row_c.pack()
        ttk.Button(btn_row_c, text="📥 Importar Clientes", style="Success.TButton",
                   command=self._on_importar_excel, width=18).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row_c, text="📄 Plantilla Clientes", style="Ghost.TButton",
                   command=self._on_descargar_plantilla, width=18).pack(side="left")

        # Bloque PQRS
        bloque_pqrs = tk.Frame(row2, bg=C["surface"],
                               highlightthickness=1, highlightbackground=C["border"],
                               padx=10, pady=6)
        bloque_pqrs.pack(side="left")
        lbl(bloque_pqrs, "PQRS", header=True,
            fg=C["purple"]).pack(anchor="w", pady=(0, 4))
        btn_row_p = tk.Frame(bloque_pqrs, bg=C["surface"])
        btn_row_p.pack()
        ttk.Button(btn_row_p, text="📥 Importar PQRS", style="Purple.TButton",
                   command=self._on_importar_pqrs_excel, width=18).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row_p, text="📄 Plantilla PQRS", style="Lilac.TButton",
                   command=self._on_descargar_plantilla_pqrs, width=18).pack(side="left")

        # ── Formulario cliente ────────────────────────────────────────────
        self._frame_cliente = tk.Frame(c, bg=C["surface"])
        self._frame_cliente.pack(fill="x", pady=(2, 0))

        # Fila: Nombre (ancho completo)
        row_nom = tk.Frame(self._frame_cliente, bg=C["surface"])
        row_nom.pack(fill="x", pady=1)
        lbl(row_nom, "Nombre", muted=True, width=8).pack(side="left")
        self._ent_nombre = dark_entry(row_nom)
        self._ent_nombre.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Fila: Teléfono + Correo
        row_tc = tk.Frame(self._frame_cliente, bg=C["surface"])
        row_tc.pack(fill="x", pady=1)
        f_tel = tk.Frame(row_tc, bg=C["surface"])
        f_tel.pack(side="left", padx=(0, 10))
        lbl(f_tel, "Teléfono", muted=True, width=8).pack(side="left")
        self._ent_tel = dark_entry(f_tel, width=18)
        self._ent_tel.pack(side="left", padx=(4, 0))
        f_cor = tk.Frame(row_tc, bg=C["surface"])
        f_cor.pack(side="left", fill="x", expand=True)
        lbl(f_cor, "Correo", muted=True, width=8).pack(side="left")
        self._ent_correo = dark_entry(f_cor)
        self._ent_correo.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Fila: Dirección (ancho completo)
        row_dir = tk.Frame(self._frame_cliente, bg=C["surface"])
        row_dir.pack(fill="x", pady=1)
        lbl(row_dir, "Dirección", muted=True, width=8).pack(side="left")
        self._ent_dir = dark_entry(row_dir)
        self._ent_dir.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Fila: Tipo Cliente
        row_tipo = tk.Frame(self._frame_cliente, bg=C["surface"])
        row_tipo.pack(fill="x", pady=1)
        lbl(row_tipo, "Tipo Cliente", muted=True, width=8).pack(side="left")
        self._cmb_tipo_cliente = ttk.Combobox(row_tipo, state="readonly", width=22,
            values=["", "Persona Natural", "Persona Jurídica", "VIP", "Corporativo"])
        self._cmb_tipo_cliente.current(0)
        self._cmb_tipo_cliente.pack(side="left", padx=(4, 0))

    # ═══════════════════════════════════════════════════════════════════════
    # PANEL C1 — GESTIÓN PQRS ACTIVA (fijo, izquierda)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_panel_c1(self, parent):
        c = card(parent)
        c.pack(fill="x", pady=(0, 8))

        lbl(c, "Gestión de PQRS Activa", header=True,
            fg=C["accent"]).pack(anchor="w", pady=(0, 4))

        # Fila operativa: buscar + atender + urgente
        row_ops = tk.Frame(c, bg=C["surface"])
        row_ops.pack(fill="x", pady=(0, 4))
        lbl(row_ops, "Radicado:", muted=True).pack(side="left", padx=(0, 6))
        self._ent_rad_buscar = dark_entry(row_ops, width=12)
        self._ent_rad_buscar.pack(side="left", padx=(0, 6))
        self._ent_rad_buscar.bind("<Return>", lambda e: self._on_buscar_pqrs())
        ttk.Button(row_ops, text="🔍 Buscar", style="Ghost.TButton",
                   command=self._on_buscar_pqrs).pack(side="left", padx=(0, 6))

        # Botones de acción con ancho fijo
        btn_frame = tk.Frame(row_ops, bg=C["surface"])
        btn_frame.pack(side="left", fill="x", expand=True)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        ttk.Button(btn_frame, text="⚡ Atender Siguiente", style="Success.TButton",
                   command=self._on_atender, width=18).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(btn_frame, text="🔥 Ver Más Urgente", style="Danger.TButton",
                   command=self._on_urgente, width=16).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        ttk.Separator(c, orient="horizontal").pack(fill="x", pady=2)

        # ── Detalle de la PQRS activa (compacto) ──────────────────────────
        self._frame_detalle = tk.Frame(c, bg=C["surface"])
        self._frame_detalle.pack(fill="x")

        # Cabecera: radicado + badge estado
        cab = tk.Frame(self._frame_detalle, bg=C["surface"])
        cab.pack(fill="x")
        self._lbl_rad_det = tk.Label(cab, text="—", bg=C["surface"],
                                     fg=C["accent_dk"], font=FONT_MONO)
        self._lbl_rad_det.pack(side="left")
        self._badge_det = tk.Label(cab, text="", font=FONT_SMALL,
                                   padx=6, pady=1, relief="flat")
        self._badge_det.pack(side="right")

        # Grid detalle compacto (pady=0)
        grid = tk.Frame(self._frame_detalle, bg=C["surface"])
        grid.pack(fill="x", pady=(2, 0))
        campos_detalle = [
            ("Tipo",        "_lbl_tipo_det"),
            ("Asunto",      "_lbl_asunto_det"),
            ("Descripción", "_lbl_desc_det"),
            ("Prioridad",   "_lbl_prio_det"),
            ("Canal",       "_lbl_canal_det"),
            ("Fecha",       "_lbl_fecha_det"),
        ]
        for i, (etq, attr) in enumerate(campos_detalle):
            lbl(grid, etq, muted=True).grid(row=i, column=0, sticky="w", pady=0)
            w = lbl(grid, "—")
            w.grid(row=i, column=1, sticky="w", padx=(16, 0))
            setattr(self, attr, w)

        ttk.Separator(self._frame_detalle, orient="horizontal").pack(fill="x", pady=3)

        # ── Gestión unificada (compacta) ──────────────────────────────────
        row_est = tk.Frame(self._frame_detalle, bg=C["surface"])
        row_est.pack(fill="x", pady=(0, 2))
        lbl(row_est, "Nuevo estado:", muted=True).pack(side="left", padx=(0, 6))
        self._cmb_estado_det = ttk.Combobox(row_est, state="readonly", width=14)
        self._cmb_estado_det.pack(side="left")

        lbl(self._frame_detalle, "Comentario:", muted=True).pack(anchor="w")
        self._txt_comentario = dark_text(self._frame_detalle, height=3)
        self._txt_comentario.pack(fill="x", pady=(1, 3))
        # Detectar escritura para marcar gestión sucia
        self._txt_comentario.bind("<KeyRelease>", lambda e: self._marcar_gestion_sucia())

        ttk.Button(self._frame_detalle, text="💾 Guardar Gestión",
                   style="Accent.TButton",
                   command=self._on_guardar_gestion).pack(anchor="e")

    # ═══════════════════════════════════════════════════════════════════════
    # PANEL C2 — BANDEJA GLOBAL PQRS ABIERTAS (fijo, derecha)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_panel_c2(self, parent):
        c = card(parent)
        c.pack(fill="x", pady=(0, 8))

        lbl(c, "PQRS Abiertas", header=True,
            fg=C["accent"]).pack(anchor="w", pady=(0, 6))

        cols = ("radicado", "tipo", "asunto", "prioridad", "estado", "fecha")
        hdrs = [("Radicado", 85), ("Tipo", 70), ("Asunto", 100),
                ("Prio", 40), ("Estado", 80), ("Fecha", 100)]

        self._tree_abiertas, frame_abiertas = treeview_con_scroll(
            c, cols, hdrs, height=6
        )
        frame_abiertas.pack(fill="x")
        # Doble click para cargar PQRS activa (evita cambios accidentales)
        self._tree_abiertas.bind("<Double-1>", self._on_dbl_click_pqrs_abierta)

    # ═══════════════════════════════════════════════════════════════════════
    # PANEL B — HISTORIAL PQRS DEL CLIENTE (scrollable, izquierda)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_panel_b(self, parent):
        c = card(parent)
        c.pack(fill="x", pady=(0, 8), anchor="n")

        lbl(c, "Historial del Cliente", header=True,
            fg=C["accent"]).pack(anchor="w", pady=(0, 4))

        cols = ("radicado", "tipo", "asunto", "prioridad", "estado", "fecha")
        hdrs = [("Radicado", 90), ("Tipo", 80), ("Asunto", 120),
                ("Prio", 45), ("Estado", 90), ("Fecha", 120)]

        self._tree_pqrs_cliente, frame_tree = treeview_con_scroll(
            c, cols, hdrs, height=5
        )
        frame_tree.pack(fill="x")
        # Doble click para cargar PQRS activa (evita cambios accidentales)
        self._tree_pqrs_cliente.bind("<Double-1>", self._on_dbl_click_pqrs_cliente)

    # ═══════════════════════════════════════════════════════════════════════
    # PANEL D — TRAZABILIDAD DE LA PQRS ACTIVA (scrollable, ancho completo)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_panel_d(self, parent):
        c = card(parent)
        c.pack(fill="both", expand=True, pady=(0, 8), anchor="n")

        lbl(c, "Trazabilidad", header=True,
            fg=C["accent"]).pack(anchor="w", pady=(0, 6))

        cols = ("fecha", "tipo", "estado_ant", "estado_nuevo", "comentario", "usuario")
        hdrs = [("Fecha", 140), ("Evento", 100), ("Anterior", 90),
                ("Nuevo", 90), ("Comentario", 300), ("Usuario", 90)]

        self._tree_hist, frame_tree = treeview_con_scroll(c, cols, hdrs, height=6)
        frame_tree.pack(fill="x", pady=(0, 6))

        # Tooltip
        self._tooltip_hist = None
        self._tree_hist.bind("<Motion>", self._on_hist_mouse_motion)
        self._tree_hist.bind("<Leave>", self._on_hist_mouse_leave)

        # Panel detalle del log
        ttk.Separator(c, orient="horizontal").pack(fill="x", pady=4)
        lbl(c, "Detalle del evento seleccionado", header=True,
            fg=C["accent"]).pack(anchor="w", pady=(0, 4))

        grid_log = tk.Frame(c, bg=C["surface"])
        grid_log.pack(fill="x", pady=(0, 4))
        self._lbl_log_tipo = lbl(grid_log, "Tipo: —", muted=True)
        self._lbl_log_tipo.grid(row=0, column=0, sticky="w", padx=(0, 20))
        self._lbl_log_usuario = lbl(grid_log, "Usuario: —", muted=True)
        self._lbl_log_usuario.grid(row=0, column=1, sticky="w")
        self._lbl_log_fecha = lbl(grid_log, "Fecha: —", muted=True)
        self._lbl_log_fecha.grid(row=0, column=2, sticky="w", padx=(20, 0))

        lbl(c, "Comentario completo:", muted=True).pack(anchor="w", pady=(2, 2))
        self._txt_log_comentario = dark_text(c, height=2, state="disabled")
        self._txt_log_comentario.pack(fill="x")

        self._tree_hist.bind("<<TreeviewSelect>>", self._on_sel_historial)

    # ═══════════════════════════════════════════════════════════════════════
    # PANEL E — NUEVA PQRS (scrollable, derecha)
    # ═══════════════════════════════════════════════════════════════════════

    def _build_panel_e(self, parent):
        c = card(parent)
        c.pack(fill="x", anchor="n")

        lbl(c, "Nueva PQRS", header=True, fg=C["accent"]).pack(anchor="w", pady=(0, 4))

        # Fila compacta: Tipo + Canal + Asunto
        row1 = tk.Frame(c, bg=C["surface"])
        row1.pack(fill="x", pady=(0, 4))

        col_tipo = tk.Frame(row1, bg=C["surface"])
        col_tipo.pack(side="left", padx=(0, 8))
        lbl(col_tipo, "Tipo", muted=True).pack(anchor="w")
        self._cmb_tipo_pqrs = ttk.Combobox(col_tipo, state="readonly",
                                            values=self._ctrl.tipos, width=12)
        self._cmb_tipo_pqrs.current(0)
        self._cmb_tipo_pqrs.pack()

        col_canal = tk.Frame(row1, bg=C["surface"])
        col_canal.pack(side="left", padx=(0, 8))
        lbl(col_canal, "Canal", muted=True).pack(anchor="w")
        self._cmb_canal = ttk.Combobox(col_canal, state="readonly", width=12,
            values=["", "Web", "Email", "Teléfono", "Presencial", "App"])
        self._cmb_canal.current(0)
        self._cmb_canal.pack()

        col_asunto = tk.Frame(row1, bg=C["surface"])
        col_asunto.pack(side="left", fill="x", expand=True)
        lbl(col_asunto, "Asunto", muted=True).pack(anchor="w")
        self._ent_asunto = dark_entry(col_asunto)
        self._ent_asunto.pack(fill="x")

        # Descripción
        lbl(c, "Descripción:", muted=True).pack(anchor="w", pady=(4, 2))
        self._txt_desc_pqrs = dark_text(c, height=3)
        self._txt_desc_pqrs.pack(fill="x", pady=(0, 6))

        ttk.Button(c, text="+ Crear PQRS", style="Accent.TButton",
                   command=self._on_crear_pqrs).pack(anchor="e")

    # ═══════════════════════════════════════════════════════════════════════
    # CALLBACKS: CLIENTES
    # ═══════════════════════════════════════════════════════════════════════

    def _on_buscar_cliente(self):
        cedula = self._ent_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Cédula requerida", "Ingresa una cédula para buscar.")
            return
        cliente = self._ctrl.buscar_cliente(cedula)
        if cliente is None:
            messagebox.showwarning("No encontrado",
                                   f"No existe cliente con cédula '{cedula}'.\nCréalo con el botón 'Crear Cliente'.")
            self._limpiar_cliente()
            return
        self._cargar_cliente(cliente)

    def _on_crear_cliente(self):
        cedula = self._ent_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Cédula requerida", "Ingresa la cédula primero.")
            return
        try:
            cliente = self._ctrl.registrar_cliente(
                cedula=cedula,
                nombre=self._ent_nombre.get().strip(),
                telefono=self._ent_tel.get().strip(),
                correo=self._ent_correo.get().strip(),
                direccion=self._ent_dir.get().strip(),
                tipo_cliente=self._cmb_tipo_cliente.get(),
            )
            self._cargar_cliente(cliente)
            messagebox.showinfo("Cliente creado",
                                f"Cliente '{cliente['nombre']}' registrado exitosamente.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _on_descargar_plantilla(self):
        """Descarga una plantilla Excel con los encabezados requeridos."""
        ruta = filedialog.asksaveasfilename(
            title="Guardar plantilla Excel",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
            initialfile="plantilla_clientes.xlsx"
        )
        if not ruta:
            return
        try:
            self._ctrl.descargar_plantilla_excel(ruta)
            messagebox.showinfo("Plantilla descargada",
                                f"Plantilla guardada en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la plantilla:\n{e}")

    def _on_descargar_plantilla_pqrs(self):
        """Descarga una plantilla Excel para importar PQRS."""
        ruta = filedialog.asksaveasfilename(
            title="Guardar plantilla PQRS Excel",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
            initialfile="plantilla_pqrs.xlsx"
        )
        if not ruta:
            return
        try:
            self._ctrl.descargar_plantilla_pqrs_excel(ruta)
            messagebox.showinfo("Plantilla descargada",
                                f"Plantilla PQRS guardada en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la plantilla:\n{e}")

    def _on_importar_excel(self):
        """Abre un diálogo para seleccionar archivo .xlsx e importa clientes."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return
        try:
            resumen = self._ctrl.importar_clientes_excel(ruta)
            msg = (
                f"✅ Importación completada\n\n"
                f"📌 Insertados: {resumen['insertados']}\n"
                f"🔄 Actualizados: {resumen['actualizados']}\n"
                f"❌ Errores:     {resumen['errores']}"
            )
            if resumen.get("detalles_errores"):
                msg += "\n\nDetalles de errores:\n" + "\n".join(resumen["detalles_errores"][:10])
            messagebox.showinfo("Resultado de importación", msg)
            if self._cliente_actual:
                self._refrescar_pqrs_cliente(self._cliente_actual["id"])
        except Exception as e:
            messagebox.showerror("Error de importación", f"No se pudo importar el archivo:\n{e}")

    def _on_importar_pqrs_excel(self):
        """Abre un diálogo para seleccionar archivo .xlsx e importa PQRS masivamente."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo Excel para importar PQRS",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return
        try:
            resumen = self._ctrl.importar_pqrs_excel(ruta)
            msg = (
                f"✅ Importación de PQRS completada\n\n"
                f"📌 Insertadas: {resumen['insertadas']}\n"
                f"❌ Errores:     {resumen['errores']}"
            )
            if resumen.get("detalles_errores"):
                msg += "\n\nDetalles de errores:\n" + "\n".join(resumen["detalles_errores"][:10])
            messagebox.showinfo("Resultado de importación PQRS", msg)
            if self._cliente_actual:
                self._refrescar_pqrs_cliente(self._cliente_actual["id"])
        except Exception as e:
            messagebox.showerror("Error de importación", f"No se pudo importar el archivo:\n{e}")

    def _cargar_cliente(self, cliente: dict, sincronizar_pqrs: bool = True):
        """Carga los datos de un cliente en el formulario y sincroniza paneles."""
        self._cliente_actual = cliente
        self._ent_cedula.delete(0, "end")
        self._ent_cedula.insert(0, cliente["cedula"])
        self._ent_nombre.delete(0, "end")
        self._ent_nombre.insert(0, cliente["nombre"] or "")
        self._ent_tel.delete(0, "end")
        self._ent_tel.insert(0, cliente["telefono"] or "")
        self._ent_correo.delete(0, "end")
        self._ent_correo.insert(0, cliente["correo"] or "")
        self._ent_dir.delete(0, "end")
        self._ent_dir.insert(0, cliente["direccion"] or "")
        if cliente["tipo_cliente"]:
            self._cmb_tipo_cliente.set(cliente["tipo_cliente"])
        else:
            self._cmb_tipo_cliente.current(0)
        if sincronizar_pqrs:
            self._refrescar_pqrs_cliente(cliente["id"])

    def _limpiar_cliente(self):
        self._cliente_actual = None
        for attr in ("_ent_nombre", "_ent_tel", "_ent_correo", "_ent_dir"):
            getattr(self, attr).delete(0, "end")
        self._cmb_tipo_cliente.current(0)
        for row in self._tree_pqrs_cliente.get_children():
            self._tree_pqrs_cliente.delete(row)

    def _refrescar_pqrs_cliente(self, cliente_id: int):
        for row in self._tree_pqrs_cliente.get_children():
            self._tree_pqrs_cliente.delete(row)
        lista = self._ctrl.listar_pqrs_cliente(cliente_id)
        for data in lista:
            self._tree_pqrs_cliente.insert("", "end", values=(
                data["radicado"], data["tipo"], data["asunto"],
                f"P{data['prioridad']}", data["estado"], data["fecha"],
            ))

    # ═══════════════════════════════════════════════════════════════════════
    # CALLBACKS: PQRS
    # ═══════════════════════════════════════════════════════════════════════

    def _on_crear_pqrs(self):
        if self._cliente_actual is None:
            messagebox.showwarning("Sin cliente",
                                   "Debes buscar o crear un cliente primero.")
            return
        desc = self._txt_desc_pqrs.get("1.0", "end").strip()
        try:
            data = self._ctrl.crear_pqrs(
                tipo=self._cmb_tipo_pqrs.get(),
                descripcion=desc,
                cliente_id=self._cliente_actual["id"],
                asunto=self._ent_asunto.get().strip(),
                canal_ingreso=self._cmb_canal.get(),
            )
            self._refrescar_pqrs_cliente(self._cliente_actual["id"])
            self._txt_desc_pqrs.delete("1.0", "end")
            self._ent_asunto.delete(0, "end")
            self._cmb_canal.current(0)
            messagebox.showinfo("PQRS Creada",
                                f"PQRS {data['radicado']} creada para {self._cliente_actual['nombre']}.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _on_buscar_pqrs(self):
        rad = self._ent_rad_buscar.get().strip()
        if not rad:
            return
        data = self._ctrl.buscar(rad)
        if data:
            self._cargar_pqrs_activa(data)
        else:
            messagebox.showwarning("No encontrada",
                                   f"No existe PQRS con radicado '{rad}'.")

    def _on_atender(self):
        """
        Atiende la siguiente PQRS.
        - Si PQRS activa está Cerrada → carga siguiente sin preguntar
        - Si PQRS activa NO está Cerrada → pregunta si desea cambiar
        """
        if self._pqrs_activa is not None and self._pqrs_activa["estado"] != "Cerrada":
            resp = messagebox.askyesno(
                "Cambiar PQRS activa",
                "La PQRS actual no está cerrada.\n"
                "¿Desea cambiar a la siguiente?"
            )
            if not resp:
                return

        data = self._ctrl.atender_siguiente()
        if data:
            self._cargar_pqrs_activa(data)
        else:
            messagebox.showwarning("Cola vacía", "No hay PQRS pendientes por atender.")

    def _on_urgente(self):
        data = self._ctrl.ver_mas_urgente()
        if data:
            self._cargar_pqrs_activa(data)
        else:
            messagebox.showwarning("Cola vacía", "No hay PQRS en cola.")

    def _on_dbl_click_pqrs_cliente(self, _=None):
        """Doble click en Panel B: carga la PQRS como activa."""
        sel = self._tree_pqrs_cliente.selection()
        if not sel:
            return
        rad = str(self._tree_pqrs_cliente.item(sel[0])["values"][0])
        data = self._ctrl.buscar(rad)
        if data:
            self._cargar_pqrs_activa(data)

    def _on_dbl_click_pqrs_abierta(self, _=None):
        """Doble click en Panel C2: carga la PQRS como activa."""
        sel = self._tree_abiertas.selection()
        if not sel:
            return
        rad = str(self._tree_abiertas.item(sel[0])["values"][0])
        data = self._ctrl.buscar(rad)
        if data:
            self._cargar_pqrs_activa(data)

    def _on_guardar_gestion(self):
        """
        Acción unificada: Guardar Gestión.
        - Si cambia estado: guarda cambio + comentario
        - Si mantiene estado: guarda comentario de seguimiento
        - Si estado actual = Abierta: NO permite mantener Abierta, debe pasar a En_Proceso mínimo
        """
        if self._pqrs_activa is None:
            messagebox.showwarning("Sin PQRS activa",
                                   "No hay una PQRS activa para gestionar.")
            return

        rad = self._pqrs_activa["radicado"]
        estado_actual = self._pqrs_activa["estado"]
        nuevo_estado = self._cmb_estado_det.get()
        comentario = self._txt_comentario.get("1.0", "end").strip()

        if not comentario:
            messagebox.showwarning("Comentario requerido",
                                   "Debe escribir un comentario para guardar la gestión.")
            return

        # Validación: si estado actual = Abierta, no permitir mantener Abierta
        if estado_actual == "Abierta" and nuevo_estado == "Abierta":
            messagebox.showwarning("Estado inválido",
                                   "Una PQRS en estado 'Abierta' debe pasar al menos a 'En_Proceso'.\n"
                                   "Seleccione un estado diferente.")
            return

        if nuevo_estado != estado_actual:
            # Cambio de estado + comentario
            ok = self._ctrl.cambiar_estado(rad, nuevo_estado, comentario=comentario)
            if ok:
                messagebox.showinfo("Gestión guardada",
                                    f"Estado cambiado a '{nuevo_estado}' y comentario registrado.")
            else:
                messagebox.showerror("Error", "No se pudo cambiar el estado.")
                return
        else:
            # Solo comentario de seguimiento
            ok = self._ctrl.agregar_comentario(rad, comentario)
            if ok:
                messagebox.showinfo("Gestión guardada",
                                    "Comentario de seguimiento registrado.")
            else:
                messagebox.showerror("Error", "No se pudo agregar el comentario.")
                return

        # Refrescar todo
        self._gestion_sucia = False
        self._txt_comentario.delete("1.0", "end")
        data = self._ctrl.buscar(rad)
        if data:
            self._cargar_pqrs_activa(data)

    # ═══════════════════════════════════════════════════════════════════════
    # HISTORIAL
    # ═══════════════════════════════════════════════════════════════════════

    def _on_sel_historial(self, _=None):
        """Al seleccionar un log en el historial, muestra detalle completo."""
        sel = self._tree_hist.selection()
        if not sel:
            return
        valores = self._tree_hist.item(sel[0])["values"]
        if len(valores) < 6:
            return
        fecha, tipo, ant, nuevo, comentario, usuario = valores[:6]
        self._lbl_log_tipo.config(text=f"Tipo: {tipo}")
        self._lbl_log_usuario.config(text=f"Usuario: {usuario}")
        self._lbl_log_fecha.config(text=f"Fecha: {fecha}")
        self._txt_log_comentario.config(state="normal")
        self._txt_log_comentario.delete("1.0", "end")
        self._txt_log_comentario.insert("1.0", comentario or "(sin comentario)")
        self._txt_log_comentario.config(state="disabled")

    def _refrescar_historial(self, radicado: str):
        """Refresca el Panel D con la trazabilidad de la PQRS activa (más reciente primero)."""
        for row in self._tree_hist.get_children():
            self._tree_hist.delete(row)
        logs = self._ctrl.ver_historial(radicado)
        # Mostrar más reciente primero (invertir orden)
        for log in reversed(logs):
            self._tree_hist.insert("", "end", values=(
                log["fecha_evento"],
                log["tipo_evento"],
                log["estado_anterior"] or "—",
                log["estado_nuevo"] or "—",
                log["comentario"] or "",
                log["usuario"] or "Sistema",
            ))

    # ═══════════════════════════════════════════════════════════════════════
    # SINCRONIZACIÓN
    # ═══════════════════════════════════════════════════════════════════════

    def _cargar_pqrs_activa(self, data: dict):
        """Carga una PQRS como activa y sincroniza todos los paneles."""
        self._pqrs_activa = data
        self._gestion_sucia = False

        # Panel C1: Detalle
        self._lbl_rad_det.config(text=data["radicado"])
        bg, fg = ESTADO_COLOR.get(data["estado"], (C["surface2"], C["text_muted"]))
        self._badge_det.config(text=f"  {data['estado']}  ", bg=bg, fg=fg)
        self._lbl_tipo_det.config(text=data["tipo"])
        self._lbl_asunto_det.config(text=data.get("asunto", "—"))
        self._lbl_desc_det.config(text=data.get("descripcion", "—"))
        pc = PRIORIDAD_COLOR.get(data["prioridad"], C["text_muted"])
        self._lbl_prio_det.config(text=f"P{data['prioridad']}", fg=pc)
        self._lbl_canal_det.config(text=data.get("canal_ingreso", "—"))
        self._lbl_fecha_det.config(text=data["fecha"])

        # Configurar combobox de estado
        self._cmb_estado_det.config(values=self._ctrl.estados)
        self._cmb_estado_det.set(data["estado"])

        # Limpiar comentario
        self._txt_comentario.delete("1.0", "end")

        # Panel A: Sincronizar cliente
        cliente = self._ctrl.buscar_cliente(data.get("cliente_cedula", ""))
        if cliente:
            self._cargar_cliente(cliente, sincronizar_pqrs=True)

        # Panel D: Trazabilidad
        self._refrescar_historial(data["radicado"])

        # Panel C2: Refrescar bandeja
        self._refrescar_bandeja_abiertas()

    def _refrescar_bandeja_abiertas(self):
        """Refresca la bandeja de PQRS Abiertas en Panel C2."""
        for row in self._tree_abiertas.get_children():
            self._tree_abiertas.delete(row)
        lista = self._ctrl.listar_pqrs_abiertas()
        for data in lista:
            self._tree_abiertas.insert("", "end", values=(
                data["radicado"], data["tipo"],
                data.get("asunto", ""),
                f"P{data['prioridad']}", data["estado"], data["fecha"],
            ))

    def _marcar_gestion_sucia(self):
        """Marca que hay un comentario sin guardar."""
        self._gestion_sucia = True

    # ═══════════════════════════════════════════════════════════════════════
    # TOOLTIP
    # ═══════════════════════════════════════════════════════════════════════

    def _on_hist_mouse_motion(self, event):
        item = self._tree_hist.identify_row(event.y)
        col = self._tree_hist.identify_column(event.x)
        if item and col == "#5":  # columna comentario
            valores = self._tree_hist.item(item)["values"]
            if len(valores) >= 5 and valores[4]:
                self._mostrar_tooltip(event, str(valores[4]))
                return
        self._ocultar_tooltip()

    def _on_hist_mouse_leave(self, _=None):
        self._ocultar_tooltip()

    def _mostrar_tooltip(self, event, texto):
        self._ocultar_tooltip()
        x = event.x_root + 15
        y = event.y_root + 10
        self._tooltip_hist = tk.Toplevel(self._tree_hist)
        self._tooltip_hist.wm_overrideredirect(True)
        self._tooltip_hist.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self._tooltip_hist, text=texto, bg="#FFFFDD",
                       fg=C["text"], font=FONT_SMALL, wraplength=400,
                       padx=8, pady=4, relief="solid", borderwidth=1)
        lbl.pack()

    def _ocultar_tooltip(self):
        if self._tooltip_hist:
            self._tooltip_hist.destroy()
            self._tooltip_hist = None

    # ═══════════════════════════════════════════════════════════════════════
    # INICIAR
    # ═══════════════════════════════════════════════════════════════════════

    def iniciar(self):
        self._refrescar_bandeja_abiertas()
        self._root.mainloop()
