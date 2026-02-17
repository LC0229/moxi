# How training works

End-to-end process from data to a trained model you can use for README generation.

---

## 1. What training does

Training **fine-tunes a base LLM** (e.g. Llama-3.2-3B) so it learns to **generate README text** given:

- **Input:** A file tree (list of paths like `["src/main.py", "README.md"]`) and optional project type.
- **Output:** README-style markdown (sections, tone, structure).

We use **SFT (supervised fine-tuning)** with **LoRA** (low-rank adaptation) so we don’t train the full model, only a small adapter. That keeps compute and memory manageable (e.g. one GPU like AWS g5.2xlarge).

**Final result:** A **trained adapter** (or merged model) saved under `models/checkpoints/` (or your `--output-dir`). You use that later in an inference step to generate READMEs for new repos.

---

## 2. Pipeline steps (in order)

| Step | What | Command / output |
|------|------|-------------------|
| **1. Collect** | Get READMEs + file trees from awesome-readme lists | `make moxi-collect` → `data/collection/` + optional MongoDB |
| **2. Chunk** | Split each README into chunks, keep file_tree per chunk | `make moxi-chunk` → `data/chunks/readme_chunks.json` |
| **3. SFT dataset** | Turn chunks into (instruction, input, output) for the model | `make generate-sft-dataset` → `data/sft/training_dataset.json` |
| **4. Train** | Run SFT + LoRA on the dataset | `make moxi-train` → `models/checkpoints/` (or AWS, see below) |
| **5. Infer** | Use trained model to generate README from file_tree | (To implement; uses saved model) |

Training is **step 4**. It only runs after you have **SFT data** in `data/sft/` (or a path you pass with `--dataset`).

---

## 3. Training components (what we have)

| Component | Role |
|-----------|------|
| **moxi_train.finetune.main** | Entry point: parses args, loads dataset path, calls trainer. |
| **SFTTrainerWrapper** | Loads base model + tokenizer, builds Alpaca-format prompts from your JSON, runs TRL `SFTTrainer` with LoRA. |
| **LoRAConfig** | LoRA rank, alpha, target modules (in `moxi_train.finetune.lora_config`). |
| **CometTracker** | Optional experiment tracking (Comet ML). |
| **Dataset** | JSON in Alpaca-style: `instruction`, `input` (e.g. file_tree), `output`/`content`. Can merge with public dataset (e.g. FineTome-Alpaca) via settings or `--no-public-dataset`. |

**Input to training:** A JSON file (e.g. `data/sft/training_dataset.json`) with one object per sample, e.g.:

```json
{
  "instruction": "Generate a README for this project.",
  "input": "File tree: src/main.py, requirements.txt, ...",
  "output": "# My Project\n\n..."
}
```

**Output:** Checkpoints under `output_dir` (default `models/checkpoints/`), including a `final` adapter you can load for inference.

---

## 4. Commands to run training

**Local (one machine with GPU):**

```bash
# Ensure SFT data exists, then:
make moxi-train
# or with options:
cd src && PYTHONPATH=$(pwd) poetry run python -m moxi_train.finetune.main \
  --dataset ../data/sft/training_dataset.json \
  --output-dir ../models/checkpoints \
  --epochs 3 --batch-size 2
```

**Cloud (AWS):** Set `AWS_S3_BUCKET` (and optional `AWS_ARN_ROLE`) in `.env`, then run **`make train-aws`**. That uploads SFT data to S3 and prints exact EC2 commands to run the same training in the cloud. See **docs/TRAINING_ON_AWS.md** for IAM, S3, and DevOps setup.

---

## 5. Summary flow to “final result”

1. **Collect** → READMEs + file trees in `data/collection/`.
2. **Chunk** → `data/chunks/readme_chunks.json`.
3. **Build SFT dataset** → (instruction, input, output) → `data/sft/training_dataset.json`.
4. **Train** → `make moxi-train` (or run on AWS) → **trained model** in `models/checkpoints/`.
5. **Use the model** → Inference (Phase 5) loads the adapter and generates README from a new repo’s file_tree.

Training is step 4; it consumes the SFT dataset and produces the model. Everything before is data prep; everything after is inference.
