import sys

from oauth import get_verification_url, get_token, WiiLinkAccountPage, WiiNumberSelector
from just_eat import JustEatCredentialsPage, CountrySelect, JustEat2FAPage
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QApplication,
    QLabel,
    QVBoxLayout,
    QComboBox,
)

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
        self.setTitle(self.tr("Linking success!"))
        self.label = QLabel(
            self.tr(
                f"""Your Just Eat account has successfully been linked to the Wii with number {self.wizard().property("wii_no")}.

                Enjoy ordering food on your Wii!"""
            )
        )
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

def main():
    wizard.setWindowTitle(app.tr("WiiLink Just Eat Linker"))
    wizard.setWizardStyle(QWizard.WizardStyle.ModernStyle)
    wizard.setSubTitleFormat(Qt.TextFormat.RichText)

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


if __name__ == '__main__':
    main()
