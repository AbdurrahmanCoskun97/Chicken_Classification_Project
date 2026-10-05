# Industrial Vision Inspector

A real-time vision inspection and product classification system designed for industrial conveyor lines. The system integrates a PyTorch-based deep learning inference engine (EfficientNet-B4) with edge devices (Raspberry Pi) via TCP socket communication and provides an operator desktop interface built with Tkinter.

---

## Overview

Industrial Vision Inspector captures product images from an edge camera module (such as a Raspberry Pi positioned over a conveyor belt), performs real-time classification using a convolutional neural network, and returns the classification results to downstream automation hardware (e.g., pneumatic sorting arms, PLCs) while logging all inspection data for quality auditing.

---

## Key Features

- **Dual Operating Modes:**
  - **Online Mode:** Starts a TCP server socket on port `5001` to receive images directly from edge devices and returns inference results via port `6000`.
  - **Offline Mode:** Continuously monitors a local directory for incoming image files and processes them sequentially.
- **Deep Learning Inference:** Utilizes a customized `EfficientNet-B4` architecture trained on poultry part categories, running on CUDA-enabled GPUs or CPU fallbacks.
- **Auditory Feedback:** Dispatches class-specific audio cues asynchronously to alert operators on the production line without blocking UI or processing loops.
- **Data Logging and Export:** Records timestamps, image filenames, predicted labels, and confidence scores into an Excel spreadsheet (`prediction_log.xlsx`).
- **Active Error Flagging:** Allows operators to flag false-positive predictions directly from the interface, copying the misclassified sample to a dedicated folder for dataset refinement and retraining.

---

## Supported Classes

The model is configured to identify the following five poultry cuts:

| Class Name | Description | Associated Audio Cue |
| :--- | :--- | :--- |
| **Breasts** | Chicken breast fillets | `Breast.wav` |
| **ButterfliedDrumsticks** | Butterflied drumstick cuts | `ButterfliedDrumsticks.wav` |
| **Drumsticks** | Whole drumsticks | `Drumsticks.wav` |
| **WholeLeg** | Whole chicken legs | `WholeLeg.wav` |
| **Wings** | Whole chicken wings | `Wings.wav` |

---

## System Architecture

```
+--------------------+      TCP Port 5001       +-------------------------------+
|    Raspberry Pi    |  ──────────────────────>  |       Host Workstation        |
|  (Camera Module)   |    Image Transmission    |     (server.py & main.py)     |
+--------------------+                          +-------------------------------+
          ^                                                     |
          |                 TCP Port 6000                       | EfficientNet-B4
          |               Result Transmission                   v Inference
          +--------------------------------------       +---------------+
                                                        | Classifier    |
                                                        +---------------+
                                                                |
                                        +-----------------------+-----------------------+
                                        v                                               v
                          [Operator GUI & Audio Alerts]                   [Excel Log & Archive]
```

---

## Repository Structure

```
├── Logo/
│   └── logo.png                  # Application header logo
├── Sounds/
│   ├── Breast.wav                # Class-specific audio notifications
│   ├── ButterfliedDrumsticks.wav
│   ├── Drumsticks.wav
│   ├── WholeLeg.wav
│   └── Wings.wav
├── data/
│   ├── received_images/          # Incoming image buffer
│   ├── output/
│   │   └── prediction_log.xlsx   # Output log storing historical predictions
│   └── wrong_classifications/    # Manually flagged misclassified images
├── audio_player.py               # Asynchronous audio playback worker
├── config.py                     # Centralized settings, network ports, and path resolvers
├── model.py                      # PyTorch EfficientNet-B4 model wrapper
├── server.py                     # Low-level TCP socket networking routines
├── main.py                       # Tkinter GUI and orchestration thread
└── README.md                     # Project documentation
```

---

## Prerequisites and Installation

### 1. Requirements

- Python 3.8 or newer
- NVIDIA GPU with CUDA support (recommended for high throughput; CPU is supported)
- Windows, Linux, or macOS

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/industrial-vision-inspector.git
cd industrial-vision-inspector
```

### 3. Set Up a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install torch torchvision pandas pillow openpyxl
```

---

## Usage Instructions

1. **Launch the Application:**

   ```bash
   python main.py
   ```

2. **Load Model Weights:**
   - Click the **"Model Seç (.pth)"** (Select Model) button in the lower toolbar.
   - Choose a trained weights file (`.pth` or `.pt`).

3. **Select Operating Mode:**
   - **Online Mode:** Enter the IP address of the destination Raspberry Pi. The server listens on port `5001` for images and transmits results back to the device on port `6000`.
   - **Offline Mode:** Toggle the mode button to **"Mod: Offline"**. The system will scan the selected input directory and evaluate images as they appear.

4. **Start Inspection:**
   - Click the green **"Başlat"** (Start) button to begin the worker loop.
   - Click **"Durdur"** (Stop) at any time to pause inspection and close open sockets.

5. **Flagging Classification Errors:**
   - Select an entry in the inspection log table.
   - Click **"Hatalı Olarak İşaretle"** (Mark as Incorrect) to copy the raw image into the `wrong_classifications/` directory for model re-training.

---

## Configuration (`config.py`)

Key parameters can be adjusted directly in `config.py`:

```python
# Network Parameters
IMAGE_PORT = 5001              # Port for incoming image streams
SEND_BACK_PORT = 6000          # Port for returning classification labels
DEFAULT_RASPBERRY_IP = "0.0.0.0" # Target device IP address

# Classification Target Names
CLASS_NAMES = ['Breasts', 'ButterfliedDrumsticks', 'Drumsticks', 'WholeLeg', 'Wings']
```

---

## Excel Log Format

All inference entries are appended to `data/output/prediction_log.xlsx`:

| Timestamp | Image | Prediction | Confidence |
| :--- | :--- | :--- | :--- |
| 14:23:05 05/10/2026 | image_1791206585.jpg | Drumsticks | 0.9412 |
| 14:23:08 05/10/2026 | image_1791206588.jpg | Wings | 0.8875 |

---

## Packaging as Standalone Executable

To build a standalone Windows binary with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed \
    --add-data "Logo;Logo" \
    --add-data "Sounds;Sounds" \
    main.py
```

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m 'Add NewFeature'`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

---

## License

This project is licensed under the [MIT License](LICENSE).