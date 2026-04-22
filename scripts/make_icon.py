#!/usr/bin/env python3
"""
Generates an AppIcon.icns file using the app's gradient colors.
Usage: python3 make_icon.py <output_path>
"""
import struct, zlib, os, subprocess, shutil, sys, tempfile

SIZE = 1024


def write_png(path, pixels):
    """
    Writes a list of RGB pixel rows to a PNG file at the given path.
    @param {str} path - Output file path.
    @param {list} pixels - 2D list of (r, g, b) tuples.
    """
    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)

    raw = b''
    for row in pixels:
        raw += b'\x00'
        for r, g, b in row:
            raw += bytes([r, g, b])

    compressed = zlib.compress(raw, 6)
    png  = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', SIZE, SIZE, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def gradient_color(x, y):
    """
    Returns an (r, g, b) tuple for a pixel at (x, y) using the app gradient.
    Matches: linear-gradient(135deg, #1e40af 0%, #6d28d9 45%, #c026d3 100%)
    @param {int} x - Pixel x position.
    @param {int} y - Pixel y position.
    @returns {tuple}
    """
    t = (x + y) / (2 * (SIZE - 1))
    if t < 0.45:
        s = t / 0.45
        r = int(0x1e + (0x6d - 0x1e) * s)
        g = int(0x40 + (0x28 - 0x40) * s)
        b = int(0xaf + (0xd9 - 0xaf) * s)
    else:
        s = (t - 0.45) / 0.55
        r = int(0x6d + (0xc0 - 0x6d) * s)
        g = int(0x28 + (0x26 - 0x28) * s)
        b = int(0xd9 + (0xd3 - 0xd9) * s)
    return r, g, b


def build_icns(dest_path):
    """
    Renders the gradient, builds an iconset at all required sizes, and writes an .icns file.
    @param {str} dest_path - Full path where the .icns file should be written.
    """
    with tempfile.TemporaryDirectory() as tmp:
        png_path  = os.path.join(tmp, 'icon_1024.png')
        iconset   = os.path.join(tmp, 'AppIcon.iconset')
        icns_path = os.path.join(tmp, 'AppIcon.icns')
        os.makedirs(iconset)

        print('  Rendering gradient…')
        pixels = [[gradient_color(x, y) for x in range(SIZE)] for y in range(SIZE)]
        write_png(png_path, pixels)

        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for s in sizes:
            subprocess.run(
                ['sips', '-z', str(s), str(s), png_path, '--out', f'{iconset}/icon_{s}x{s}.png'],
                check=True, capture_output=True)
            if s <= 512:
                subprocess.run(
                    ['sips', '-z', str(s * 2), str(s * 2), png_path, '--out', f'{iconset}/icon_{s}x{s}@2x.png'],
                    check=True, capture_output=True)

        subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', icns_path], check=True)
        shutil.copy(icns_path, dest_path)
        print(f'  Icon written to {dest_path}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 make_icon.py <output.icns>')
        sys.exit(1)
    build_icns(sys.argv[1])
