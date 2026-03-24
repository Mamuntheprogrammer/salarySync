import sys
import os
from cx_Freeze import setup, Executable

# ----------------------------
# Base Configuration (for GUI)
# ----------------------------
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# ----------------------------
# Prevent recursion issues
# ----------------------------
sys.setrecursionlimit(5000)

# ----------------------------
# Root-level source modules
# These MUST be explicitly packaged since they sit in the project
# root and won't be found automatically when frozen.
# ----------------------------
root_modules = [
    "config",
    "database",
    "models",
    "migrate",
]

# ----------------------------
# Include Files
# Static assets and sub-packages that need to be copied
# into the build directory. Tuple format: (source, destination)
# ----------------------------
include_files = [
    ("logo.ico", "logo.ico"),
    # NOTE: Do NOT include 'data/' here.
    # The app creates this folder fresh on first run via Config.ensure_directories().
    # Bundling 'data/' would ship the developer's own database and config.json
    # (which has setup_complete=True), causing the first-run wizard to be skipped
    # and a pre-populated database to be used by new installations.
    #
    # UI, Services and Utils sub-packages are Python packages —
    # cx_Freeze handles them automatically via 'packages' below.
    # But we include the raw .py files in case any dynamic import
    # or template loading references them by file path.
    ("ui/", "ui/"),
    ("services/", "services/"),
    ("utils/", "utils/"),
    # Root-level modules
    ("config.py", "config.py"),
    ("database.py", "database.py"),
    ("models.py", "models.py"),
    ("migrate.py", "migrate.py"),
    # Useful assets
    ("Import_Template.xlsx", "Import_Template.xlsx"),
]

# ----------------------------
# Build Options
# ----------------------------
build_exe_options = {
    "include_files": include_files,

    # Explicitly declare all top-level packages to ensure they
    # are fully bundled. cx_Freeze sometimes misses sub-modules
    # in complex packages like PyQt6, sqlalchemy, and face_recognition.
    "packages": [
        # Qt GUI
        "PyQt6",
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",

        # Database
        "sqlalchemy",
        "sqlalchemy.dialects",
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.orm",
        "sqlalchemy.pool",

        # Face recognition stack
        "face_recognition",
        "face_recognition_models",
        "dlib",

        # Computer vision & numerics
        "cv2",
        "numpy",

        # PDF generation
        "reportlab",
        "reportlab.platypus",
        "reportlab.lib",

        # Excel
        "openpyxl",
        "openpyxl.styles",
        "openpyxl.utils",

        # Security
        "bcrypt",

        # Charting
        "matplotlib",
        "matplotlib.backends.backend_qt5agg",

        # Standard library helpers that cx_Freeze can miss
        "sqlite3",
        "logging",
        "json",
        "email",
        "email.mime",
        "tempfile",
        "shutil",
        "pathlib",
        "warnings",
    ],

    # PyQt6 must NOT be zipped — it needs to load platform plugins
    # from the filesystem. Zipping it causes "platform plugin not found" errors.
    "zip_exclude_packages": [
        "PyQt6",
    ],

    # Modules that are safe to exclude to reduce build size.
    # NOTE: Do NOT exclude 'unittest' — bcrypt uses it internally.
    "excludes": [
        "tkinter",
        "distutils",
        "pydoc",
        "doctest",
    ],

    # Keep the build cleaner by not including test sub-packages
    "include_msvcr": True,  # Bundle the VC++ runtime DLLs (Windows)
}

# ----------------------------
# MSI Shortcut Configuration
# ----------------------------
shortcut_table = [
    (
        "DesktopShortcut",
        "DesktopFolder",
        "AttenSync HRMS",
        "TARGETDIR",
        "[TARGETDIR]AttenSync.exe",
        None,
        "Employee Attendance & Payroll Management System",
        None,
        None,
        None,
        None,
        "TARGETDIR",
    )
]

msi_data = {"Shortcut": shortcut_table}
bdist_msi_options = {
    "data": msi_data,
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\AttenSync",
}

# ----------------------------
# Executable Target Definition
# ----------------------------
executables = [
    Executable(
        "main.py",
        target_name="AttenSync",
        icon="logo.ico",
        base=base,
        # Embed the version info into the .exe on Windows
        copyright="2024 Md Abdullah Al Mamun",
    )
]

# ----------------------------
# Setup Definition
# ----------------------------
setup(
    name="AttenSync",
    version="1.0.0",
    description="Employee Attendance and Payroll Management System",
    author="Md Abdullah Al Mamun",
    author_email="pygemsbd@gmail.com",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
