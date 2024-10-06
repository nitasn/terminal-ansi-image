from PIL import Image
from sys import argv
import numpy as np
import shutil

import urllib.request
from io import BytesIO


def fetch_image_from_url(url) -> Image:
  with urllib.request.urlopen(url) as response:
    buf = response.read()
    img = Image.open(BytesIO(buf))
    return img


def load_image(path) -> Image:
  if path.startswith('http://') or path.startswith('https://'):
    img = fetch_image_from_url(path)
  else:
    img = Image.open(path)
  return img.convert('RGB')


def resize(img, desired_width) -> Image:
  width, height = img.size
  
  new_width = desired_width // 2
  new_height = int((new_width / width) * height)
  
  return img.resize((new_width, new_height))


def parse_argv() -> tuple[list[str], dict[str, str]]:
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


def assert_cmd_args() -> tuple[str, dict[str, str]]:
  regular_args, kv_args = parse_argv()
  optional_keys = ['--width']
      
  if len(regular_args) != 1 or kv_args.keys() - optional_keys:
    print()
    print(f'usage: python3 {argv[0]} path/to/image [--width]')
    print()
    print(f'  path/to/image   local file, or remote url')
    print(f'  --width         number of terminal columns, or a percentage')
    print()
    exit(1)
  
  img_path = regular_args[0]
  return img_path, kv_args


def get_desired_width(kv_args) -> int:
  width_arg = kv_args.get('--width', '')
  
  if width_arg and not width_arg.endswith('%'):
    return int(width_arg)
  
  terminal_width, _ = shutil.get_terminal_size()
  
  if width_arg and width_arg.endswith('%'):
    fraction = int(width_arg[:-1]) / 100
    return int(terminal_width * fraction)
  
  return terminal_width


def ansii_color(r, g, b) -> str:
  return f'\033[48;2;{r};{g};{b}m'


def print_image(pixels: np.ndarray) -> None:
  for row in pixels:
    print(''.join(ansii_color(r, g, b) + '  ' for r, g, b in row) + '\033[0m')
  print()


def main() -> None:
  image_path, kv_args = assert_cmd_args()
  desired_width = get_desired_width(kv_args)
  img = load_image(image_path)
  img = resize(img, desired_width)
  pixels = np.array(img)
  print_image(pixels)


if __name__ == '__main__':
  main()
