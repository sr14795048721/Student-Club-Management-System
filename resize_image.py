from PIL import Image

img = Image.open('image/main/校徽.png')
img.thumbnail((100, 100), Image.Resampling.LANCZOS)
img.save('image/main/校徽.png')
print(f'图片已调整，新尺寸: {img.size}')
