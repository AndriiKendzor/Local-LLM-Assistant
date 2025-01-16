from PIL import Image

# Завантажуємо зображення
img = Image.open("img/only_logo-removebg-preview.png")

# Змінюємо розмір до 32x32
img = img.resize((32, 32), Image.Resampling.LANCZOS)

# Зберігаємо у форматі PNG
img.save("img/only_logo_resized.png")

# За потреби, зберігаємо у форматі ICO
img.save("img/only_logo_resized.ico", format="ICO")