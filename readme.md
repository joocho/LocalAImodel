
Ollama is perfect for running Llama 3.2 on your laptop efficiently. Here's how to set up a security code auditing system using Ollama:

## Install Ollama
For macOS or Linux
```
bash# curl -fsSL https://ollama.com/install.sh | sh
```

After installation, verify it's working:
```
bash# ollama --version
```

## Pull the Llama 3.2 3B Model
Store Llama 3.2 with 3B on your computer.
```
bash# ollama pull llama3.2
```

## Create a Custom Modelfile for Security Auditing

Create a file named Modelfile. See m-en-kr-01.modelfile for example.


## Create Your Custom Model

```
bash# ollama create m-en-kr-01 -f m-en-kr-01.modelfile
```

## Use the Model for Code Auditing

### Basic Command Line Usage:

```
bash# ollama run m-en-kr-01 
>>> Send a message (/? for help)
Translate this to Korean: "Artificial intelligence is transforming industries."
```

### From File Usage:
```
ollama run translation-ko-en "Translate to Korean: $(cat input.txt)"
```

### Build a Simple Python Interface

This interface is to read a input file, audit the code, and display the result.

- Create a file named `security_audit.py`:

```python
import requests
import json

def translate_text(text, source_lang="English", target_lang="Korean"):
    url = "http://localhost:11434/api/generate"
    
    prompt = f"""Translate the following text from {source_lang} to {target_lang}.

Source Text:
{text}

Translation:"""
    
    payload = {
        "model": "translation-ko-en",
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    return result['response']

# 사용 예시
text = "Machine learning is a subset of artificial intelligence."
translation = translate_text(text)
print(translation)
```

Usage:
```
python security_audit.py vulnerable_code.py 
```


### Parallel processing sample:

```
pythonimport concurrent.futures
import requests

def translate_chunk(chunk_data):
    chunk_id, text = chunk_data
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "translation-ko-en",
        "prompt": f"Translate to Korean:\n{text}",
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    return chunk_id, response.json()['response']

# Divide input into chunks
chunks = [
    (0, "First paragraph..."),
    (1, "Second paragraph..."),
    (2, "Third paragraph..."),
]

# Parallel translation
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(translate_chunk, chunks))

# Align and merge
results.sort(key=lambda x: x[0])
full_translation = "\n\n".join([r[1] for r in results])
print(full_translation)
```


## Fine-tuning 

### Training data

- JSONL format:

```
json{"prompt": "Translate to Korean: Hello, world!", "response": "안녕하세요, 세상!"}
{"prompt": "Translate to Korean: Machine gun", "response": "기관총"}
```


- LoRA Fine-tuning

```
# unsloth usage
pip install unsloth

# or Hugging Face PEFT
pip install peft transformers datasets
```

## Python script sample:

```python

from unsloth import FastLanguageModel
import torch

# loading model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "meta-llama/Llama-3.2-3B",
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

# LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = True,
)

# training ...
```


## Improve Results with Additional Context

For better results, you can create a more advanced Modelfile that includes examples of common terminology. This technique is called "few-shot prompting" and can significantly improve results without fine-tuning.

### Add to Modelfile:
PARAMETER num_gpu 1
PARAMETER num_thread 8


### Adjusting Context Window 
PARAMETER num_ctx 16384  # longer input


### Batch processing

bash# 
OLLAMA_HOST=0.0.0.0:11434 ollama serve &
OLLAMA_HOST=0.0.0.0:11435 ollama serve &
OLLAMA_HOST=0.0.0.0:11436 ollama serve &



