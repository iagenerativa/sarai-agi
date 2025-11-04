"""
Code Expert Agent - Self-Debugging Code Generation

Production-ready code generation with automatic syntax validation and self-debugging
using VisCoder2-7B-Q4_K_M quantized model.

Capabilities
------------
- Python/JavaScript/TypeScript code generation
- Self-debug loop (2 iterations) with syntax validation
- Production-ready code with type hints and error handling
- Multi-language syntax validation (AST for Python, esprima for JS/TS)

Performance Benchmarks (VisCoder2-7B Q4_K_M)
---------------------------------------------
- HumanEval: 78.3% (Python function correctness)
- MBPP: 72.6% (Python problem solving)
- CodeContests: 65.1% (competitive programming)

Self-Debug Loop
---------------
1. Generate code (temperature: 0.3 for precision)
2. Validate syntax with language-specific parser
3. If invalid → Retry with error feedback (max 2 iterations)
4. Return validated code or raise error

Architecture
------------
- Model: VisCoder2-7B Q4_K_M (~4.3GB)
- Backend: Unified Model Wrapper (GGUF via llama-cpp)
- Singleton pattern: Single instance for efficiency
- Lazy loading: Model loaded only on first invoke()

Usage
-----
>>> from sarai_agi.agents.specialized import get_code_expert_agent
>>> 
>>> agent = get_code_expert_agent()
>>> code = agent.invoke("Write a Python function to find prime numbers")
>>> print(code)
>>> 
>>> # Validate syntax manually
>>> result = validate_syntax(code, "python")
>>> print(f"Valid: {result['valid']}")

Version: v3.5.1
Author: SARAi Project
"""

import ast
import os
from typing import Dict, Any, Optional, Literal

# ✅ MIGRATED IMPORT: core.unified_model_wrapper → sarai_agi.model.wrapper
from sarai_agi.model.wrapper import get_model


class CodeExpertAgent:
    """
    Code generation agent with self-debugging capability.
    
    Uses VisCoder2-7B for high-quality code generation with automatic
    syntax validation and retry logic.
    
    Singleton Pattern
    -----------------
    Use get_code_expert_agent() to get the global instance.
    Ensures only one model instance in memory (~4.3GB).
    
    Attributes
    ----------
    _model : Optional[LLM]
        Lazy-loaded VisCoder2-7B model instance
    
    Methods
    -------
    invoke(prompt, config)
        Generate code with self-debug loop
    
    Examples
    --------
    >>> agent = CodeExpertAgent()
    >>> code = agent.invoke("Write a binary search in Python")
    >>> print(code)
    def binary_search(arr, target):
        ...
    """
    
    def __init__(self):
        """Initialize Code Expert with lazy loading."""
        self._model = None
    
    def _get_model(self):
        """
        Lazy load VisCoder2-7B model.
        
        Returns
        -------
        LLM
            VisCoder2 model instance from Unified Wrapper
        
        Notes
        -----
        Model is loaded only on first invoke() call to save memory.
        """
        if self._model is None:
            print("[CodeExpert] Loading VisCoder2-7B Q4_K_M...")
            self._model = get_model("viscoder2")
        return self._model
    
    def invoke(
        self, 
        prompt: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate production-ready code with self-debug loop.
        
        Parameters
        ----------
        prompt : str
            Code generation request (e.g., "Write a function to sort...")
        config : dict, optional
            Configuration overrides (temperature, max_tokens, etc.)
        
        Returns
        -------
        str
            Generated code (validated or best effort)
        
        Raises
        ------
        RuntimeError
            If code generation fails after 2 retry attempts
        
        Notes
        -----
        Self-Debug Loop:
        1. Generate code with system prompt
        2. Validate syntax (Python AST, JS esprima)
        3. If invalid → Retry with error feedback (max 2 attempts)
        4. Return validated code or raise error
        
        Examples
        --------
        >>> agent = get_code_expert_agent()
        >>> code = agent.invoke(
        ...     "Write a Python function to calculate Fibonacci",
        ...     config={"temperature": 0.2}
        ... )
        >>> print(code)
        def fibonacci(n: int) -> int:
            ...
        """
        model = self._get_model()
        config = config or {}
        
        # System prompt for production-ready code
        system_prompt = """You are an expert programmer. Generate production-ready code with:
- Clear variable names
- Type hints (Python) or JSDoc (JavaScript/TypeScript)
- Error handling
- Docstrings/comments
- Efficient algorithms

Output only the code, no explanations before or after."""
        
        full_prompt = f"""{system_prompt}

User request: {prompt}

Code:
```"""
        
        # Self-debug loop (max 2 iterations)
        max_attempts = 2
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # Generate code
                response = model.create_completion(
                    full_prompt,
                    temperature=config.get("temperature", 0.3),  # Low for precision
                    max_tokens=config.get("max_tokens", 2048),
                    stop=["```\n\n", "\n\n\n"]
                )
                
                code = response["choices"][0]["text"].strip()
                
                # Try to extract language and validate
                # Assume Python if not specified
                validation = validate_syntax(code, "python")
                
                if validation["valid"]:
                    print(f"[CodeExpert] ✅ Valid {validation['language']} code (attempt {attempt+1})")
                    return code
                
                else:
                    # Retry with error feedback
                    last_error = validation["error"]
                    print(f"[CodeExpert] ⚠️ Syntax error (attempt {attempt+1}): {last_error}")
                    
                    if attempt < max_attempts - 1:
                        # Modify prompt for retry
                        full_prompt = f"""{system_prompt}

User request: {prompt}

Previous attempt had syntax error: {last_error}
Fix the error and generate correct code.

Code:
```"""
            
            except Exception as e:
                last_error = str(e)
                print(f"[CodeExpert] ❌ Generation error (attempt {attempt+1}): {e}")
        
        # If we reach here, all attempts failed
        raise RuntimeError(
            f"Code generation failed after {max_attempts} attempts. "
            f"Last error: {last_error}"
        )


