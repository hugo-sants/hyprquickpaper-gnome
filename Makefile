.PHONY: install uninstall cache run

install:
	bash ./scripts/install.sh

uninstall:
	bash ./scripts/uninstall.sh

cache:
	bash ./scripts/cache.sh $(CURDIR)

run:
	GSK_RENDERER=gl python3 app.py