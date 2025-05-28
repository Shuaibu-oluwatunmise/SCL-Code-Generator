from Parser import parse_sequence
from UserInputSingle import get_user_input_single
from typing import List

def generate_scl_sequence(sequence, step_counter, counter_level=0, indent="    "):
    scl_lines = []
    counter_var = "RepeatCounter" if counter_level == 0 else f"SubCounter{counter_level}"
    for item in sequence:
        scl_lines.extend(generate_scl_step(item, step_counter, counter_level, indent))
    return scl_lines

def generate_scl_step(item, step_counter, counter_level, indent):
    scl = []
    item_type = item['type']
    step = step_counter['value']

    if item_type == 'delay':
        duration = item['duration']
        scl.append(f"{indent}{step}: Timer_{duration}s(IN:=TRUE, PT:=T#{duration}S);")
        scl.append(f"{indent}IF Timer_{duration}s.Q THEN Timer_{duration}s(IN:=FALSE); Step:={step+1}; END_IF;")
        step_counter['value'] += 1

    elif item_type == 'light':
        light = item['light']
        state = 'TRUE' if item['state'] == 'on' else 'FALSE'
        scl.append(f"{indent}{step}: {light}:={state}; Step:={step+1};")
        step_counter['value'] += 1

    elif item_type == 'action':
        for cyl in item['cylinders']:
            action = f"{cyl[:-1]}_Extend" if cyl.endswith('+') else f"{cyl[:-1]}_Retract"
            feedback = f"{cyl[:-1]}_Extended" if cyl.endswith('+') else f"{cyl[:-1]}_Retracted"
            scl.append(f"{indent}{step}: {action}:=TRUE; IF {feedback} THEN Step:={step+1}; END_IF;")
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
        scl.append(f"{indent}{step}: {' '.join(actions)}; IF {' AND '.join(feedbacks)} THEN Step:={step+1}; END_IF;")
        step_counter['value'] += 1

    elif item_type == 'repeat':
        count = item['count']
        nested_sequence = item['sequence']
        counter_var = f"SubCounter{counter_level+1}" if counter_level >= 0 else "RepeatCounter"
        case_step = step
        scl.append(f"{indent}{case_step}: CASE {counter_var} OF")
        for i in range(count * len(nested_sequence)):
            scl.append(f"{indent}    {i}:")
            nested_scl = generate_scl_sequence(nested_sequence, step_counter, counter_level+1, indent + "        ")
            scl.extend(nested_scl)
            scl.append(f"{indent}        {counter_var}:={counter_var}+1; Step:={case_step};")
        scl.append(f"{indent}    ELSE {counter_var}:=0; Step:={step+1}; END_CASE;")
        step_counter['value'] += 1

    elif item_type == 'sequence':
        for sub_item in item['steps']:
            scl.extend(generate_scl_step(sub_item, step_counter, counter_level, indent))

    if item.get('self_repeat', False):
        step = step_counter['value']
        scl.append(f"{indent}{step}: Step:=0;")
        step_counter['value'] += 1

    return scl

def generate_scl_program(parsed_sequence: List[dict]) -> str:
    scl_lines = [
        "VAR",
        "    Step : INT := 0;",
        "    Timer_1s : TON;",
        "    Timer_2s : TON;",
        "    RepeatCounter : INT := 0;",
        "    SubCounter1 : INT := 0;",
        "    SubCounter2 : INT := 0;",
        "    SubCounter3 : INT := 0;",
        "    L, M1, M2, M3 : BOOL;",
        "    A_Extend, A_Retract, B_Extend, B_Retract : BOOL;",
        "    A_Extended, A_Retracted, B_Extended, B_Retracted : BOOL;",
        "END_VAR\n",
        "IF StartSeq THEN",
        "    CASE Step OF"
    ]
    step_counter = {'value': 0}
    scl_lines += generate_scl_sequence(parsed_sequence, step_counter)
    scl_lines += [
        "    END_CASE;",
        "ELSE",
        "    Step:=0; RepeatCounter:=0; SubCounter1:=0; SubCounter2:=0; SubCounter3:=0;",
        "    Timer_1s(IN:=FALSE); Timer_2s(IN:=FALSE);",
        "    L:=FALSE; M1:=FALSE; M2:=FALSE; M3:=FALSE;",
        "    A_Extend:=FALSE; A_Retract:=FALSE; B_Extend:=FALSE; B_Retract:=FALSE;",
        "END_IF"
    ]
    return '\n'.join(scl_lines)

if __name__ == "__main__":
    user_config = get_user_input_single()
    parsed = parse_sequence(user_config['sequence'])
    scl_code = generate_scl_program(parsed)
    print("\nGenerated SCL Code (Single Sequence):\n")
    print(scl_code)