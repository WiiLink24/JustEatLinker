import time
import sys
from curl_cffi import requests
from errors import VerificationURLError, TokenHTTPError, AttributeRetrievalError
from PySide6.QtWidgets import (
    QWizardPage,
    QLabel,
    QVBoxLayout,
    QWizard,
    QComboBox,
    QMessageBox,
)
from PySide6.QtCore import QThread, QObject, Signal, QTimer, Qt

access_token = ""


def get_verification_url():
    data = {
        "client_id": "ChGKaNcTcArxLCWSxAbvXXtbWKsM1xcy6x7k8ssn",
        "scope": "openid email profile goauthentik.io/api",
    }

    headers = {
        "User-Agent": "WiiLink Just Eat Linker v0.1",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    resp = requests.post(
        "https://sso.riiconnect24.net/application/o/device/", headers=headers, data=data
    )
    if resp.status_code != 200:
        raise VerificationURLError(resp.status_code)

    return resp.json()


def get_token(device_code: str):
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": "ChGKaNcTcArxLCWSxAbvXXtbWKsM1xcy6x7k8ssn",
        "device_code": device_code,
    }

    headers = {
        "User-Agent": "WiiLink Just Eat Linker v0.1",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    resp = requests.post(
        "https://sso.riiconnect24.net/application/o/token/", headers=headers, data=data
    )
    if resp.status_code != 200 and resp.status_code != 400:
        raise TokenHTTPError(resp.status_code)

    return resp.json()


class WiiLinkAccountPage(QWizardPage):
    interval: int
    device_code: str
    finished = False

    def __init__(self, parent=None):
        super().__init__(parent)

        # Get the device code
        try:
            data = get_verification_url()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Failed to connect to WiiLink",
                f"""The linker was unable to connect to WiiLink servers.

Exception: {e}""",
            )
            sys.exit(1)
        self.interval = data["interval"]
        self.device_code = data["device_code"]

        self.setTitle(self.tr("Login to your WiiLink Account"))
        self.setSubTitle(self.tr("Login with your browser"))

        self.label = QLabel(
            self.tr(
                f"""Visit <a href="{data['verification_uri']}">{data['verification_uri']}</a> and enter the code below:</br></br>

<h1 style='text-align: center;'>{data["user_code"]}</h1></br></br>

Upon success you will be redirected to the next page."""
            )
        )
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.logic_thread = QThread()
        self.logic_worker = AccountConnector()

    def initializePage(self):
        QTimer.singleShot(0, self.disable_back_button)
        QTimer.singleShot(0, self.disable_next_button)

        self.logic_worker.interval = self.interval
        self.logic_worker.device_code = self.device_code

        self.logic_worker.moveToThread(self.logic_thread)
        self.logic_thread.started.connect(self.logic_worker.poll_device_page)

        self.logic_worker.finished.connect(self.logic_finished)
        self.logic_worker.finished.connect(self.logic_thread.quit)
        self.logic_thread.finished.connect(self.logic_worker.deleteLater)
        self.logic_thread.finished.connect(self.logic_thread.deleteLater)

        self.logic_thread.start()

    def isComplete(self):
        return self.finished

    def logic_finished(self):
        self.finished = True
        self.completeChanged.emit()
        self.wizard().setProperty("access_token", access_token)
        QTimer.singleShot(0, self.wizard().next)

    def disable_back_button(self):
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)

    def disable_next_button(self):
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)


class AccountConnector(QObject):
    finished = Signal(bool)
    error = Signal(str)
    device_code: str
    interval: int

    def poll_device_page(self):
        while True:
            data = get_token(self.device_code)
            try:
                if data["error"] == "authorization_pending":
                    time.sleep(self.interval)
            except KeyError:
                # If this happens we are logged in.
                global access_token
                access_token = data["access_token"]
                break

        self.finished.emit(True)


class WiiNumberSelector(QWizardPage):
    wii_nos: list[str] = []
    linked: bool = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Select your Wii Number"))
        self.setSubTitle(
            self.tr("Select the Wii number you want to link with Just Eat.")
        )

        self.layout = QVBoxLayout()

    def initializePage(self):
        QTimer.singleShot(0, self.disable_back_button)

        global access_token

        this_headers = {
            "Authorization": access_token,
        }

        try:
            resp = requests.get(
                "https://accounts.wiilink.ca/link/user", headers=this_headers
            )
            if resp.status_code != 200:
                raise AttributeRetrievalError(resp.status_code)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Failed to connect to WiiLink",
                f"""The linker was unable to connect to WiiLink servers.

Exception: {e}""",
            )
            return

        resp = resp.json()

        if resp["attributes"] == {}:
            self.linked = False
            label = QLabel(
                self.tr(
                    """Currently, you have no Wiis linked to your account.<br><br>

Follow the guide at <a href='https://wiilink.ca/guide/accounts'>https://wiilink.ca/guide/accounts</a> to link your console.<br><br>

Then, run this app again."""
                )
            )
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setWordWrap(True)
            label.setOpenExternalLinks(True)
            self.layout.addWidget(label)
            self.setLayout(self.layout)
            return

        print(resp["attributes"])

        self.wii_nos = resp["attributes"]["wiis"]
        box = QComboBox()
        box.addItems(self.wii_nos)
        box.currentTextChanged.connect(self.number_changed)
        self.wizard().setProperty("wii_no", self.wii_nos[0])

        self.layout.addWidget(box)
        self.setLayout(self.layout)

    def isComplete(self):
        # Needed to keep back button disabled when navigating back to page
        # Thank you Qt, this is very logical
        QTimer.singleShot(0, self.disable_back_button)
        if self.wii_nos and self.linked:
            return True

        if not self.linked:
            return False

        # If the wii_nos list is empty, we were unable to retrieve
        # Wii numbers, and thus the app cannot continue
        sys.exit(1)

    def number_changed(self, number):
        self.wizard().setProperty("wii_no", number)

    def disable_back_button(self):
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)
