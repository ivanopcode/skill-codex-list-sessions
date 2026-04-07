.PHONY: install skill

install:
	python3 scripts/setup_main.py $(if $(LOCALE),--locale "$(LOCALE)")

skill:
	@true
