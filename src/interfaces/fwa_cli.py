def get_fwa_input(old_context):
    print("\n" + "="*40)
    print("      EDIT FWA RCA CONTEXT")
    print(" - Press Enter to KEEP current value")
    print(" - Type 'del' to CLEAR a value")
    print(" - Type new value to MODIFY")
    print("="*40)
    
    new_context = {}
    
    for key, current_val in old_context.items():
        # Format the label for display
        display_val = f"[{current_val}]" if current_val is not None else "[Empty]"
        user_in = input(f"{key.replace('_', ' ').title()} {display_val}: ").strip()
        
        if user_in == "":
            # Keep the old value
            new_context[key] = current_val
        elif user_in.lower() == "del":
            # Clear the value
            new_context[key] = None
        else:
            # Update with new value (handle numeric conversion)
            try:
                new_context[key] = float(user_in.replace(',', '.'))
            except ValueError:
                new_context[key] = user_in
                
    return new_context