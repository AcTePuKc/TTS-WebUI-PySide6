# Packaging with Briefcase

This project can be packaged into a standalone application using [BeeWare Briefcase](https://briefcase.readthedocs.io/).
Follow the steps below to create platform specific builds.

1. Install Briefcase:
   ```bash
   pip install briefcase
   ```
2. Generate the initial project skeleton:
   ```bash
   briefcase create
   ```
3. Build the application:
   ```bash
   briefcase build
   ```
4. Create the distributable package:
   ```bash
   briefcase package
   ```

On first launch the application attempts to import PyTorch. If it is missing and
`UV_APP_DRY` is not set to `1`, the user will be prompted to install it. The
download can be large (up to **2&nbsp;GB**) and may take several minutes. A
matching NVIDIA CUDA runtime must be present for GPU acceleration; otherwise the
app falls back to CPU mode. If CUDA is not detected or if `UV_APP_DRY=1` is
specified the program runs in CPU mode.

