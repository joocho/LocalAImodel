#!/usr/bin/env python3
"""
Llama 3.2 3B Fine-tuning for Defense Translation
"""

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import torch

# === 설정 ===
MODEL_NAME = "unsloth/Llama-3.2-3B"  # 또는 "meta-llama/Llama-3.2-3B"
TRAINING_DATA = "defense_training_data.jsonl"
OUTPUT_DIR = "defense_translator_finetuned"
MAX_SEQ_LENGTH = 2048
LORA_RANK = 16

print("=" * 70)
print("Defense Translator Fine-tuning")
print("=" * 70)

# 1. 모델 로드
print("\n1️⃣  모델 로드 중...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,  # Auto-detect
    load_in_4bit=True,  # 4-bit 양자화로 메모리 절약
)

# 2. LoRA 어댑터 추가
print("2️⃣  LoRA 어댑터 추가 중...")
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# 3. 학습 데이터 로드
print(f"3️⃣  학습 데이터 로드 중: {TRAINING_DATA}")
dataset = load_dataset("json", data_files=TRAINING_DATA, split="train")
print(f"   총 {len(dataset)}개 샘플")

# 4. 트레이너 설정
print("4️⃣  트레이너 설정 중...")
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=200,  # 데이터셋 크기에 따라 조정
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

# 5. 학습 시작
print("\n5️⃣  학습 시작...")
print("-" * 70)
trainer_stats = trainer.train()

# 6. 모델 저장
print("\n6️⃣  모델 저장 중...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"\n✅ Fine-tuning 완료!")
print(f"   저장 위치: {OUTPUT_DIR}")
print("=" * 70)

# 7. GGUF 형식으로 변환 (Ollama용)
print("\n7️⃣  GGUF 형식 변환 중 (Ollama용)...")
model.save_pretrained_gguf(
    "defense_translator_gguf",
    tokenizer,
    quantization_method="q4_k_m"
)

print(f"\n✅ GGUF 변환 완료!")
print(f"   저장 위치: defense_translator_gguf/")
print("\n다음 Modelfile로 Ollama에 등록하세요:")
print("""
FROM ./defense_translator_gguf/unsloth.Q4_K_M.gguf

SYSTEM \"\"\"
You are a specialized defense translation AI, fine-tuned on defense documentation.
\"\"\"

PARAMETER temperature 0.2
PARAMETER top_p 0.85
""")