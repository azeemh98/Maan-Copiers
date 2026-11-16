# Smart QR Print promo video — source

`promo.html` is the whole animation: a 540×960 page with a CSS timeline. `seek(t)` jumps to any second.

Re-render after editing text or timings:

    for k in 0 1 2 3; do node render.js $((k*420)) $(((k+1)*420)) & done; wait   # frames -> fr/ (needs Playwright + Chromium)
    python3 music.py                                                              # music.wav (numpy)
    ffmpeg -framerate 30 -i fr/%05d.jpg -i music.wav -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -shortest out.mp4

Run `mkdir fr` first. `qr.js` holds the QR code. To make it open your real print page, regenerate it with any QR library and replace the SVG.
