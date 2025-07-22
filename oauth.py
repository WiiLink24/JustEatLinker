import time
from wsgiref import headers

import requests
from errors import VerificationURLError, TokenHTTPError
from PySide6.QtWidgets import QWizardPage, QLabel, QVBoxLayout, QWizard, QWidget, QComboBox, QMessageBox
from PySide6.QtCore import QThread, QObject, Signal, QTimer


access_token = ""


def get_verification_url():
    data = {
        "client_id": "ChGKaNcTcArxLCWSxAbvXXtbWKsM1xcy6x7k8ssn",
        "scope": "openid email profile goauthentik.io/api"
    }

    headers = {
        "User-Agent": "WiiLink Just Eat Linker v0.1",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    resp = requests.post("https://sso.riiconnect24.net/application/o/device/", headers=headers, data=data)
    if resp.status_code != 200:
        raise VerificationURLError(resp.status_code)

    return resp.json()


def get_token(device_code: str):
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": "ChGKaNcTcArxLCWSxAbvXXtbWKsM1xcy6x7k8ssn",
        "device_code": device_code
    }

    headers = {
        "User-Agent": "WiiLink Just Eat Linker v0.1",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    resp = requests.post("https://sso.riiconnect24.net/application/o/token/", headers=headers, data=data)
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
        data = get_verification_url()
        self.interval = data["interval"]
        self.device_code = data["device_code"]

        self.setTitle(self.tr("Login to your WiiLink Account"))
        self.setSubTitle(
            self.tr(
                "Login with your browser"
            )
        )

        self.label = QLabel(
            self.tr(
                f"""Visit {data['verification_uri']} and enter the code below:

               {data["user_code"]}

Upon success you will be redirected to the next page.
                """
            )
        )
        self.label.setWordWrap(True)
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Select your Wii Number"))
        self.setSubTitle(self.tr("Select the Wii number you want to link with Just Eat."))

        self.layout = QVBoxLayout()

    def initializePage(self):
        global access_token

        this_headers = {
            "Authorization": access_token,
        }

        resp = requests.get("https://accounts.wiilink.ca/link/user", headers=this_headers)
        if resp.status_code != 200:
            QMessageBox.critical(self, "Failed to connect to WiiLink Accounts", "Please check your connection.")
            return

        resp = resp.json()
        wii_nos: list[str] = resp["attributes"]["wiis"]

        box = QComboBox()
        box.addItems(wii_nos)
        box.currentTextChanged.connect(self.number_changed)
        self.wizard().setProperty("wii_no", wii_nos[0])

        self.layout.addWidget(box)
        self.setLayout(self.layout)

    def number_changed(self, number):
        self.wizard().setProperty("wii_no", number)
