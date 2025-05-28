def get_user_input_single():
    config = {}

    # Input single sequence
    seq_input = input("Enter the sequence (e.g., ((A+, B+), 2s, (A-, B-))^2): ")
    config['sequence'] = seq_input

    # Number of cylinders
    num_cylinders = int(input("Enter number of cylinders: "))
    config['cylinders'] = []
    for i in range(1, num_cylinders + 1):
        cylinder = {}
        cylinder_name = input(f"Enter name of cylinder {i} (e.g., A, B, C): ").strip().upper()
        cylinder_type = input(f"Enter type for cylinder {cylinder_name} (single-acting or double-acting): ").strip().lower()
        valve_type = input(f"Enter valve type for cylinder {cylinder_name} (e.g., 5/2 way pilot actuated, spring return, etc.): ").strip()
        cylinder['name'] = cylinder_name
        cylinder['type'] = cylinder_type
        cylinder['valve'] = valve_type
        config['cylinders'].append(cylinder)

    return config

if __name__ == "__main__":
    user_config = get_user_input_single()
    print("\nCollected Configuration (Single Sequence):")
    print(user_config)
