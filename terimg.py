from PIL import Image

from typing import Literal, TypeAlias, Optional

from shutil import get_terminal_size
from sys import argv
import re

import urllib.request
from io import BytesIO

from os import getenv

supports_true_color = getenv('COLORTERM') == 'truecolor'


def fetch_image_from_url(url: str) -> Image.Image:
  with urllib.request.urlopen(url) as response:
    buf = response.read()
    img = Image.open(BytesIO(buf))
    return img


def load_image(path: str) -> Image.Image:
  if path.startswith('http://') or path.startswith('https://'):
    img = fetch_image_from_url(path)
  else:
    img = Image.open(path)
  return img.convert('RGBA')


def resize(img: Image.Image, desired_width: int) -> Image.Image:
  width, height = img.size
  
  new_width = desired_width // 2
  new_height = int((new_width / width) * height)
  
  return img.resize((new_width, new_height))


PixelsArray: TypeAlias = list[list[tuple[int, int, int, int]]]

def to_pixels_array(img: Image.Image) -> PixelsArray:
  width, height = img.size
  pixels = list(img.getdata())
  return [pixels[i * width : (i + 1) * width] for i in range(height)]


def parse_argv() -> tuple[list[str], dict[str, str]]:
  '''
  for instance, if you ran `python3 main.py path/to/image --width 80`, 
  the function will return:
  ```
    regular_args = ['path/to/image'],
    kv_args = { '--width': '80' }
  ```
  '''
  regular_args = []
  kv_args = {}

  prev_key = None
  for arg in argv[1:]:
    if prev_key is None:
      if arg.startswith('--'):
        prev_key = arg
      else:
        regular_args.append(arg)
    else:
      if arg.startswith('--'):
        kv_args[prev_key] = ''
        prev_key = arg
      else:
        kv_args[prev_key] = arg
        prev_key = None
  if prev_key:
    kv_args[prev_key] = ''

  return regular_args, kv_args


def print_help_and_exit():
  print()
  print(f'usage: python3 {argv[0]} path/to/image [--width] [--alpha]')
  print()
  print(f'  path/to/image   local file, or remote url')
  print(f'  --width         number of terminal columns, or a percentage')
  print(f'  --alpha         transparency mode: `threshold` |`whiten` |`blacken` ')
  print()
  exit()


def assert_cmd_args() -> tuple[str, dict[str, str]]:
  regular_args, kv_args = parse_argv()
  optional_keys = ('--width', '--alpha')
  
  if len(regular_args) != 1 or kv_args.keys() - optional_keys:
    print_help_and_exit()
  
  width_arg = kv_args.get('--width', None)
  if width_arg is not None and not re.fullmatch(r'\d+%?', width_arg):
    print_help_and_exit()
  
  alpha_arg = kv_args.get('--alpha', None)
  if alpha_arg is not None and alpha_arg not in ('threshold', 'whiten', 'blacken'):
    print_help_and_exit()
  
  img_path = regular_args[0]
  return img_path, kv_args


def get_desired_width(kv_args: dict[str, str]) -> int:
  width_arg = kv_args.get('--width', None)
  
  if width_arg and not width_arg.endswith('%'):
    return int(width_arg)
  
  terminal_width, _ = get_terminal_size()
  
  if width_arg and width_arg.endswith('%'):
    fraction = int(width_arg[:-1]) / 100
    return int(terminal_width * fraction)
  
  return terminal_width


TransparencyMode = Literal['threshold', 'whiten', 'blacken']

def get_desired_transparency_mode(kv_args: dict[str, str]) -> TransparencyMode:
  return kv_args.get('--alpha', 'whiten')


def ansi_color(r, g, b, alpha = 255, transparency_mode: Optional[TransparencyMode] = None) -> str:
  if alpha < 255:
    if transparency_mode == 'threshold':
      if alpha < 32: return '\033[0m'
    else:
      bg_r, bg_g, bg_b = (0, 0, 0) if transparency_mode == 'blacken' else (255, 255, 255)
      r = round(r * alpha / 255 + bg_r * (255 - alpha) / 255)
      g = round(g * alpha / 255 + bg_g * (255 - alpha) / 255)
      b = round(b * alpha / 255 + bg_b * (255 - alpha) / 255)
      return ansi_color(r, g, b)
  
  if supports_true_color:
    return f'\033[48;2;{r};{g};{b}m'
  
  # fallback to older ansi 256-color palette
  # colors 16 to 231 represent a 6×6×6 color cube, and colors 232 to 255 are grayscale shades.
  if r == g == b:
    color_code = 232 + round(r / 255 * 23)
  else:
    r6, g6, b6 = round(r / 255 * 5), round(g / 255 * 5), round(b / 255 * 5)
    color_code = 16 + (36 * r6) + (6 * g6) + b6
  return f'\033[48;5;{color_code}m'


def print_image(pixels: PixelsArray, transparency_mode: TransparencyMode) -> None:
  print()
  for row in pixels:
    chars = (ansi_color(*rgba, transparency_mode) + '  ' for rgba in row)
    print(''.join(chars) + '\033[0m')
  print()


def main() -> None:
  image_path, kv_args = assert_cmd_args()
  
  desired_width = get_desired_width(kv_args)
  transparency_mode = get_desired_transparency_mode(kv_args)
  
  img = load_image(image_path)
  img = resize(img, desired_width)
  pixels = to_pixels_array(img)
  print_image(pixels, transparency_mode)


if __name__ == '__main__':
  main()
