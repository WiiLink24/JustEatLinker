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

from constants import file_path
from oauth import WiiLinkAccountPage, WiiNumberSelector
from just_eat import JustEatCredentialsPage, CountrySelect, JustEat2FAPage
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWizard, QWizardPage, QApplication, QLabel, QVBoxLayout

app = QApplication(sys.argv)
wizard = QWizard()


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
                f"""Your Just Eat account has successfully been linked to the Wii with number <strong>{self.wizard().property("wii_no")}</strong>.</br></br>

Enjoy ordering food on your Wii!"""
            )
        )
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def disable_back_button(self):
        self.wizard().button(QWizard.WizardButton.BackButton).setEnabled(False)


def main():
    wizard.setWindowTitle(app.tr("WiiLink Just Eat Linker"))
    wizard.setWizardStyle(QWizard.WizardStyle.ModernStyle)
    wizard.setSubTitleFormat(Qt.TextFormat.RichText)

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
    wizard.setPixmap(QWizard.WizardPixmap.LogoPixmap, just_eat_pixmap)
    wizard.setPixmap(QWizard.WizardPixmap.BannerPixmap, banner)

    wizard.setWindowIcon(icon)

    # Apply global stylesheet for consistent styling across all pages
    stylesheet_path = file_path.joinpath("style.qss")
    stylesheet = open(stylesheet_path, "r").read()
    stylesheet = stylesheet.replace(
        "%AssetsDir%",
        file_path.joinpath("assets").resolve().as_posix(),
    )
    wizard.setStyleSheet(stylesheet)

    wizard.setButtonText(QWizard.WizardButton.NextButton, "Next")
    wizard.setButtonText(QWizard.WizardButton.BackButton, "Back")

    wizard.setPage(0, IntroPage())
    # Skip for now
    wizard.setPage(1, WiiLinkAccountPage())
    wizard.setPage(2, WiiNumberSelector())
    wizard.setPage(3, CountrySelect())
    wizard.setPage(4, JustEatCredentialsPage())
    wizard.setPage(5, JustEat2FAPage())
    wizard.setPage(6, FinalPage())

    wizard.setStartId(0)
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
