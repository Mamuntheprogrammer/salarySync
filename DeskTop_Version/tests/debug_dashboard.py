import sys
import os
sys.path.append(os.getcwd())

from PyQt6.QtWidgets import QApplication
from ui.admin.dashboard import AdminDashboard

class MockUser:
    username = "admin"
    role = "admin"

class MockMainWindow:
    def switch_to_dashboard(self, w):
        pass

def test():
    app = QApplication(sys.argv)
    try:
        user = MockUser()
        mw = MockMainWindow()
        print("Instantiating Dashboard...")
        dash = AdminDashboard(mw, user)
        print("Dashboard Instantiated Successfully")
        print("Modules initialized:")
        for k in dash.pages:
            print(f"- {k}")
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
