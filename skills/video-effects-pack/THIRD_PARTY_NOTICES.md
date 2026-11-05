# Third-party notices

The code and documentation of this repository are MIT-licensed (see `LICENSE`).
The following third-party files are bundled in the `assets/` folder of the skill (`skills/video-effects-pack/assets/` in the repository) and keep their own licences. Full licence texts are in `assets/licenses/`.

| File | What it is | Licence | Source |
|---|---|---|---|
| `Inter-Regular.otf`, `Inter-Bold.otf`, `Inter-Black.otf` | Inter typeface, version 4.000 | SIL Open Font License 1.1 (`licenses/Inter-OFL-1.1.txt`) | https://github.com/rsms/inter - Copyright 2016 The Inter Project Authors |
| `u2netp.onnx` | U²-Net-P (small) salient-object / person segmentation model, ONNX file | Apache License 2.0 (`licenses/U2Net-Apache-2.0.txt`) | Architecture and weights: https://github.com/xuebinqin/U-2-Net (Qin et al., "U²-Net: Going Deeper with Nested U-Structure for Salient Object Detection", Pattern Recognition 2020) |
| `face_detection_yunet_2023mar.onnx` | YuNet face detector | MIT (`licenses/YuNet-MIT.txt`) | https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet - Copyright (c) 2020 Shiqi Yu |
| `haarcascade_frontalface_default.xml` | Haar cascade face detector (fallback) | Intel License Agreement for Open Source Computer Vision Library (the full text is in the header of the file itself) | OpenCV: https://github.com/opencv/opencv/tree/4.x/data/haarcascades |

## SHA-256 of the bundled binaries

```
1dc81aa64047bfb4246ece435105ec85944f575744d6d850ab7a287fe6b640e7  Inter-Black.otf
00fd6f4691ee8884a33b46bf45851b341927c37c30064f558e1befb242971c49  Inter-Bold.otf
be6d709dcb730ddaf050cbdae6fe89bd56d5d14dc66885639bbf6f06bd03521b  Inter-Regular.otf
309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8  u2netp.onnx
8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4  face_detection_yunet_2023mar.onnx
0f7d4527844eb514d4a4948e822da90fbb16a34a0bbbbc6adc6498747a5aafb0  haarcascade_frontalface_default.xml
```

## Notes

- `u2netp.onnx` is a third-party ONNX conversion of the U²-Net-P model, whose authors publish the architecture and weights under Apache-2.0. The maintainer of this repository did not make the conversion and has not recorded where this particular converted file was first published. If you need a verifiable chain, convert the official `u2netp.pth` yourself and replace the file; the code only needs an ONNX model with the same input/output layout.
- Python dependencies (numpy, opencv-python, Pillow) are not bundled; they are installed separately under their own licences. ffmpeg is not bundled and is used as an external program.
- The pack imitates the look of common video-editor effect presets, implemented from scratch. It is not affiliated with, endorsed by or derived from any video-editor vendor's code or assets, and no vendor logos, names or media are included.
