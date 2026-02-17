# AWS training — flow to do right now

Step-by-step: get the base model from Hugging Face, prepare SFT data, then run training on AWS.

**Default: SageMaker.** Running `make train-aws` with `AWS_ARN_ROLE` set in `.env` submits a **SageMaker HuggingFace training job** (same as the LLM course). Use **AWS Service Quotas → SageMaker** if you hit quota limits. EC2 is a fallback if you pass `--ec2` or don’t set the role.

---

## 1. Hugging Face (base model)

The **base model** (e.g. Llama-3.2-3B-Instruct) is downloaded **when training runs** — on your machine for local training, or on the EC2 instance for AWS. You don’t have to download it separately for AWS.

**Do this once:**

1. Go to [huggingface.co](https://huggingface.co) → Settings → Access Tokens → Create token (read).
2. In `.env` set:
   ```bash
   HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxx
   ```
3. (Optional) **Pre-download locally** (only if you want to train locally or cache):
   ```bash
   make download-base-model
   ```
   This uses `MODEL_ID` from config (default: `meta-llama/Llama-3.2-3B-Instruct`). For **AWS only**, you can skip this; the EC2 run will download the model when you start training.

---

## 2. SFT data (you need this before AWS)

Training needs **SFT data** in `data/sft/training_dataset.json`.

**If you already have chunks** (e.g. `training_data/readme_chunks.json` or `data/chunks/readme_chunks.json`):

```bash
# Set OPENAI_API_KEY in .env, then:
make generate-sft-dataset
# Optional test with fewer samples:
make generate-sft-dataset LIMIT=100
```

**If you don’t have chunks yet:**

```bash
make moxi-collect    # then
make moxi-chunk      # then
make generate-sft-dataset
```

Check that this file exists: **`data/sft/training_dataset.json`** (or `data/sft/` with that file in it).

---

## 3. AWS setup (one-time)

1. **Create an S3 bucket** (e.g. `my-moxi-training`).
2. **In `.env` set:**
   ```bash
   AWS_REGION=us-east-1
   AWS_S3_BUCKET=my-moxi-training
   # If not using instance profile / SSO (e.g. from your laptop):
   AWS_ACCESS_KEY=AKIA...
   AWS_SECRET_KEY=...
   ```
3. **Install and configure AWS CLI** on your laptop (if not already):
   ```bash
   aws configure
   # or export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
   ```

---

## 4. Upload data and start training (SageMaker by default)

1. Set **`AWS_ARN_ROLE`** in `.env` (SageMaker execution role with S3 access).
2. Install SDK: **`poetry install --with aws`**.
3. Run:
   ```bash
   make train-aws
   ```
   This uploads `data/sft/` to S3 and **submits a SageMaker HuggingFace training job**. When the job finishes, model artifacts are in `s3://<bucket>/moxi/models/`.

To skip SageMaker and only get EC2 commands: **`PYTHONPATH=src python scripts/run_training_on_aws.py --ec2`** (or leave `AWS_ARN_ROLE` unset).

---

## 5. On the EC2 GPU instance (e.g. g5.2xlarge)

1. **Launch an EC2 instance** with a GPU (e.g. **g5.2xlarge**), Amazon Linux 2 or Ubuntu. Attach an IAM role with S3 read/write (or configure `aws configure` with keys).

2. **Set Hugging Face token** (so training can download the base model):
   ```bash
   export HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxx
   ```

3. **Sync training data from S3** (use the bucket and region from your `.env`):
   ```bash
   aws s3 sync s3://YOUR_BUCKET/moxi/data/sft/ /tmp/moxi/data/sft/ --region us-east-1
   ```

4. **Clone repo and install:**
   ```bash
   git clone https://github.com/YOUR_USER/moxi.git && cd moxi
   poetry install
   ```

5. **Run training** (this will **download the base model from Hugging Face** on first run, then train):
   ```bash
   cd src && PYTHONPATH=$(pwd) poetry run python -m moxi_train.finetune.main \
     --dataset /tmp/moxi/data/sft/training_dataset.json \
     --output-dir /tmp/moxi/models/checkpoints
   ```

6. **Upload trained model back to S3:**
   ```bash
   aws s3 sync /tmp/moxi/models/ s3://YOUR_BUCKET/moxi/models/checkpoints/ --region us-east-1
   ```

Replace `YOUR_BUCKET` and region with your `AWS_S3_BUCKET` and `AWS_REGION`.

---

## Flow summary (right now)

| Order | Where        | What |
|-------|--------------|------|
| 1     | Laptop       | Get Hugging Face token → put in `.env` as `HUGGINGFACE_ACCESS_TOKEN`. |
| 2     | Laptop       | Have SFT data: `make generate-sft-dataset` (after chunks exist). |
| 3     | Laptop       | Create S3 bucket; set `AWS_S3_BUCKET` and `AWS_ARN_ROLE` (and optional AWS keys) in `.env`. |
| 4     | Laptop       | Run `poetry install --with aws`, then `make train-aws` → uploads data to S3 and **submits SageMaker job**. |
| 5     | SageMaker    | Job runs in AWS; model artifacts in S3. (Or use EC2 with `--ec2`.) |

So: **SageMaker** = default when `AWS_ARN_ROLE` is set. **EC2** = fallback with `--ec2` or no role.
