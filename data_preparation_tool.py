#!/usr/bin/env python3
"""
방산 번역 데이터 준비 도구
기존 방산 문서를 AI 학습 데이터로 변환
"""

import json
import re
from pathlib import Path
from typing import List, Tuple, Dict
import PyPDF2


class DefenseDataPreparator:
    """방산 문서를 학습 데이터로 변환"""
    
    def __init__(self):
        self.terminology = {}
        self.examples = []
    
    def load_terminology_from_file(self, filepath: str):
        """
        용어 사전 로드
        
        파일 형식 (TSV):
        fighter aircraft    전투기
        guided missile      유도탄
        """
        self.terminology = {}
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if '\t' in line:
                    en, ko = line.strip().split('\t', 1)
                    self.terminology[en.strip()] = ko.strip()
        
        print(f"✅ {len(self.terminology)}개 용어 로드 완료")
        return self.terminology
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            print(f"✅ PDF 텍스트 추출 완료: {len(text)} 문자")
        except Exception as e:
            print(f"❌ PDF 읽기 오류: {e}")
        
        return text
    
    def split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장으로 분리"""
        # 간단한 문장 분리 (개선 가능)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences
    
    def create_parallel_corpus_from_files(
        self,
        english_file: str,
        korean_file: str,
        output_file: str = "training_data.jsonl"
    ):
        """
        영어/한국어 병렬 파일을 학습 데이터로 변환
        
        파일 형식:
        - 각 줄이 하나의 문장
        - 영어 파일과 한국어 파일의 줄 수가 동일해야 함
        """
        print(f"파일 읽는 중...")
        
        # 파일 읽기
        with open(english_file, 'r', encoding='utf-8') as f:
            english_lines = [line.strip() for line in f if line.strip()]
        
        with open(korean_file, 'r', encoding='utf-8') as f:
            korean_lines = [line.strip() for line in f if line.strip()]
        
        if len(english_lines) != len(korean_lines):
            print(f"⚠️  경고: 영어 {len(english_lines)}줄, 한국어 {len(korean_lines)}줄")
            min_len = min(len(english_lines), len(korean_lines))
            english_lines = english_lines[:min_len]
            korean_lines = korean_lines[:min_len]
        
        # 학습 데이터 생성
        training_data = []
        for en, ko in zip(english_lines, korean_lines):
            # Llama 3.2 형식으로 포맷팅
            formatted_text = (
                f"<|start_header_id|>user<|end_header_id|>\n\n"
                f"Translate to Korean: {en}<|eot_id|>"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n"
                f"{ko}<|eot_id|>"
            )
            training_data.append({"text": formatted_text})
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"✅ {len(training_data)}개 학습 샘플 생성: {output_file}")
        return output_file
    
    def create_few_shot_examples(
        self,
        examples: List[Tuple[str, str]],
        output_file: str = "few_shot_examples.txt"
    ) -> str:
        """
        Few-shot 예제를 Modelfile에 삽입할 형식으로 생성
        
        Args:
            examples: [(영어, 한국어), ...] 튜플 리스트
        """
        formatted_examples = []
        
        for i, (en, ko) in enumerate(examples, 1):
            formatted = f"""Example {i}:
