from pathlib import Path
from typing import Tuple, List, Optional
import torch
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import efficientnet_b4
from PIL import Image


class PoultryClassifier:
    """Handles EfficientNet architecture initialization and inference."""

    def __init__(self, class_names: List[str]):
        self.class_names = class_names
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[torch.nn.Module] = None

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def load_weights(self, model_path: str | Path) -> None:
        """Constructs the model architecture and loads pretrained weights."""
        net = efficientnet_b4(weights=None)
        in_features = net.classifier[1].in_features
        net.classifier[1] = torch.nn.Sequential(
            torch.nn.Dropout(p=0.3),
            torch.nn.Linear(in_features, len(self.class_names))
        )

        state_dict = torch.load(str(model_path), map_location=self.device)
        net.load_state_dict(state_dict)
        net.to(self.device)
        net.eval()
        self.model = net

    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, image_path: str | Path) -> Tuple[str, float]:
        """Runs model inference on an image and returns class label and confidence score."""
        if not self.is_loaded():
            raise RuntimeError("Model is not loaded. Call load_weights() first.")

        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(input_tensor)
            probs = F.softmax(output, dim=1).cpu().numpy()[0]
            pred_idx = probs.argmax()

            label = self.class_names[pred_idx]
            confidence = float(probs[pred_idx])

        return label, confidence