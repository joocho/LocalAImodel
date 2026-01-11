
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

Create a file named Modelfile:

```
FROM llama3.2

# System prompt that specializes the model for security auditing
SYSTEM """
You are a specialized AI security code auditor. Analyze provided code for security vulnerabilities including:
- SQL injection
- XSS vulnerabilities
- Authentication flaws
- CSRF vulnerabilities
- Insecure direct object references
- Security misconfigurations
- Sensitive data exposure
- Broken access control
- Insufficient logging & monitoring

For each vulnerability found:
1. Identify the specific line or section with the issue
2. Explain why it's vulnerable and potential impact
3. Provide a secure code alternative
4. Reference relevant security standards (OWASP, CWE) when applicable

Prioritize findings by severity (Critical, High, Medium, Low).
"""

# Optional parameters to improve performance
PARAMETER temperature 0.2
PARAMETER top_p 0.8
PARAMETER seed 42
```


## Create Your Custom Model

```
bash# ollama create security-code-audit -f Modelfile
```

## Use the Model for Code Auditing

### Basic Command Line Usage:

```
bash# ollama run security-code-audit 
>>> Send a message (/? for help)
```
Copy and paste the following inference:

```python
Audit this code for security vulnerabilities:
def login(username, password):
    query = \"SELECT * FROM users WHERE username = '\" + username + \"' AND password = '\" + password + \"'\"
    result = db.execute(query)
    if result:
        return generate_session_token()
    return None
```

### Build a Simple Python Interface

This interface is to read a input file, audit the code, and display the result.

- install ollama 

```
pip install ollama
```
- Create a file named `security_audit.py`:

```python
import ollama
import argparse
import os

def audit_file(file_path):
    """Audit a single file for security vulnerabilities."""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        file_ext = os.path.splitext(file_path)[1][1:]  # Get extension without dot
        
        prompt = f"Audit this {file_ext} code for security vulnerabilities:\n```{file_ext}\n{code}\n```"
        
        response = ollama.chat(
            model='security-code-audit',
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
        
        print(f"\n--- SECURITY AUDIT RESULTS FOR {file_path} ---\n")
        print(response['message']['content'])
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Security code audit tool using Ollama')
    parser.add_argument('files', nargs='+', help='Files to audit')
    
    args = parser.parse_args()
    
    for file_path in args.files:
        audit_file(file_path)

if __name__ == "__main__":
    main()
```

Usage:
```
python security_audit.py vulnerable_code.py 
```

## Improve Results with Additional Context

For better results, you can create a more advanced Modelfile that includes examples of common vulnerabilities and their fixes. This technique is called "few-shot prompting" and can significantly improve results without fine-tuning.
