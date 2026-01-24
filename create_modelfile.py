#!/usr/bin/env python3
"""
JSON 용어 사전과 예제를 Modelfile에 자동 삽입
"""

import json

def create_modelfile_from_data(
    terminology_file="defense_terminology.json",
    examples_file="defense_examples.jsonl",
    output_file="auto-defense.modelfile"
):
    # 1. 용어 사전 로드
    with open(terminology_file, 'r', encoding='utf-8') as f:
        terms = json.load(f)
    
    term_lines = [f"- {en} → {ko}" for en, ko in terms.items()]
    term_section = "\n".join(term_lines)
    
    # 2. 예제 로드
    examples = []
    with open(examples_file, 'r', encoding='utf-8') as f:
        for line in f:
            examples.append(json.loads(line))
    
    example_lines = []
    for i, ex in enumerate(examples, 1):
        example_lines.append(
            f'Example {i}:\n'
            f'English: "{ex["source"]}"\n'
            f'Korean: "{ex["target"]}"\n'
        )
    example_section = "\n".join(example_lines)
    
    # 3. Modelfile 생성
    modelfile = f'''FROM llama3.2:3b

SYSTEM """
You are a specialized military and defense translation AI.

Standard Defense Terminology (ALWAYS use these translations):
{term_section}

Translation Examples:
{example_section}

Translate accurately while maintaining technical precision and consistency.
"""

PARAMETER temperature 0.2
PARAMETER top_p 0.85
PARAMETER top_k 30
PARAMETER repeat_penalty 1.15
PARAMETER num_predict 4096
PARAMETER num_ctx 8192

TEMPLATE """
{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}
{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}
<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>
"""
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modelfile)
    
    print(f"✅ Modelfile 생성 완료: {output_file}")
    print(f"   - {len(terms)}개 용어")
    print(f"   - {len(examples)}개 예제")
    print(f"\n다음 명령으로 모델 생성:")
    print(f"   ollama create defense-translator -f {output_file}")

if __name__ == "__main__":
    create_modelfile_from_data()