# Icons

Colour icons used by the vocabulary revision guide (`build/build_vocab_es.py`).
They are [Twemoji](https://github.com/jdecked/twemoji) 15.1.0 SVGs, licensed
CC-BY 4.0 (graphics © Twitter, Inc. and other contributors), credited on the
guide's front page.

Each file is named by the emoji's code point, so the builder can turn any emoji
written in `vocabulario_elemental.md` into its icon. To add one:

    curl -o <codepoint>.svg https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.1.0/assets/svg/<codepoint>.svg
