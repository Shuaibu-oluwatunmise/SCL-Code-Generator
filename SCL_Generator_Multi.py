from Parser import parse_sequence
from UserInputMulti import get_user_input_multi
from typing import List

def generate_scl_sequence(sequence, step_counter, counter_level=0, indent="    ", seq_number=1):
    scl_lines = []
    counter_var = f"SubCounter{seq_number}" if counter_level == 0 else f"SubCounter{counter_level}"
    step_var = f"Step{seq_number}"
    for item in sequence:
        scl_lines.extend(generate_scl_step(item, step_counter, counter_level, indent, seq_number))
    return scl_lines

def generate_scl_step(item, step_counter, counter_level, indent, seq_number):
    scl = []
    item_type = item['type']
    step = step_counter['value']
    step_var = f"Step{seq_number}"
    counter_var = f"SubCounter{seq_number}"

    if item_type == 'delay':
        duration = item['duration']
        scl.append(f"{indent}{step}: Timer_{duration}s{seq_number}(IN:=TRUE, PT:=T#{duration}S);")
        scl.append(f"{indent}IF Timer_{duration}s{seq_number}.Q THEN Timer_{duration}s{seq_number}(IN:=FALSE); {step_var}:={step+1}; END_IF;")
        step_counter['value'] += 1

    elif item_type == 'light':
        light = item['light']
        state = 'TRUE' if item['state'] == 'on' else 'FALSE'
        scl.append(f"{indent}{step}: {light}:={state}; {step_var}:={step+1};")
        step_counter['value'] += 1

    elif item_type == 'action':
        for cyl in item['cylinders']:
            action = f"{cyl[:-1]}_Extend" if cyl.endswith('+') else f"{cyl[:-1]}_Retract"
            feedback = f"{cyl[:-1]}_Extended" if cyl.endswith('+') else f"{cyl[:-1]}_Retracted"
            scl.append(f"{indent}{step}: {action}:=TRUE; IF {feedback} THEN {step_var}:={step+1}; END_IF;")
            step_counter['value'] += 1

    elif item_type == 'simultaneous':
        actions = []
        feedbacks = []
        for action in item['actions']:
            for cyl in action['cylinders']:
                cmd = f"{cyl[:-1]}_Extend" if cyl.endswith('+') else f"{cyl[:-1]}_Retract"
                fb = f"{cyl[:-1]}_Extended" if cyl.endswith('+') else f"{cyl[:-1]}_Retracted"
                actions.append(f"{cmd}:=TRUE")
                feedbacks.append(f"{fb}")
        scl.append(f"{indent}{step}: {' '.join(actions)}; IF {' AND '.join(feedbacks)} THEN {step_var}:={step+1}; END_IF;")
        step_counter['value'] += 1

    elif item_type == 'repeat':
        count = item['count']
        nested_sequence = item['sequence']
        case_step = step
        scl.append(f"{indent}{case_step}: CASE {counter_var} OF")
        for i in range(count * len(nested_sequence)):
            scl.append(f"{indent}    {i}:")
            nested_scl = generate_scl_sequence(nested_sequence, step_counter, counter_level+1, indent + "        ", seq_number)
            scl.extend(nested_scl)
            scl.append(f"{indent}        {counter_var}:={counter_var}+1; {step_var}:={case_step};")
        scl.append(f"{indent}    ELSE {counter_var}:=0; {step_var}:={step+1}; END_CASE;")
        step_counter['value'] += 1

    elif item_type == 'sequence':
        for sub_item in item['steps']:
            scl.extend(generate_scl_step(sub_item, step_counter, counter_level, indent, seq_number))

    if item.get('self_repeat', False):
        scl.append(f"{indent}{step}: {step_var}:=0;")
        step_counter['value'] += 1

    return scl

def generate_scl_program(config):
    scl_lines = [
        "VAR",
        "    Timer_1s : TON;",
        "    Timer_2s1 : TON;", "    Timer_2s2 : TON;", "    Timer_2s3 : TON;",
    ]
    for cyl in config['cylinders']:
        scl_lines.append(f"    {cyl['name']}_Extend, {cyl['name']}_Retract : BOOL;")
        scl_lines.append(f"    {cyl['name']}_Extended, {cyl['name']}_Retracted : BOOL;")
    for seq_number in range(1, len(config['sequences']) + 1):
        scl_lines.append(f"    Step{seq_number} : INT := 0;")
        scl_lines.append(f"    SubCounter{seq_number} : INT := 0;")
        scl_lines.append(f"    StartSeq{seq_number} : BOOL;")
    scl_lines.append("END_VAR\n")

    for idx, seq_input in enumerate(config['sequences']):
        seq_number = idx + 1
        parsed_sequence = parse_sequence(seq_input)
        scl_lines.append(f"IF StartSeq{seq_number} THEN")
        scl_lines.append(f"    CASE Step{seq_number} OF")
        step_counter = {'value': 0}
        scl_lines += generate_scl_sequence(parsed_sequence, step_counter, seq_number=seq_number)
        scl_lines.append("    END_CASE;")
        scl_lines.append("ELSE")
        scl_lines.append(f"    Step{seq_number}:=0; SubCounter{seq_number}:=0;")
        for cyl in config['cylinders']:
            scl_lines.append(f"    {cyl['name']}_Extend:=FALSE; {cyl['name']}_Retract:=FALSE;")
        scl_lines.append("END_IF\n")
    return "\n".join(scl_lines)

if __name__ == "__main__":
    config = get_user_input_multi()
    scl_code = generate_scl_program(config)
    print("\nGenerated SCL Code (Multiple Sequences):\n")
    print(scl_code)
