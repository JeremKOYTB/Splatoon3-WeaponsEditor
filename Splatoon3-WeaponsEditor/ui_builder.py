from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QPushButton, QComboBox, QCheckBox, QLabel, 
    QProgressBar, QTableWidget, QHeaderView, 
    QTreeWidget, QSizePolicy, QFrame, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from translations import t
from components import (
    TypeEnforcedDelegate, AnimatedWeaponImage, AnimatedTitleLabel, WeaponTableDelegate
)

def setup_ui(win):
    cw = QWidget()
    win.setCentralWidget(cw)
    layout = QHBoxLayout(cw)
    layout.setContentsMargins(15, 12, 15, 12) 
    layout.setSpacing(14)
    
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(8)
    layout.addWidget(splitter)

    lp = QFrame()
    lp.setObjectName("Card")
    lp.setMinimumWidth(260) 
    ll = QVBoxLayout(lp)
    ll.setContentsMargins(12, 12, 12, 12)
    ll.setSpacing(10)
    
    win.btn_open = QPushButton("")
    win.btn_open.clicked.connect(win.load_pack)
    win.btn_open.setFixedHeight(38)
    win.btn_open.setStyleSheet("font-weight: bold;")
    ll.addWidget(win.btn_open)

    win.btn_import_romfs = QPushButton("")
    win.btn_import_romfs.clicked.connect(win.import_local_romfs)
    win.btn_import_romfs.setFixedHeight(38)
    win.btn_import_romfs.setStyleSheet("""
        QPushButton { background-color: #8e44ad; color: white; font-weight: bold; border-radius: 6px; border: none; }
        QPushButton:hover { background-color: #7d3c98; }
    """)
    ll.addWidget(win.btn_import_romfs)

    win.btn_compare = QPushButton("")
    win.btn_compare.clicked.connect(win.perform_comparison)
    win.btn_compare.setFixedHeight(38)
    win.btn_compare.setStyleSheet("""
        QPushButton { background-color: #34495e; color: white; font-weight: bold; border-radius: 6px; border: none; }
        QPushButton:hover { background-color: #2c3e50; }
    """)
    ll.addWidget(win.btn_compare)

    filter_layout = QVBoxLayout()
    filter_layout.setSpacing(8)
    
    win.search_bar = QLineEdit()
    win.search_bar.setFixedHeight(32)
    win.search_bar.textChanged.connect(win.on_search_changed)
    filter_layout.addWidget(win.search_bar)
    
    form_layout = QFormLayout()
    form_layout.setSpacing(8)
    
    win.lbl_filter = QLabel("")
    win.combo_filter = QComboBox()
    win.combo_filter.setFixedHeight(32)
    win.combo_filter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    win.combo_filter.addItem("", "all")
    win.combo_filter.addItem("Weapon", "Weapon")
    win.combo_filter.addItem("Bullet", "Bullet")
    win.combo_filter.addItem("", "WeaponSp")
    win.combo_filter.addItem("", "Coop")
    win.combo_filter.addItem("", "Hero")
    
    win.combo_filter.currentIndexChanged.connect(win.on_filter_changed)
    form_layout.addRow(win.lbl_filter, win.combo_filter)
    filter_layout.addLayout(form_layout)
    
    chks_layout = QHBoxLayout()
    chks_layout.setSpacing(10)
    
    def add_wrapped_chk(attr_name, callback):
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        
        chk = QCheckBox()
        chk.stateChanged.connect(callback)
        
        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def toggle_chk(event, c=chk):
            c.toggle()
        lbl.mousePressEvent = toggle_chk

        chk.setStyleSheet("""
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)

        l.addWidget(chk, 0, Qt.AlignmentFlag.AlignVCenter)
        l.addWidget(lbl, 1, Qt.AlignmentFlag.AlignVCenter)
        
        setattr(win, attr_name, chk)
        setattr(win, f"{attr_name}_lbl", lbl)
        setattr(win, f"{attr_name}_container", container)
        chks_layout.addWidget(container, 1)

    add_wrapped_chk("chk_hide_filenames", win.on_hide_filenames_toggled)
    add_wrapped_chk("chk_hide_dummy", win.on_hide_dummy_toggled)
    add_wrapped_chk("chk_auto_expand", win.on_auto_expand_toggled)
    
    win.chk_hide_dummy_container.setVisible(True)
    
    filter_layout.addLayout(chks_layout)
    ll.addLayout(filter_layout)

    win.prog_container = QWidget()
    prog_layout = QVBoxLayout(win.prog_container)
    prog_layout.setContentsMargins(0, 0, 0, 0)
    
    win.progress_lbl = QLabel("")
    win.progress_lbl.setObjectName("ProgressLabel")
    
    win.progress_bar = QProgressBar()
    win.progress_bar.setFixedHeight(10)
    win.progress_bar.setTextVisible(False)
    
    prog_layout.addWidget(win.progress_lbl)
    prog_layout.addWidget(win.progress_bar)
    win.prog_container.setVisible(False)
    ll.addWidget(win.prog_container)

    win.count_lbl = QLabel("")
    win.count_lbl.setObjectName("CountLabel")
    win.count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ll.addWidget(win.count_lbl)

    win.table_w = QTableWidget(0, 2)
    win.table_w.viewport().setStyleSheet("background-color: transparent;") 
    win.table_w.horizontalHeader().setVisible(False)
    win.table_w.verticalHeader().setVisible(False)
    win.table_w.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    win.table_w.setColumnWidth(0, 28)
    win.table_w.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    win.table_w.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    win.table_w.setShowGrid(False)
    win.table_w.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    win.table_w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    win.table_w.customContextMenuRequested.connect(win.on_table_context_menu)
    win.table_w.setMinimumWidth(180) 
    win.table_w.verticalHeader().setDefaultSectionSize(36)
    win.table_w.currentItemChanged.connect(win.on_table_current_changed)
    win.table_w.cellClicked.connect(win.on_cell_clicked)
    
    win.weapon_delegate = WeaponTableDelegate(win.table_w)
    win.table_w.setItemDelegate(win.weapon_delegate)
    
    ll.addWidget(win.table_w, 1)
    
    win.btn_update = QPushButton(f"Splatoon 3 Weapons Editor (v{win.APP_VERSION})")
    win.btn_update.setFixedHeight(34)
    win.btn_update.clicked.connect(win.launch_updater)
    ll.addWidget(win.btn_update)
    
    splitter.addWidget(lp)

    rp = QFrame()
    rp.setObjectName("Card")
    rp.setMinimumWidth(320) 
    rl = QVBoxLayout(rp)
    rl.setContentsMargins(14, 14, 14, 14)
    rl.setSpacing(12)
    
    win.weapon_card = QFrame()
    win.weapon_card.setObjectName("weapon_card")
    win.weapon_card.setStyleSheet("""
        #weapon_card {
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 8px;
        }
    """)
    card_l = QHBoxLayout(win.weapon_card)
    card_l.setContentsMargins(14, 10, 14, 10)
    card_l.setSpacing(16)
    card_l.setAlignment(Qt.AlignmentFlag.AlignVCenter)
    
    win.img_lbl = AnimatedWeaponImage()
    win.img_lbl.setFixedSize(110, 110)
    win.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    win.img_lbl.setStyleSheet("""
        background-color: rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
    """)
    card_l.addWidget(win.img_lbl)
    
    info_vbox = QVBoxLayout()
    info_vbox.setContentsMargins(0, 0, 0, 0)
    info_vbox.setSpacing(4)
    info_vbox.setAlignment(Qt.AlignmentFlag.AlignVCenter)
    
    win.name_lbl = AnimatedTitleLabel("")
    win.name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    win.name_lbl.setFont(QFont("Segoe UI Variable", 12, QFont.Weight.Bold))
    win.name_lbl.setTextFormat(Qt.TextFormat.RichText)
    win.name_lbl.setWordWrap(True)
    info_vbox.addWidget(win.name_lbl)
    
    info_vbox.addSpacing(8)

    lang_row = QHBoxLayout()
    lang_row.setContentsMargins(0, 2, 0, 0)
    lang_row.setSpacing(8)
    win.lbl_lang = QLabel("")
    win.lbl_lang.setStyleSheet("color: #b0b0b8; font-size: 11px;")
    lang_row.addWidget(win.lbl_lang)
    
    win.lang_combo = QComboBox()
    win.lang_combo.setFixedHeight(28)
    win.lang_combo.addItems(list(win.languages.keys()))
    win.lang_combo.currentTextChanged.connect(win.on_language_changed)
    lang_row.addWidget(win.lang_combo)
    lang_row.addStretch()
    
    info_vbox.addLayout(lang_row)
    card_l.addLayout(info_vbox, 1)
    
    rl.addWidget(win.weapon_card)

    win.tree_w = QTreeWidget()
    win.tree_w.setColumnWidth(0, 360)
    win.tree_w.setAlternatingRowColors(True)
    win.tree_w.header().setStretchLastSection(True)
    win.delegate = TypeEnforcedDelegate(win.tree_w)
    win.tree_w.setItemDelegateForColumn(1, win.delegate)
    win.tree_w.setEditTriggers(QTreeWidget.EditTrigger.DoubleClicked | QTreeWidget.EditTrigger.EditKeyPressed)
    win.tree_w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    win.tree_w.customContextMenuRequested.connect(win.on_tree_context_menu)
    
    rl.addWidget(win.tree_w, 1)

    win.btn_save = QPushButton("")
    win.btn_save.clicked.connect(win.save_pack)
    win.btn_save.setFixedHeight(40)
    win.btn_save.setStyleSheet("""
        QPushButton { background-color: #27ae60; color: white; font-size: 11pt; font-weight: bold; border-radius: 6px; border: none; }
        QPushButton:hover { background-color: #2ecc71; }
    """)
    rl.addWidget(win.btn_save)

    splitter.addWidget(rp)
    splitter.setSizes([450, 850])

def update_ui_texts(win):
    win.setWindowTitle(t("window_title"))
    win.search_bar.setPlaceholderText(t("search_placeholder"))
    win.btn_open.setText(t("btn_open"))
    win.btn_import_romfs.setText(t("btn_import_romfs"))
    win.btn_compare.setText(t("btn_compare"))
    win.btn_save.setText(t("btn_save"))
    
    win.lbl_filter.setText(t("lbl_filter"))
    win.lbl_lang.setText(t("lbl_lang"))
    
    win.chk_hide_dummy_lbl.setText(t("chk_hide_dummy"))
    win.chk_hide_filenames_lbl.setText(t("chk_hide_filenames"))
    win.chk_auto_expand_lbl.setText(t("chk_auto_expand"))
    
    if hasattr(win, 'btn_rsdb'):
        win.btn_rsdb.setText(t("btn_rsdb"))
    
    win.tree_w.setHeaderLabels([t("tree_prop"), t("tree_val")])

    win.combo_filter.blockSignals(True)
    for i in range(win.combo_filter.count()):
        data = win.combo_filter.itemData(i)
        if data == "all": 
            win.combo_filter.setItemText(i, t("filter_all"))
        elif data == "dummy": 
            win.combo_filter.setItemText(i, t("filter_dummy"))
        elif data == "Coop": 
            win.combo_filter.setItemText(i, t("filter_coop"))
        elif data == "Hero": 
            win.combo_filter.setItemText(i, t("filter_hero"))
        elif data == "WeaponSp":
            sp_text = win.data_manager._find_json_value("SpecialAttack", t("filter_special"))
            if sp_text:
                sp_text = sp_text[0].upper() + sp_text[1:]
            else:
                sp_text = t("filter_special")
            win.combo_filter.setItemText(i, f"{sp_text} (WeaponSp)")
            
    win.combo_filter.blockSignals(False)

    if not win.pack_manager.sarc:
        win.name_lbl.setText(t("lbl_wait_archive"), animate=False)
        win.count_lbl.setText(t("count_info", 0, 0, 0, 0))
    else:
        win.refresh_file_list()
        if win.current_byml_name:
            win.refresh_weapon_ui(win.current_byml_name)
        else:
            win.name_lbl.setText(t("lbl_archive_loaded"), animate=False)