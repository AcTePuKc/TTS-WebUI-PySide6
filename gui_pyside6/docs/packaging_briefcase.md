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

The packaged application should run `install_torch.py` the first time it starts (or include the correct PyTorch wheel in the bundle) so that the appropriate PyTorch build is installed for the user.
