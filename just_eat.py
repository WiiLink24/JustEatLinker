import traceback
import uuid

from PySide6.QtWidgets import (
    QWizardPage,
    QLabel,
    QVBoxLayout,
    QWizard,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from curl_cffi import requests
from curl_cffi.requests.exceptions import HTTPError
from constants import devices, linker_version

import random
import base64
import json
import time

country = ""


class CountrySelect(QWizardPage):
    countries = {
        "United Kingdom": "UK",
        "Italy": "IT",
        "Austria": "AT",
        "Germany": "DE",
        "Ireland": "IE",
        "Spain": "ES",
    }

    def __init__(self, parent=None):
        global country
        super().__init__(parent)
        self.setTitle(self.tr("Select your country"))
        self.setSubTitle(
            self.tr("Select the country associated with your Just Eat Account.")
        )

        box = QComboBox()
        box.addItems(list(self.countries.keys()))
        box.currentTextChanged.connect(self.text_changed)
        country = self.countries[box.currentText()]

        self.layout = QVBoxLayout()
        self.layout.addWidget(box)
        self.setLayout(self.layout)

    def text_changed(self, text):
        global country
        country = self.countries[text]


def link_to_server(data, wii_number, auth, device_id, acr):
    header = {
        "Authorization": auth,
        "User-Agent": f"WiiLink Just Eat Linker {linker_version}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    payload = {
        "wii_number": wii_number,
        "eat_auth": "Bearer " + data["access_token"],
        "refresh_token": data["refresh_token"],
        "expire_time": int(time.time()) + int(data["expires_in"]),
        "device_model": device_id,
        "acr": acr,
    }

    return requests.post(
        "https://just-eat.wiilink.ca/link", headers=header, data=payload
    )


class JustEatCredentialsPage(QWizardPage):
    has_2fa = False

    # noinspection PyPackageRequirements
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Just Eat Login"))
        self.setSubTitle(self.tr("Enter your credentials for your Just Eat Account."))

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.reset_password_button = QLabel(self.tr("Reset Password..."))
        font = QFont()
        font.setUnderline(True)
        self.reset_password_button.setFont(font)
        self.reset_password_button.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.reset_password_button.setStyleSheet("color: #606060;")
        self.reset_password_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_password_button.mousePressEvent = self.reset_password

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.reset_password_button)
        self.layout.addWidget(self.login_button)
        self.setLayout(self.layout)

    def initializePage(self):
        QTimer.singleShot(0, self.disable_next_button)

    def disable_next_button(self):
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)

    def nextId(self):
        if self.has_2fa:
            return 5

        return 6

    def reset_password(self, event=None):
        global country
        device_id = random.choice(devices)

        try:
            resp = requests.get(
                f"https://just-eat.wiilink.ca/resetdata.json?device_id={device_id}&country={country}"
            )
            resp.raise_for_status()
        except HTTPError:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to get password reset information from WiiLink servers.

Received status code {resp.status_code}.
Response: {resp.text}""",
            )
            return
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to get password reset information from WiiLink servers.

{exception_traceback}""",
            )
            return

        data = resp.json()
        payload = {
            "EmailAddress": self.username_input.text(),
        }

        try:
            resp = requests.post(
                data["url"],
                headers=data["header"],
                data=json.dumps(payload),
                impersonate="safari17_0",
            )
            resp.raise_for_status()
        except HTTPError:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to request the password reset.

Received status code {resp.status_code}.
Response: {resp.text}""",
            )
            return
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to request the password reset.

{exception_traceback}""",
            )
            return

        QMessageBox.information(
            self,
            "Successfully reset password",
            f"If there is a Just Eat account associated with <b>{self.username_input.text()}</b>, you will receive an email from Just Eat to reset your password.",
        )

    def handle_login(self):
        global country
        device_id = random.choice(devices)

        try:
            resp = requests.get(
                f"https://just-eat.wiilink.ca/userdatalogin.json?device_id={device_id}&country={country}"
            )
            resp.raise_for_status()
        except HTTPError:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to get login information from WiiLink servers.

