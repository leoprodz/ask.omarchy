# Ask

You already know Omarchy has a shortcut for the thing you want. You don't
remember which one.

The menu search (`Super+Space`) and the keybindings overlay (`Super+K`) are
keyword matchers. The cheatsheet is a list you scroll. None of them take a
sentence like "move this to the other monitor" and give you the chord.

Ask is that prompt. Type what you want. [Jev](https://typesafe.ai) ranks
the three most likely shortcuts against **your** keybindings
(`omarchy menu keybindings --print` — the chords, not `omarchy commands`).
It copies the top one. It does **not** run it.

There's a second, dumber problem: native `omarchy-menu-input` crops long
text with an ellipsis. A real sentence doesn't fit. Ask brings its own
overlay so the prompt wraps, and only falls back to `--width 800` if that
overlay can't be summoned.

## Install

```bash
omarchy plugin add https://github.com/leoprodz/ask.omarchy.git --enable
```

Without `--enable`, read the checkout first, then:

```bash
omarchy plugin enable ask.omarchy
```

`omarchy plugin add` only clones files. No install hooks, no sudo, nothing
copied onto `PATH`. The folder lands at `~/.config/omarchy/plugins/ask.omarchy/`
because that is the plugin id.

## Key

Put `TYPESAFE_API_KEY` in `~/.vault/.env.master`. Either form works:

```
TYPESAFE_API_KEY=...
export TYPESAFE_API_KEY=...
```

`JEV_API_KEY` is accepted as a fallback, as is the same name already in the
environment. **Never commit the key or `~/.vault/`.**

## Bind (optional)

```lua
o.bind("SUPER + SHIFT + K", "Ask command", 'python3 "$HOME/.config/omarchy/plugins/ask.omarchy/ask.py"')
```

## Menu (optional)

```jsonc
"ask": {
  "icon": "󰍉",
  "label": "Ask",
  "aliases": ["ask", "jev", "command", "nl"],
  "description": "Natural-language shortcut search. Shows the 3 most likely keybindings; does not run them.",
  "action": "python3 \"$HOME/.config/omarchy/plugins/ask.omarchy/ask.py\""
}
```

## Run

```bash
python3 "$HOME/.config/omarchy/plugins/ask.omarchy/ask.py"
```

Author: Leo Prodz. MIT.
