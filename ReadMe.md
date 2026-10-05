# Industrial Vision Inspector

A real-time vision inspection and product classification system designed for industrial poultry processing and conveyor sorting lines. The system couples a PyTorch deep learning inference engine (EfficientNet-B4) with edge devices (such as a Raspberry Pi with a camera module) via standard TCP socket communication, managed through a Tkinter desktop operator dashboard.

---

## Overview

Industrial Vision Inspector captures product images from an edge camera unit positioned over a conveyor belt, performs real-time classification across distinct poultry cut categories, and returns the classification results to downstream automation hardware (e.g., pneumatic sorting kickers, PLCs, or status indicators). All inference transactions, confidence scores, and visual previews are indexed into a persistent Excel audit log.

---

## Key Features

- **Dual Operating Modes:**
  - **Online Mode (Socket Active):** Starts a TCP server socket on port `5001` to receive image byte streams directly from edge units and transmits inference labels back to the device on port `6000`.
  - **Offline Mode (Folder Watch):** Monitors a local staging directory (`data/received_images/`) and automatically classifies images as they are added.
- **Deep Learning Inference:** Custom classifier head built on `EfficientNet-B4` running with hardware acceleration on NVIDIA GPUs (CUDA) or automated CPU fallbacks.
- **Pretrained Checkpoint Ready:** Includes a pre-trained weights file (`best_model.pth`) directly inside the repository for immediate testing and out-of-the-box trials.
- **Auditory Operator Feedback:** Dispatches class-specific audio alerts asynchronously (`.wav`) via non-blocking worker threads.
- **Audit Logging & Analytics:** Automatically appends timestamps, filenames, predicted classes, and confidence scores into an Excel spreadsheet (`prediction_log.xlsx`).
- **Active Error Flagging:** Allows quality inspectors to flag misclassified items with one click, copying the image to a designated directory (`data/wrong_classifications/`) for dataset curation and active learning retraining.

---

## Technical Specifications & Image Input

- **Backbone Architecture:** EfficientNet-B4 (`PoultryClassifier`) via PyTorch / Torchvision.
- **Target Resolution:** Designed and optimized for **$380 \times 380 \times 3$** RGB images (matching EfficientNet-B4 native input resolution).
- **Inference Pipeline:**
  - Channel ordering: RGB
  - Tensor Normalization: ImageNet standard ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$)
  - Dropout layer: $p = 0.3$ prior to the linear classification layer.
- **Pretrained Model File:** `best_model.pth` (included in the root repository).

---

## Supported Classes

The system is configured to classify five primary poultry cuts:

| Class Name | Description | Associated Audio Cue |
| :--- | :--- | :--- |
| **Breasts** | Chicken breast cuts / fillets | `Breast.wav` |
| **ButterfliedDrumsticks** | Butterflied drumstick cuts | `ButterfliedDrumsticks.wav` |
| **Drumsticks** | Whole drumstick pieces | `Drumsticks.wav` |
| **WholeLeg** | Whole chicken legs (thigh + drumstick) | `WholeLeg.wav` |
| **Wings** | Whole chicken wings | `Wings.wav` |

---

## System Architecture

```
+--------------------+        TCP Port 5001        +-------------------------------+
|    Raspberry Pi    |  ────────────────────────>  |       Host Workstation        |
|  (Camera Module)   |      Image Data Stream      |     (server.py & main.py)     |
+--------------------+                             +-------------------------------+
          ^                                                        |
          |                   TCP Port 6000                        | EfficientNet-B4
          |                 Prediction String                      v Inference
          +-----------------------------------------       +---------------+
                                                           | Classifier    |
                                                           +---------------+
                                                                   |
                                           +-----------------------+-----------------------+
                                           v                                               v
                             [Operator GUI & Audio Alerts]                   [Excel Log & Archive]
```

---

## Repository Structure

```text
├── Logo/
│   └── logo.png                  # Application header logo
├── Sounds/
│   ├── Breast.wav                # Class-specific audio notifications
│   ├── ButterfliedDrumsticks.wav
│   ├── Drumsticks.wav
│   ├── WholeLeg.wav
│   └── Wings.wav
├── data/                         # Auto-generated at initial execution
│   ├── received_images/          # Staging buffer for incoming inspection images
│   ├── output/
│   │   └── prediction_log.xlsx   # Historical inspection log spreadsheet
│   └── wrong_classifications/    # Manually flagged misclassified images
├── audio_player.py               # Asynchronous audio playback worker
├── best_model.pth                # Pretrained PyTorch model checkpoint
├── config.py                     # Centralized settings, network ports, and path resolvers
├── model.py                      # PyTorch EfficientNet-B4 inference module
├── server.py                     # Low-level TCP socket networking routines
├── main.py                       # Tkinter GUI and orchestration thread
└── README.md                     # Project documentation
```