English: "{en}"
Korean: "{ko}"
"""
            formatted_examples.append(formatted)
        
        result = "\n".join(formatted_examples)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"✅ {len(examples)}개 Few-shot 예제 생성: {output_file}")
        return result
    
    def create_modelfile_with_terminology(
        self,
        terminology_dict: Dict[str, str],
        examples: List[Tuple[str, str]],
        output_file: str = "custom-modelfile"
    ):
        """
        용어 사전과 예제를 포함한 Modelfile 생성
        """
        # 용어 사전 포맷팅
        term_lines = [f"- {en} → {ko}" for en, ko in terminology_dict.items()]
        term_section = "\n".join(term_lines)
        
        # 예제 포맷팅
        example_lines = []
        for i, (en, ko) in enumerate(examples, 1):
            example_lines.append(f'Example {i}:\nEnglish: "{en}"\nKorean: "{ko}"\n')
        example_section = "\n".join(example_lines)
        
        # Modelfile 생성
        modelfile_content = f'''FROM llama3.2:3b

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
PARAMETER num_ctx 8192
'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        print(f"✅ Modelfile 생성 완료: {output_file}")
        print(f"   - {len(terminology_dict)}개 용어")
        print(f"   - {len(examples)}개 예제")
        print(f"\n다음 명령으로 모델 생성:")
        print(f"   ollama create defense-translator -f {output_file}")
        
        return output_file
    
    def validate_parallel_corpus(
        self,
        english_file: str,
        korean_file: str
    ) -> Dict[str, any]:
        """병렬 코퍼스 품질 검증"""
        
        with open(english_file, 'r', encoding='utf-8') as f:
            en_lines = [line.strip() for line in f if line.strip()]
        
        with open(korean_file, 'r', encoding='utf-8') as f:
            ko_lines = [line.strip() for line in f if line.strip()]
        
        stats = {
            "english_lines": len(en_lines),
            "korean_lines": len(ko_lines),
            "aligned": len(en_lines) == len(ko_lines),
            "avg_en_length": sum(len(s) for s in en_lines) / len(en_lines) if en_lines else 0,
            "avg_ko_length": sum(len(s) for s in ko_lines) / len(ko_lines) if ko_lines else 0,
            "issues": []
        }
        
        # 품질 체크
        if not stats["aligned"]:
            stats["issues"].append(f"줄 수 불일치: EN={len(en_lines)}, KO={len(ko_lines)}")
        
        # 너무 짧거나 긴 문장 체크
        for i, (en, ko) in enumerate(zip(en_lines, ko_lines)):
            if len(en) < 10 or len(ko) < 5:
                stats["issues"].append(f"라인 {i+1}: 너무 짧음 (EN={len(en)}, KO={len(ko)})")
            if len(en) > 500 or len(ko) > 500:
                stats["issues"].append(f"라인 {i+1}: 너무 김 (EN={len(en)}, KO={len(ko)})")
        
        print("\n=== 데이터 검증 결과 ===")
        print(f"영어 문장: {stats['english_lines']}개")
        print(f"한국어 문장: {stats['korean_lines']}개")
        print(f"정렬 상태: {'✅ OK' if stats['aligned'] else '❌ 불일치'}")
        print(f"평균 길이: EN={stats['avg_en_length']:.1f}, KO={stats['avg_ko_length']:.1f}")
        
        if stats["issues"]:
            print(f"\n⚠️  발견된 문제 {len(stats['issues'])}개:")
            for issue in stats["issues"][:5]:  # 처음 5개만 표시
                print(f"  - {issue}")
        else:
            print("✅ 품질 검증 통과!")
        
        return stats


def main():
    """사용 예시"""
    
    preparator = DefenseDataPreparator()
    
    print("=" * 60)
    print("방산 번역 데이터 준비 도구")
    print("=" * 60)
    
    # 예시 1: 용어 사전 + Few-shot 예제로 Modelfile 생성
    print("\n[방법 1] Few-shot Learning용 Modelfile 생성")
    print("-" * 60)
    
    # 방산 용어 사전
    terminology = {
        "fighter aircraft": "전투기",
        "guided missile": "유도탄",
        "fire control system": "사격통제시스템",
        "target acquisition": "표적 획득",
        "ballistic missile": "탄도미사일",
        "night vision device": "야간투시경",
        "electronic warfare": "전자전",
        "surface-to-air missile": "지대공미사일"
    }
    
    # 번역 예제
    examples = [
        (
            "The fire control system integrates radar and targeting data.",
            "사격통제시스템은 레이더와 표적 데이터를 통합합니다."
        ),
        (
            "Advanced fighter aircraft employ stealth technology.",
            "첨단 전투기는 스텔스 기술을 활용합니다."
        ),
        (
            "The guided missile achieved target lock at maximum range.",
            "유도탄이 최대 사거리에서 표적 고정을 달성했습니다."
        )
    ]
    
    preparator.create_modelfile_with_terminology(
        terminology,
        examples,
        "defense-few-shot.modelfile"
    )
    
    # 예시 2: 병렬 파일을 학습 데이터로 변환
    print("\n[방법 2] Fine-tuning용 학습 데이터 생성")
    print("-" * 60)
    print("다음 파일이 필요합니다:")
    print("  - defense_english.txt (영어 문장, 한 줄에 하나씩)")
    print("  - defense_korean.txt (한국어 번역, 한 줄에 하나씩)")
    print("\n파일이 있다면 다음 코드 주석을 해제하세요:")
    print("""
    # preparator.create_parallel_corpus_from_files(
    #     "defense_english.txt",
    #     "defense_korean.txt",
    #     "defense_training.jsonl"
    # )
    """)
    
    # 예시 3: 데이터 검증
    print("\n[도구] 병렬 코퍼스 검증")
    print("-" * 60)
    print("파일이 있다면 다음 코드 주석을 해제하세요:")
    print("""
    # preparator.validate_parallel_corpus(
    #     "defense_english.txt",
    #     "defense_korean.txt"
    # )
    """)


if __name__ == "__main__":
    main()