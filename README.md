# Ask

Natural-language Omarchy shortcut search. Type what you want; Jev ranks the
three most likely keybindings, copies the chord, and does **not** run it.

This folder is the plugin. `manifest.json` lives at the root so
`omarchy plugin add` can clone it straight into
`~/.config/omarchy/plugins/leo.ask/`.

## Install

```bash
omarchy plugin add https://github.com/leoprodz/leo.ask.git --enable
```

Without `--enable`, review the checkout first, then:

```bash
omarchy plugin enable leo.ask
```

`omarchy plugin add` only clones files. No install hooks, no sudo, nothing
copied onto `PATH`.

## Key

Put `TYPESAFE_API_KEY` in `~/.vault/.env.master`. Either form works:

```
TYPESAFE_API_KEY=...
export TYPESAFE_API_KEY=...
```

`JEV_API_KEY` is accepted as a fallback, as is the same name already in the
environment. **Never commit the key or `~/.vault/`.**

## Bind (optional)

Add this to `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + SHIFT + K", "Ask command", 'python3 "$HOME/.config/omarchy/plugins/leo.ask/ask.py"')
```

## Menu (optional)

Add this to `~/.config/omarchy/extensions/omarchy-menu.jsonc`:

```jsonc
"ask": {
  "icon": "󰍉",
  "label": "Ask",
  "aliases": ["ask", "jev", "command", "nl"],
  "description": "Natural-language shortcut search. Shows the 3 most likely keybindings; does not run them.",
  "action": "python3 \"$HOME/.config/omarchy/plugins/leo.ask/ask.py\""
}
```

## Run

```bash
python3 "$HOME/.config/omarchy/plugins/leo.ask/ask.py"
```

The wrapping overlay (`Ask.qml`) is the prompt. Native `omarchy-menu-input`
elides long text, so Ask keeps its own input surface and falls back to
`--width 800` only if the overlay cannot be summoned.
