from check_deep_sorting import rva_to_method_name, dump_func_details

print("=== Matching UxmlSerializedData / Bind / Drag / Row methods ===")
for rva, names in sorted(rva_to_method_name.items()):
    for n in names:
        if any(k in n for k in ["StreamedTable", "StreamedListView", "VirtualisedList", "UxmlSerializedData", "Bindings."]):
            if any(sub in n for sub in ["Deserialize", "Drag", "Bind", "Item", "Row", "Sort", "Order", "SetInternal", "Set"]):
                print(f"  0x{rva:08x}: {n}")

print("\n" + "="*80)
dump_func_details("Sub_014c3c20 (called by Bindings.SetInternal)", 0x014c3c20, 0x350)