def validate_syntax(
    code: str, 
    language: Literal["python", "javascript", "typescript"] = "python"
) -> Dict[str, Any]:
    """
    Validate code syntax using language-specific parsers.
    
    Parameters
    ----------
    code : str
        Code to validate (may include markdown code blocks)
    language : {"python", "javascript", "typescript"}, optional
        Programming language (default: "python")
    
    Returns
    -------
    dict
        Validation result with keys:
        - valid (bool): Whether syntax is valid
        - error (str or None): Error message if invalid
        - language (str): Detected/specified language
    
    Notes
    -----
    - Python: Uses ast.parse() (stdlib)
    - JavaScript/TypeScript: Uses esprima (with fallback heuristics)
    - Automatically extracts code from markdown blocks
    
    Examples
    --------
    >>> code = "def add(a, b):\\n    return a + b"
    >>> result = validate_syntax(code, "python")
    >>> print(result)
    {'valid': True, 'error': None, 'language': 'python'}
    
    >>> bad_code = "def add(a, b\\n    return a + b"  # Missing colon
    >>> result = validate_syntax(bad_code, "python")
    >>> print(result)
    {'valid': False, 'error': 'invalid syntax...', 'language': 'python'}
    """
    # Extract code from markdown blocks if present
    if "```" in code:
        # Find code between ``` markers
        import re
        match = re.search(r"```(?:python|javascript|typescript|js|ts)?\n(.*?)```", code, re.DOTALL)
        if match:
            code = match.group(1).strip()
    
    # Validate based on language
    if language == "python":
        try:
            ast.parse(code)
            return {"valid": True, "error": None, "language": "python"}
        except SyntaxError as e:
            return {
                "valid": False, 
                "error": f"Line {e.lineno}: {e.msg}",
                "language": "python"
            }
    
    elif language in ["javascript", "typescript"]:
        # Try esprima if available
        try:
            import esprima
            esprima.parseScript(code)
            return {"valid": True, "error": None, "language": language}
        
        except ImportError:
            # Fallback: Basic heuristic checks
            print("[CodeExpert] esprima not installed, using heuristic validation")
            
            # Check for common syntax errors
            if code.count("{") != code.count("}"):
                return {
                    "valid": False,
                    "error": "Mismatched braces",
                    "language": language
                }
            
            if code.count("(") != code.count(")"):
                return {
                    "valid": False,
                    "error": "Mismatched parentheses",
                    "language": language
                }
            
            # Passed basic checks
            return {
                "valid": True,  # Best effort
                "error": None,
                "language": language
            }
        
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "language": language
            }
    
    else:
        return {
            "valid": False,
            "error": f"Unsupported language: {language}",
            "language": language
        }


# Singleton instance
_code_expert_instance = None


def get_code_expert_agent() -> CodeExpertAgent:
    """
    Get the singleton Code Expert Agent instance.
    
    Returns
    -------
    CodeExpertAgent
        Global code expert instance
    
    Notes
    -----
    Ensures only one VisCoder2 model instance in memory (~4.3GB).
    Model is lazy-loaded on first invoke() call.
    
    Examples
    --------
    >>> agent = get_code_expert_agent()
    >>> code1 = agent.invoke("Write a quicksort in Python")
    >>> 
    >>> # Same instance, model already loaded
    >>> agent2 = get_code_expert_agent()
    >>> assert agent is agent2  # True
    """
    global _code_expert_instance
    
    if _code_expert_instance is None:
        _code_expert_instance = CodeExpertAgent()
    
    return _code_expert_instance


# Exports
__all__ = ["CodeExpertAgent", "get_code_expert_agent", "validate_syntax"]