---

## Prerequisites and Installation

### 1. Requirements

- Python 3.9 or newer (Python 3.9 – 3.12 recommended)
- Operating System: Windows 10/11 (fully supported with audio alerts), Linux, or macOS
- Dedicated NVIDIA GPU with CUDA support recommended for industrial line throughput; standard CPU is supported.

### 2. Clone the Repository

```bash
git clone https://github.com/AbdurrahmanCoskun97/Chicken_Classification_Project
cd Chicken_Classification_Project
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

Select either the **GPU** or **CPU** configuration depending on your hardware environment:

#### Option A: GPU (NVIDIA CUDA Acceleration) — *Recommended for Production*
```bash
# Install core dependencies
pip install pillow pandas openpyxl

# Install PyTorch with CUDA 12.1 support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# (Optional: for legacy CUDA 11.8 environments, use 'cu118' instead)
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

Verify GPU availability in your environment:
```bash
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
```

#### Option B: CPU Only — *For Development and Low-Throughput Testing*
```bash
# Install core dependencies
pip install pillow pandas openpyxl

# Install PyTorch (CPU-only build)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

---

## Usage Instructions

1. **Launch the Application:**

   ```bash
   python main.py
   ```

2. **Load Model Weights:**
   - Click the **"Load Model (.pth)"** button in the lower toolbar.
   - Select the pre-trained weights file **`best_model.pth`** provided in the repository root directory (or choose a custom trained `.pth` checkpoint).

3. **Select Operating Mode:**
   - **Online Mode:** Enter the IP address of the target Raspberry Pi into the top IP input field. Ensure the mode button reads **"Mode: Online (Socket Active)"**. The host listens on port `5001` for images and transmits results back to the remote device on port `6000`.
   - **Offline Mode:** Click the mode button to toggle to **"Mode: Offline (Folder Watch)"**. Place or stream $380 \times 380$ images directly into the `data/received_images/` folder to be processed automatically.

4. **Start Inspection:**
   - Click the green **"Start"** button to start the background worker thread.
   - Live camera captures, predicted labels, and confidence bars will update in real-time.
   - Click **"Stop"** at any time to pause inspection and close open sockets.

5. **Flagging Classification Errors:**
   - Select the corresponding item in the historical inspection table.
   - Click **"Mark as Incorrect"** to copy the image into the `data/wrong_classifications/` folder for subsequent dataset refinement.

---

## Network Protocol Details

| Direction | Socket / Role | Default Port | Payload |
| :--- | :--- | :--- | :--- |
| **Client $\rightarrow$ Server** | Server Socket (`server.py`) | `5001` | Raw binary image stream (`.jpg` / `.png`) |
| **Server $\rightarrow$ Client** | Client Socket (`server.py`) | `6000` | Plaintext UTF-8 string (e.g., `Drumsticks`) |

---

## Configuration (`config.py`)

Central system parameters can be modified directly in `config.py`:

```python
# Network Parameters
IMAGE_PORT = 5001              # Port for incoming image streams
SEND_BACK_PORT = 6000          # Port for returning classification labels
DEFAULT_RASPBERRY_IP = "0.0.0.0" # Target Raspberry Pi IP address

# Target Classes
CLASS_NAMES = ['Breasts', 'ButterfliedDrumsticks', 'Drumsticks', 'WholeLeg', 'Wings']
```

---

## Excel Log Format

Every processed inspection item is appended to `data/output/prediction_log.xlsx`:

| Timestamp | Image | Prediction | Confidence |
| :--- | :--- | :--- | :--- |
| 2026-10-05 14:23:05 | image_1791206585.jpg | Drumsticks | 0.9412 |
| 2026-10-05 14:23:08 | image_1791206588.jpg | Wings | 0.8875 |

---

## Packaging as Standalone Executable (Windows)

To build a standalone executable distribution for operator stations without installing Python:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed \
    --add-data "Logo;Logo" \
    --add-data "Sounds;Sounds" \
    main.py
```

*Note: After building, ensure `best_model.pth` is placed in the executable directory or loaded manually via the GUI file picker.*

---