Received status code {resp.status_code}.
Response: {resp.text}""",
            )
            return
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to get login information from WiiLink servers.

{exception_traceback}""",
            )
            return

        # Complete the body based on the user's inputs.
        data = resp.json()
        payload = data["payload"]

        acr_device = {
            "DeviceType": "Android",
            "DeviceName": device_id,
            "DeviceId": str(uuid.uuid4()),
        }
        acr = f"tenant:{country} device:{base64.b64encode(json.dumps(acr_device).encode()).decode()} deviceId:{device_id}"
        payload["acr"] = acr
        payload["username"] = self.username_input.text()
        payload["password"] = self.password_input.text()

        try:
            resp = requests.post(
                data["url"],
                headers=data["header"],
                data=payload,
                impersonate="safari17_0",
            )
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to login to your account.

{exception_traceback}""",
            )
            return

        if resp.status_code == 400 and resp.json()["error"] == "invalid_grant":
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Warning",
                "Please enter the correct credentials for your Just Eat account.",
            )
            return
        elif resp.status_code == 200:
            try:
                resp = link_to_server(
                    resp.json(),
                    self.wizard().property("wii_no"),
                    self.wizard().property("access_token"),
                    device_id,
                    acr,
                )
                resp.raise_for_status()
            except HTTPError:
                exception_traceback = traceback.format_exc()
                print(exception_traceback)
                QMessageBox.critical(
                    self,
                    "WiiLink Just Eat Linker - Error",
                    f"""The linker was unable to link your Just Eat account to your WiiLink account.

Received status code {resp.status_code}.
Response: {resp.text}""",
                )
                return
            except:
                exception_traceback = traceback.format_exc()
                print(exception_traceback)
                QMessageBox.critical(
                    self,
                    "WiiLink Just Eat Linker - Error",
                    f"""The linker was unable to link your Just Eat account to your WiiLink account.

{exception_traceback}""",
                )
                return

            self.wizard().next()
            return
        elif resp.status_code == 403 and resp.json()["error"] == "mfa_required":
            data = resp.json()
            self.has_2fa = True
            self.wizard().setProperty("mfa_token", data["mfa_token"])
            self.wizard().setProperty("device_id", device_id)
            self.wizard().setProperty("payload", payload)
            self.wizard().setProperty("acr", acr)
            self.wizard().next()
        else:
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to login to your account.

Received status code {resp.status_code}.
Response: {resp.text}""",
            )


class JustEat2FAPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Just Eat Login"))
        self.setSubTitle(self.tr("Enter the 2FA code sent to your Just Eat email"))

        self.code_label = QLabel("Code:")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter your code")

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.code_label)
        self.layout.addWidget(self.code_input)
        self.layout.addWidget(self.login_button)
        self.setLayout(self.layout)

    def initializePage(self):
        QTimer.singleShot(0, self.disable_buttons)

    def disable_buttons(self):
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)

    def handle_login(self):
        global country
        mfa_token = self.wizard().property("mfa_token")
        device_id = self.wizard().property("device_id")
        other_payload = self.wizard().property("payload")

        try:
            resp = requests.get(
                f"https://just-eat.wiilink.ca/2fadata.json?device_id={device_id}&country={country}"
            )
            resp.raise_for_status()
        except HTTPError:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to connect to WiiLink servers.

Received status code {resp.status_code}.
Message: {resp.text}""",
            )
            return
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to connect to WiiLink servers.

{exception_traceback}""",
            )
            return

        # Complete the body based on the user's inputs.
        data = resp.json()
        payload = data["payload"]
        other_payload.update(payload)
        other_payload["mfa_token"] = mfa_token
        other_payload["otp"] = self.code_input.text()

        # Post to the 2FA endpoint.
        try:
            resp = requests.post(
                data["url"],
                headers=data["header"],
                data=other_payload,
                impersonate="safari17_0",
            )
            resp.raise_for_status()
        except HTTPError:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to authenticate with your provided 2FA code.

Received status code {resp.status_code}.
Message: {resp.text}""",
            )
            return
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to authenticate with your provided 2FA code.

{exception_traceback}""",
            )
            return

        # We now need to send the auth data to the Demae Just Eat server.
        data = resp.json()
        try:
            resp = link_to_server(
                data,
                self.wizard().property("wii_no"),
                self.wizard().property("access_token"),
                self.wizard().property("device_id"),
                self.wizard().property("acr"),
            )
            resp.raise_for_status()
        except HTTPError:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to link your Just Eat account to your WiiLink account.

Received status code {resp.status_code}.
Message: {resp.text}""",
            )
            return
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.critical(
                self,
                "WiiLink Just Eat Linker - Error",
                f"""The linker was unable to link your Just Eat account to your WiiLink account.

{exception_traceback}""",
            )
            return

        self.wizard().next()
