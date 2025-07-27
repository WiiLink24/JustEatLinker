CC=python -m nuitka
ARCH_FLAGS?=

all:
	pyside6-project build pyproject.toml
	$(CC) --show-progress --assume-yes-for-downloads JustEatLinker.py $(ARCH_FLAGS) -o JustEatLinker

clean:
	rm JustEatLinker
	rm -rd JustEatLinker.build/
	rm -rd JustEatLinker.dist/
	rm -rd JustEatLinker.onefile-build/