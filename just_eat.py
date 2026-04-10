import asyncio
import traceback
import uuid
import nodriver as uc

from PySide6.QtWidgets import (
    QWizardPage,
    QLabel,
    QVBoxLayout,
    QWizard,
    QComboBox,
    QMessageBox,
)
from PySide6.QtCore import QTimer, QObject, Signal, QThread
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
    login_complete = False

    # noinspection PyPackageRequirements
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Just Eat Login"))
        self.setSubTitle(self.tr("Enter your credentials for your Just Eat Account."))

        instructions = QLabel(
            self.tr(
                """In the browser that opens, login to your Just Eat account.

It will automatically close once login is completed.

IMPORTANT - DO NOT RESIZE THE BROWSER WINDOW. DOING SO CAN CAUSE THE PROCESS TO FAIL."""
            )
        )
        instructions.setWordWrap(True)

        self.layout = QVBoxLayout()
        self.layout.addWidget(instructions)
        self.setLayout(self.layout)

        self.browser_thread = QThread()
        self.browser_worker = BrowserWorker()

    def initializePage(self):
        QTimer.singleShot(0, self.disable_next_button)

        try:
            resp = requests.get(
                f"https://just-eat.wiilink.ca/loginurls.json?country={country}"
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

        self.browser_worker.browser_path = self.wizard().property("browser")
        self.browser_worker.eater_url = resp.json()["eater_url"]
        self.browser_worker.token_url = resp.json()["token_url"]

        self.browser_worker.moveToThread(self.browser_thread)
        self.browser_thread.started.connect(self.browser_worker.begin_browser)
        self.browser_worker.token_signal.connect(self.browser_done)
        self.browser_worker.token_signal.connect(self.browser_thread.quit)
        self.browser_worker.token_signal.connect(self.browser_worker.deleteLater)
        self.browser_worker.token_signal.connect(self.browser_thread.deleteLater)

        self.browser_thread.start()

    def browser_done(self, token: dict):
        global country

        device_id = random.choice(devices)
        acr_device = {
            "DeviceType": "Android",
            "DeviceName": device_id,
            "DeviceId": str(uuid.uuid4()),
        }
        acr = f"tenant:{country} device:{base64.b64encode(json.dumps(acr_device).encode()).decode()} deviceId:{device_id}"

        try:
            resp = link_to_server(
                token,
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

        self.login_complete = True
        self.completeChanged.emit()
        QTimer.singleShot(0, self.wizard().next)

    def disable_next_button(self):
        self.wizard().button(QWizard.WizardButton.NextButton).setEnabled(False)

    def isComplete(self):
        return self.login_complete

    def nextId(self):
        return 5


class BrowserWorker(QObject):
    page: uc.Tab
    browser: uc.Browser
    token_json: dict
    eater_url: str
    token_url: str
    browser_path: str = None
    token_got = asyncio.Event()

    token_signal = Signal(dict)

    def begin_browser(self):
        uc.loop().run_until_complete(self.run_browser())

    async def run_browser(self):
        self.browser = await uc.start(
            browser_executable_path=self.browser_path,
            # size to match phone screen, window position to put it always in the top left corner
            browser_args=["--window-size=412,915", "--window-position=0,0"],
        )
        self.page = await self.browser.get("about:blank")
        self.page.add_handler(uc.cdp.network.ResponseReceived, self.handler)

        # domain from api "checkoutUrl"
        self.page = await self.browser.get(self.eater_url)

        await self.token_got.wait()
        self.browser.stop()
        self.token_signal.emit(self.token_json)

    async def handler(self, evt: uc.cdp.network.ResponseReceived):
        if evt.response.encoded_data_length > 0:
            # domain from api "authenticationApiUrl"
            if evt.response.url == self.token_url:
                body, is_base64 = await self.page.send(
                    uc.cdp.network.get_response_body(evt.request_id)
                )
                self.token_json = json.loads(body)
                self.token_got.set()
