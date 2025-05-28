import re
from typing import List, Tuple

def tokenize(input_str: str) -> List[str]:
    pattern = r'\(|\)|\[|\]|,|\^|\d+S|[A-Z][1-9]*[\+\-]?|simultaneous|\d+'
    tokens = re.findall(pattern, input_str.replace(" ", ""))
    return tokens

def parse(tokens: List[str], is_top_level=False) -> Tuple[List[dict], bool]:
    steps = []
    while tokens:
        token = tokens.pop(0)
        if token in ['(', '[']:
            # Extract inner group
            group_tokens = []
            depth = 1
            while tokens and depth > 0:
                next_token = tokens.pop(0)
                if next_token in ['(', '[']:
                    depth += 1
                elif next_token in [')', ']']:
                    depth -= 1
                group_tokens.append(next_token)
            group_tokens.pop()  # Remove closing bracket

            if group_tokens and group_tokens[-1] == 'simultaneous':
                group_tokens.pop()
                actions = [{"cylinders": [t]} for t in group_tokens if re.match(r'[A-Z][1-9]*[\+\-]?', t)]
                steps.append({"type": "simultaneous", "actions": actions})
            else:
                # Inner sequences, no self_repeat
                inner_steps, _ = parse(group_tokens)
                steps.append({"type": "sequence", "steps": inner_steps, "self_repeat": False})
        elif token in [')', ']']:
            return steps, token == ')'
        elif token == '^':
            count = int(tokens.pop(0))
            last = steps.pop()
            steps.append({"type": "repeat", "count": count, "sequence": [last]})
        elif 'S' in token:
            steps.append({"type": "delay", "duration": int(token.replace('S',''))})
        elif re.match(r'[LM][1-9]*[\+\-]', token):
            steps.append({"type": "light", "light": token[:-1], "state": "on" if '+' in token else "off"})
        elif re.match(r'[A-Z][1-9]*[\+\-]?', token):
            steps.append({"type": "action", "cylinders": [token], "simultaneous": False})
        else:
            pass
    return steps, False

def parse_sequence(input_str: str) -> List[dict]:
    # Check if top-level self-repeat (starts with '(' and ends with ')')
    is_self_repeat = input_str.strip().startswith('(') and input_str.strip().endswith(')')
    tokens = tokenize(input_str.strip()[1:-1] if is_self_repeat else input_str)
    steps, _ = parse(tokens, is_top_level=True)
    return [{"type": "sequence", "steps": steps, "self_repeat": is_self_repeat}]

# Example usage
if __name__ == "__main__":
    input_sequence = "(2S, L+, M1+, (A+, B+, B-, A-)^2, M1-, 1S, M2+, (A+, (A-, B+), (A+, B-), A-)^2, M2-, 1S, M3+, ((A+, A-)^2, (B+, B-)^2)^2, M3-, L-)"

    parsed_sequence = parse_sequence(input_sequence)
    import pprint
    pprint.pprint(parsed_sequence)