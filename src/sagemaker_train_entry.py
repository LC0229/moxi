"""
SageMaker training entrypoint.

Runs inside the SageMaker HuggingFace container. Reads SM_CHANNEL_TRAIN and
SM_MODEL_DIR, then calls moxi_train.finetune.main so the same training code
runs as local/EC2. Install: poetry install --with aws (sagemaker SDK) to submit.
"""

import os
import sys


def main():
    train_dir = os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train")
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    dataset = os.path.join(train_dir, "training_dataset.json")
    if not os.path.isfile(dataset):
        # Try first .json in dir (SageMaker might unpack with different name)
        for f in os.listdir(train_dir):
            if f.endswith(".json"):
                dataset = os.path.join(train_dir, f)
                break
    # Override argv so moxi_train.finetune.main sees correct args
    sys.argv = [
        "sagemaker_train_entry",
        "--dataset", dataset,
        "--output-dir", model_dir,
    ]
    from moxi_train.finetune.main import main as train_main
    train_main()


if __name__ == "__main__":
    main()
