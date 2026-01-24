#!/usr/bin/env python3
"""
defense_examples.jsonl을 학습용 데이터로 변환
"""

import json

def convert_examples_to_training_data(
    input_file="defense_examples.jsonl",
    output_file="defense_training_data.jsonl"
):
    training_data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            example = json.loads(line)
            
            # Llama 3.2 형식으로 포맷팅
            formatted_text = (
                f"<|start_header_id|>user<|end_header_id|>\n\n"
                f"Translate to Korean: {example['source']}<|eot_id|>"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n"
                f"{example['target']}<|eot_id|>"
            )
            
            training_data.append({"text": formatted_text})
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"✅ {len(training_data)}개 학습 샘플 생성: {output_file}")

if __name__ == "__main__":
    convert_examples_to_training_data()