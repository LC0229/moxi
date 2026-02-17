# Training on AWS (cloud / DevOps)

How to run Moxi training in the cloud so you use AWS correctly and can grow into a full DevOps setup (S3, IAM, SageMaker or EC2).

**→ Step-by-step “do this right now” flow:** see **docs/AWS_TRAINING_FLOW_NOW.md**. **Default:** `make train-aws` submits a **SageMaker** training job when `AWS_ARN_ROLE` is set.

---

## How the LLM course does it (SageMaker + quota, not EC2)

The **llm-twin-course** (decodingml) runs training on **AWS SageMaker**, not on a manual EC2 instance. They use:

- **SageMaker training jobs** — submit a job that runs your training script in a managed GPU environment; data and model live in S3; no SSH or manual instance.
- **Quota** — they work within **SageMaker service quotas** (e.g. max training jobs, instance limits per region). You may need to **request a quota increase** in AWS Service Quotas for SageMaker (e.g. more ml.g5.xlarge training jobs). Some setups also use **Qwak** on top of SageMaker for training/inference.

We currently document **EC2** as the “do this right now” path because we only have a script that uploads data to S3 and prints commands; we do **not** yet submit a SageMaker training job from code. To match the course:

- Prefer **SageMaker** when you can: create a SageMaker training job (HuggingFace container or custom image), point it at S3 data and output, use **AWS_ARN_ROLE** (SageMaker execution role).
- Be aware of **SageMaker quotas** in your region (Service Quotas → SageMaker); request increases if you hit limits.

---

## Why AWS for training

- **GPU:** Training needs a GPU (e.g. 24GB VRAM). AWS provides GPU instances (g5.2xlarge, g5.4xlarge, etc.).
- **DevOps:** Data and models live in S3; training runs as a job (SageMaker) or on an EC2 instance; credentials and roles stay in AWS (no long-lived keys in code).
- **Reproducibility:** Same code runs locally or on AWS; only config and entrypoint change.

---

## 1. What you need on AWS

| Resource | Use |
|----------|-----|
| **IAM user or role** | Credentials for your laptop/CI to call AWS (upload data, submit jobs). |
| **S3 bucket** | Store training data (e.g. `s3://bucket/moxi/data/sft/`) and model outputs (`s3://bucket/moxi/models/`). |
| **SageMaker execution role** | Role that the **training job** assumes. Needs: read from S3 (data), write to S3 (model), pull ECR image if you use a custom container. |
| **SageMaker training job** **or** **EC2 GPU instance** | Where the actual training process runs. |

---

## 2. Config (use the right AWS settings)

In `.env` (or environment) set:

```bash
# Required for AWS training
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-moxi-bucket          # e.g. mycompany-moxi-training
AWS_ARN_ROLE=arn:aws:iam::ACCOUNT:role/YourSageMakerRole   # For SageMaker jobs

# If not using instance profile / SSO (e.g. local or CI):
AWS_ACCESS_KEY=AKIA...
AWS_SECRET_KEY=...
```

- **AWS_S3_BUCKET:** Used by scripts to upload data and download model artifacts (e.g. `s3://your-moxi-bucket/moxi/...`).
- **AWS_ARN_ROLE:** SageMaker training job execution role (must have S3 and ECR permissions).
- **AWS_ACCESS_KEY / AWS_SECRET_KEY:** Only if you’re not using an IAM instance profile or SSO (e.g. when submitting jobs from your laptop).

---

## 3. Process: how to make training run on AWS

### Option A: SageMaker training job (recommended for DevOps)

1. **Prepare SFT data locally:** Have `data/sft/training_dataset.json` (or your dataset path).
2. **Upload data to S3:** e.g. `aws s3 cp data/sft/ s3://your-moxi-bucket/moxi/data/sft/ --recursive`
3. **Run the script that submits the job:** e.g. `python scripts/run_training_on_aws.py` (see below). It will:
   - Use `AWS_S3_BUCKET`, `AWS_ARN_ROLE`, `AWS_REGION` from config.
   - Upload the training script / use a pre-built image or SageMaker’s HuggingFace container.
   - Start a SageMaker training job that runs the same logic as `moxi_train.finetune.main` (dataset from S3, model out to S3).
4. **When the job finishes:** Model artifacts are in S3 (e.g. `s3://bucket/moxi/models/checkpoints/job-name/output/`). Download for inference or use from S3 in your app.

This way **training is fully in AWS** (correct connection: your machine only submits the job; no long-running local GPU).

### Option B: EC2 GPU instance

1. Launch an EC2 instance with a GPU (e.g. g5.2xlarge), AMI with CUDA + Python.
2. Set **AWS credentials** on the instance (instance profile with S3 access, or env vars).
3. Clone the repo, install deps (`poetry install`), upload data from S3 or copy from your machine.
4. Run the **same command** as local:  
   `cd src && PYTHONPATH=$(pwd) python -m moxi_train.finetune.main --dataset /path/to/sft.json --output-dir /path/to/out`
5. Upload checkpoints to S3 when done:  
   `aws s3 cp /path/to/out s3://your-moxi-bucket/moxi/models/checkpoints/ --recursive`

Same training code; only the machine and paths change.

---

## 4. IAM / permissions (best practice)

- **Your user/role (submit jobs):** `sagemaker:CreateTrainingJob`, `s3:PutObject`, `s3:GetObject` on the Moxi bucket (and `iam:PassRole` for the SageMaker role).
- **SageMaker execution role (AWS_ARN_ROLE):**  
  - `s3:GetObject` on `s3://bucket/moxi/data/**`  
  - `s3:PutObject` on `s3://bucket/moxi/models/**`  
  - `ecr:GetDownloadUrlForLayer` if using a custom training image.

Use IAM roles and avoid putting long-lived access keys in code; use **AWS_ACCESS_KEY/AWS_SECRET_KEY** only where necessary (e.g. local dev).

---

## 5. Make target (optional)

You can add to the Makefile:

```makefile
train-aws:  # Submit training job to AWS (set AWS_* in .env)
	cd src && PYTHONPATH=$(PYTHONPATH) python ../scripts/run_training_on_aws.py
```

So the **process to make training work on AWS** is: set AWS config → prepare SFT data → upload to S3 → run script (or Make) to start SageMaker job (or run same command on EC2) → get model from S3. That’s the correct, cloud-engineer way to connect to AWS for training.
