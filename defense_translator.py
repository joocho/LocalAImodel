#!/usr/bin/env python3
"""
Defense Translator - 방산 문서 번역 프로그램
Ollama의 defense-translator 모델을 사용하여 파일 번역
"""

import requests
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import time
import re


class DefenseTranslator:
    """방산 문서 번역기"""
    
    def __init__(
        self,
        model_name: str = "defense-translator",
        base_url: str = "http://localhost:11434",
        verbose: bool = True
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.verbose = verbose
        self.api_url = f"{base_url}/api/generate"
        
        # 모델 사용 가능 여부 확인
        if not self._check_model_available():
            print(f"⚠️  경고: '{model_name}' 모델을 찾을 수 없습니다.")
            print(f"다음 명령으로 모델을 생성하세요:")
            print(f"  ollama create {model_name} -f your-modelfile")
    
    def _check_model_available(self) -> bool:
        """모델이 사용 가능한지 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'].startswith(self.model_name) for m in models)
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Ollama 서버 연결 실패: {e}")
        return False
    
    def translate_text(
        self,
        text: str,
        source_lang: str = "English",
        target_lang: str = "Korean",
        temperature: float = 0.2
    ) -> str:
        """
        텍스트 번역
        
        Args:
            text: 번역할 텍스트
            source_lang: 원본 언어
            target_lang: 목표 언어
            temperature: 생성 온도 (0.0-1.0, 낮을수록 일관성 높음)
        
        Returns:
            번역된 텍스트
        """
        prompt = f"""Translate the following {source_lang} text to {target_lang}.
Maintain technical accuracy and terminology consistency.

IMPORTANT: Provide ONLY the translation. Do not include any notes, explanations, or commentary.

Text:
{text}

Translation:"""
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.85,
                "num_predict": 4096
            }
        }
        
        if self.verbose:
            print(f"🔄 번역 중... (길이: {len(text)} 문자)")
        
        try:
            start_time = time.time()
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            translation = result.get('response', '').strip()
            
            # 불필요한 코멘트 제거
            translation = self._remove_commentary(translation)
            
            elapsed = time.time() - start_time
            if self.verbose:
                print(f"✅ 완료 ({elapsed:.1f}초)")
            
            return translation
        
        except requests.exceptions.Timeout:
            return "[ERROR: 번역 시간 초과]"
        except requests.exceptions.RequestException as e:
            return f"[ERROR: API 요청 실패 - {str(e)}]"
        except Exception as e:
            return f"[ERROR: {str(e)}]"
    
    def translate_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        source_lang: str = "English",
        target_lang: str = "Korean",
        chunk_size: int = 1000
    ) -> bool:
        """
        파일 번역
        
        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)
            source_lang: 원본 언어
            target_lang: 목표 언어
            chunk_size: 청크당 최대 문자 수
        
        Returns:
            성공 여부
        """
        input_file = Path(input_path)
        
        # 입력 파일 확인
        if not input_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
            return False
        
        # 출력 파일 경로 생성
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = input_file.parent / f"{input_file.stem}_translated_{timestamp}.txt"
        
        output_file = Path(output_path)
        
        print("=" * 70)
        print("Defense Translator - 방산 문서 번역")
        print("=" * 70)
        print(f"입력 파일: {input_file}")
        print(f"출력 파일: {output_file}")
        print(f"번역 방향: {source_lang} → {target_lang}")
        print(f"모델: {self.model_name}")
        print("-" * 70)
        
        try:
            # 파일 읽기 (확장자에 따라 다른 방식 사용)
            print(f"📖 파일 읽는 중...")
            file_ext = input_file.suffix.lower()
            
            if file_ext == '.pdf':
                content = self._read_pdf(input_file)
            elif file_ext in ['.docx', '.doc']:
                content = self._read_docx(input_file)
            else:
                # 텍스트 파일
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            if not content.strip():
                print("❌ 파일이 비어있습니다.")
                return False
            
            print(f"   총 {len(content)} 문자")
            
            # 문단 단위로 분할
            paragraphs = self._split_into_paragraphs(content)
            print(f"   {len(paragraphs)}개 문단으로 분할")
            
            # 번역 실행
            print(f"\n🚀 번역 시작...")
            translations = []
            total_paragraphs = len(paragraphs)
            
            for i, para in enumerate(paragraphs, 1):
                if not para.strip():
                    translations.append("")
                    continue
                
                print(f"\n[{i}/{total_paragraphs}] ", end="")
                translation = self.translate_text(para, source_lang, target_lang)
                translations.append(translation)
                
                # 진행률 표시
                progress = (i / total_paragraphs) * 100
                print(f"진행률: {progress:.1f}%")
            
            # 결과 저장
            print(f"\n💾 결과 저장 중...")
            full_translation = "\n\n".join(translations)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_translation)
            
            print(f"✅ 번역 완료!")
            print(f"   출력 파일: {output_file}")
            print(f"   번역된 문자 수: {len(full_translation)}")
            print("=" * 70)
            
            return True
        
        except UnicodeDecodeError:
            print("❌ 파일 인코딩 오류. UTF-8 형식인지 확인하세요.")
            return False
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return False
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """텍스트를 문단으로 분할"""
        # 빈 줄로 구분된 문단 분리
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _remove_commentary(self, text: str) -> str:
        """
        번역 결과에서 불필요한 코멘트 제거
        
        Args:
            text: 번역된 텍스트
        
        Returns:
            코멘트가 제거된 텍스트
        """
        # 제거할 패턴들
        patterns = [
            r'\n*Note:.*$',
            r"\n*I've (?:translated|followed|used).*$",
            r"\n*If you(?:'d| would) like.*$",
            r'\n*Please let me know.*$',
            r'\n*Would you like.*$',
            r'\n*Let me know if.*$',
            r'\n*I can (?:help|assist|translate).*$',
            r'\n*Feel free to.*$',
            r'\n*Here is the translation.*$',
            r'\n*Translation:.*?\n',
        ]
        
        cleaned_text = text
        for pattern in patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # 앞뒤 공백 제거
        cleaned_text = cleaned_text.strip()
        
        # 여러 줄 공백을 두 줄로 정리
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text
    
    def _read_pdf(self, pdf_path: Path) -> str:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            추출된 텍스트
        """
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                print(f"   PDF 페이지 수: {total_pages}")
                
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text += page_text + "\n\n"
                    
                    if self.verbose and (i + 1) % 10 == 0:
                        print(f"   페이지 {i + 1}/{total_pages} 읽는 중...")
            
            return text.strip()
        
        except ImportError:
            print("❌ PyPDF2 라이브러리가 필요합니다.")
            print("   설치: pip install PyPDF2")
            raise
        except Exception as e:
            print(f"❌ PDF 읽기 오류: {e}")
            raise
    
    def _read_docx(self, docx_path: Path) -> str:
        """
        Word 문서(.docx)에서 텍스트 추출
        
        Args:
            docx_path: DOCX 파일 경로
        
        Returns:
            추출된 텍스트
        """
        try:
            import docx
            
            doc = docx.Document(docx_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            return "\n\n".join(paragraphs)
        
        except ImportError:
            print("❌ python-docx 라이브러리가 필요합니다.")
            print("   설치: pip install python-docx")
            raise
        except Exception as e:
            print(f"❌ DOCX 읽기 오류: {e}")
            raise
    
    def translate_batch_files(
        self,
        input_files: List[str],
        output_dir: Optional[str] = None,
        source_lang: str = "English",
        target_lang: str = "Korean"
    ):
        """
        여러 파일 일괄 번역
        
        Args:
            input_files: 입력 파일 경로 리스트
            output_dir: 출력 디렉토리 (None이면 입력 파일과 같은 위치)
            source_lang: 원본 언어
            target_lang: 목표 언어
        """
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        total_files = len(input_files)
        
        print(f"\n📦 일괄 번역 시작: {total_files}개 파일\n")
        
        for i, input_file in enumerate(input_files, 1):
            print(f"\n{'='*70}")
            print(f"파일 {i}/{total_files}: {input_file}")
            print('='*70)
            
            if output_dir:
                input_path = Path(input_file)
                output_file = output_path / f"{input_path.stem}_translated.txt"
            else:
                output_file = None
            
            success = self.translate_file(
                input_file,
                output_file,
                source_lang,
                target_lang
            )
            
            if success:
                success_count += 1
        
        print(f"\n{'='*70}")
        print(f"일괄 번역 완료: {success_count}/{total_files} 성공")
        print('='*70)


def main():
    """CLI 인터페이스"""
    parser = argparse.ArgumentParser(
        description="Defense Translator - 방산 문서 번역 프로그램",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 단일 파일 번역
  python defense_translator.py input.txt
  
  # PDF 파일 번역
  python defense_translator.py document.pdf
  
  # 출력 파일 지정
  python defense_translator.py input.txt -o output.txt
  
  # 여러 파일 일괄 번역
  python defense_translator.py file1.txt file2.txt file3.txt
  
  # 출력 디렉토리 지정
  python defense_translator.py *.pdf -d translated/
  
  # 다른 모델 사용
  python defense_translator.py input.txt -m translation-ko-en
  
  # 한국어 → 영어 번역
  python defense_translator.py input.txt --source Korean --target English
        """
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        help='번역할 입력 파일(들)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='출력 파일 경로 (단일 파일 번역 시만 사용)'
    )
    
    parser.add_argument(
        '-d', '--output-dir',
        help='출력 디렉토리 (여러 파일 번역 시)'
    )
    
    parser.add_argument(
        '-m', '--model',
        default='defense-translator',
        help='사용할 Ollama 모델 (기본: defense-translator)'
    )
    
    parser.add_argument(
        '--source',
        default='English',
        help='원본 언어 (기본: English)'
    )
    
    parser.add_argument(
        '--target',
        default='Korean',
        help='목표 언어 (기본: Korean)'
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:11434',
        help='Ollama 서버 URL (기본: http://localhost:11434)'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='진행 상황 메시지 숨기기'
    )
    
    args = parser.parse_args()
    
    # 번역기 초기화
    translator = DefenseTranslator(
        model_name=args.model,
        base_url=args.url,
        verbose=not args.quiet
    )
    
    # 단일 파일 vs 다중 파일
    if len(args.input_files) == 1 and not args.output_dir:
        # 단일 파일 번역
        success = translator.translate_file(
            args.input_files[0],
            args.output,
            args.source,
            args.target
        )
        sys.exit(0 if success else 1)
    else:
        # 여러 파일 일괄 번역
        translator.translate_batch_files(
            args.input_files,
            args.output_dir,
            args.source,
            args.target
        )


if __name__ == "__main__":
    main()