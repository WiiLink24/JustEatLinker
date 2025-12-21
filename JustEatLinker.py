# Nuitka options. These determine compilation settings based on the current OS.
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --standalone
#    nuitka-project: --macos-create-app-bundle
#    nuitka-project: --macos-app-icon={MAIN_DIRECTORY}/assets/logo.webp
# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --windows-icon-from-ico={MAIN_DIRECTORY}/assets/logo.webp
#    nuitka-project: --windows-console-mode=disable
# nuitka-project-if: {OS} in ("Linux", "FreeBSD", "OpenBSD"):
#    nuitka-project: --onefile
# These are standard options that are needed on all platforms.
# nuitka-project: --plugin-enable=pyside6
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/assets=assets
# nuitka-project: --include-data-file={MAIN_DIRECTORY}/style.qss=style.qss

import sys
import datetime
import random
import traceback
import webbrowser
import json

from curl_cffi import requests
from constants import file_path, linker_version
from oauth import WiiLinkAccountPage, WiiNumberSelector
from just_eat import JustEatCredentialsPage, CountrySelect, JustEat2FAPage
from PySide6.QtCore import Qt, QTimer, QLocale
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QApplication,
    QLabel,
    QVBoxLayout,
    QMessageBox,
)


def get_latest_version() -> str:
    """Gets the tag of the latest stable release from the GitHub API

    Returns:
        The latest tag from the GitHub API"""
    api_url = "https://api.github.com/repos/WiiLink24/JustEatLinker/releases/latest"

    api_response_raw = requests.get(api_url)
    api_response_raw.raise_for_status()

    api_response = json.loads(api_response_raw)

    latest_version = api_response["tag_name"].replace("v", "")

    return latest_version


class IntroPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Welcome to the WiiLink Just Eat Linker!"))
        self.setSubTitle(
            self.tr(
                "This tool will assist you in linking your WiiLink Account with Just Eat."
            )
        )

        self.label = QLabel(
            self.tr(
                """Welcome to the WiiLink Just Eat Linker!

With this tool, you'll be able to link your WiiLink Account with Just Eat for use with the Demae Channel.

Press 'Next' to get started!"""
            )
        )
        self.label.setWordWrap(True)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.label)

        self.setLayout(self.layout)


class FinalPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

    def initializePage(self):
        QTimer.singleShot(0, self.disable_back_button)

        self.setTitle(self.tr("Linking success!"))
        self.setSubTitle(
            self.tr("Your Just Eat account has been linked to your WiiLink account!")
        )
        self.label = QLabel(
            self.tr(
                f"""Your Just Eat account has successfully been linked to the Wii with number <strong>{self.wizard().property("wii_no_fancy")}</strong>.</br></br>

Enjoy ordering food on your Wii!"""
            )
        )
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def disable_back_button(self):
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)


class JustEatLinker(QWizard):
    language = QLocale("en")

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load in images
        icon = QIcon(file_path.joinpath("assets", "logo.webp").resolve().as_posix())
        just_eat_icon = QIcon(
            file_path.joinpath("assets", "just_eat_logo.webp").resolve().as_posix()
        )

        match datetime.datetime.now().month:
            case 6:
                pride_flags = file_path.joinpath("assets", "pride_banners").iterdir()
                flags_list = list(pride_flags)

                flag_index = random.randint(0, len(flags_list) - 1)
                selected_flag = flags_list[flag_index]

                background = QIcon(selected_flag.resolve().as_posix())
            case _:
                background = QIcon(
                    file_path.joinpath("assets", "background.webp").resolve().as_posix()
                )

        just_eat_pixmap = just_eat_icon.pixmap(64, 64)
        banner = background.pixmap(700, 120)
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, just_eat_pixmap)
        self.setPixmap(QWizard.WizardPixmap.BannerPixmap, banner)

        self.setWindowIcon(icon)

        # Apply global stylesheet for consistent styling across all pages
        stylesheet_path = file_path.joinpath("style.qss")
        stylesheet = open(stylesheet_path, "r").read()
        stylesheet = stylesheet.replace(
            "%AssetsDir%",
            file_path.joinpath("assets").resolve().as_posix(),
        )
        self.setStyleSheet(stylesheet)

        if "Nightly" not in linker_version and "RC" not in linker_version:
            self.check_for_updates()

        self.setWindowTitle(self.tr("WiiLink Just Eat Linker"))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setSubTitleFormat(Qt.TextFormat.RichText)

        self.setFixedWidth(550)
        self.setFixedHeight(450)

        self.setButtonText(QWizard.WizardButton.NextButton, self.tr("Next"))
        self.setButtonText(QWizard.WizardButton.BackButton, self.tr("Back"))

        self.setPage(0, IntroPage())
        # Skip for now
        self.setPage(1, WiiLinkAccountPage())
        self.setPage(2, WiiNumberSelector())
        self.setPage(3, CountrySelect())
        self.setPage(4, JustEatCredentialsPage())
        self.setPage(5, JustEat2FAPage())
        self.setPage(6, FinalPage())

        self.setStartId(0)

    def check_for_updates(self):
        """Static method to compare the current patcher version to the latest, and inform the user if they aren't up to date

        Returns:
            None"""
        try:
            latest_version = get_latest_version()
        except:
            exception_traceback = traceback.format_exc()
            print(exception_traceback)
            QMessageBox.warning(
                self,
                "WiiLink Just Eat Linker - Warning",
                f"""Unable to check for updates!

{exception_traceback}""",
            )
        else:
            latest_version_split = latest_version.split(".")
            linker_version_split = linker_version.split(".")

            to_update = False

            if len(latest_version_split) == len(linker_version_split):
                for place in range(len(latest_version_split)):
                    if latest_version_split[place] > linker_version_split[place]:
                        to_update = True
                        break
                    elif latest_version_split[place] < linker_version_split[place]:
                        break
            else:
                to_update = True

            if to_update:
                update = QMessageBox.question(
                    self,
                    "WiiLink Just Eat Linker - Update",
                    f"""An update has been detected for the linker, would you like to download it?

Your version: {linker_version}
Latest version: {latest_version}""",
                )
                if update == QMessageBox.StandardButton.Yes:
                    webbrowser.open(
                        "https://github.com/WiiLink24/JustEatLinker/releases/latest"
                    )
                    sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = JustEatLinker()

    wizard.show()
    sys.exit(app.exec())
