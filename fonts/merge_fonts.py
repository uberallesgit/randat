import fontforge

BASE = "Roboto-Regular.ttf"
EMOJI = "NotoEmoji-Regular.ttf"
OUTPUT = "RobotoEmoji.ttf"

print(f"Открываю базовый шрифт: {BASE}")
base = fontforge.open(BASE)
print(f"  em size: {base.em}")

print(f"Открываю эмодзи-шрифт: {EMOJI}")
emoji = fontforge.open(EMOJI)
print(f"  em size: {emoji.em}")

if emoji.em != base.em:
    print(f"Масштабирую эмодзи с {emoji.em} на {base.em}")
    emoji.em = base.em

print("Сливаю глифы…")
base.mergeFonts(emoji)
print("  готово")

print(f"Генерирую {OUTPUT}")
base.generate(OUTPUT)
base.close()
emoji.close()
print("Готово.")
