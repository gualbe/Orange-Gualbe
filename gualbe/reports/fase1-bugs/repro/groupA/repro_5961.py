from unittest.mock import patch
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owsql import OWSql
from Orange.widgets.utils import owbasesql

class FakeCM:
    store = {}
    def __init__(self, key): self.key = key
    def __getattr__(self, n):
        if n in ("username", "password"): return FakeCM.store.get((self.key, n))
        raise AttributeError(n)
    def __setattr__(self, n, v):
        if n in ("username", "password"): FakeCM.store[(self.key, n)] = v
        else: object.__setattr__(self, n, v)

class T(WidgetTest):
    def test_slash(self):
        with patch.object(owbasesql, "CredentialManager", FakeCM):
            w = self.create_widget(OWSql)
            w.servertext.setText("localhost:5432")
            w.databasetext.setText("some/name")
            w._check_db_settings()
            print(f"\n#5961 databasetext='some/name' -> database={w.database!r}, schema={w.schema!r}")
            # what would be passed to the backend
            captured = {}
            class B:
                def __init__(self, params): captured.update(params); raise owbasesql.BackendError("x")
            w.get_backend = lambda: B
            w.connect()
            print("#5961 params passed to backend:", captured)

    def test_shared_credentials(self):
        # #6431: two widgets, same server text, different DBMS/db/user -> keychain key is host:port only
        with patch.object(owbasesql, "CredentialManager", FakeCM):
            ok = lambda self_: None
            w1 = self.create_widget(OWSql); w2 = self.create_widget(OWSql)
            for w, user, pwd, db in ((w1, "pg_user", "pg_pwd", "pgdb"), (w2, "ms_user", "ms_pwd", "msdb")):
                w.servertext.setText("dbserver"); w.databasetext.setText(db)
                w.usernametext.setText(user); w.passwordtext.setText(pwd)
                w._check_db_settings(); w._save_credentials()
            print("\n#6431 keychain keys:", sorted({k for k, _ in FakeCM.store}))
            # simulate reopening workflow: new widgets restored from settings
            s1 = self.widget_settings = w1.settingsHandler.pack_data(w1)
            s2 = w2.settingsHandler.pack_data(w2)
            r1 = self.create_widget(OWSql, stored_settings=s1); r2 = self.create_widget(OWSql, stored_settings=s2)
            print("#6431 after reload: w1 user/pwd =", r1.usernametext.text(), r1.passwordtext.text(),
                  "| w2 user/pwd =", r2.usernametext.text(), r2.passwordtext.text())

if __name__ == "__main__":
    import unittest; unittest.main()
