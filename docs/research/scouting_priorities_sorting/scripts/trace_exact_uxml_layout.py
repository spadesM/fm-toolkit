import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from check_deep_sorting import (
    pe, meta, va_to_off, off_to_va, image_base,
    types_off, types_sz, fields_off, fields_sz, get_mstr
)

# Let's check what Deserialize (0x015f36b0) does for each of the 28 fields!
# Earlier we saw:
# flag_off=0x218 (Field[28] InitFunction_UxmlAttributeFlags) -> val_off=0x150 (Field[0] InitFunction) -> target_off=0x940
# flag_off=0x219 (Field[29] DragEvents_UxmlAttributeFlags)   -> val_off=0x158 (Field[1] DragEvents)   -> target_off=0xa00
# flag_off=0x21a (Field[30] SelectionEvents_UxmlAttributeFlags) -> val_off=0x160 (Field[2] SelectionEvents) -> target_off=0x9e8
# flag_off=0x21b (Field[31] RemoveEvents_UxmlAttributeFlags) -> val_off=0x168 (Field[3] RemoveEvents) -> target_off=0xa10
# flag_off=0x21c (Field[32] ContextMenuData_UxmlAttributeFlags) -> val_off=0x170 (Field[4] ContextMenuData) -> target_off=0x9a0
# flag_off=0x21d (Field[33] FactoryAsset_UxmlAttributeFlags) -> val_off=0x178 (Field[5] FactoryAsset) -> target_off=0x990
# flag_off=0x21e (Field[34] RowElementAsset_UxmlAttributeFlags) -> val_off=0x180 (Field[6] RowElementAsset) -> target_off=0x980
# flag_off=0x21f (Field[35] HeaderCellAsset_UxmlAttributeFlags) -> val_off=0x188 (Field[7] HeaderCellAsset) -> target_off=0x9c0
#WAIT A SECOND!
# Why did Obj 229 have:
#   +0x33c (rem+0x000): "f45d19f7c2614ae4782f06ccd001fbb1" (36 bytes) + 8 bytes (SubObjectName, SubObjectType) = 44 bytes (rem+0x000..0x02c)?
#Wait: what is at rem+0x02c..0x038 (12 bytes)?
# Wait: does ContextMenuData (or AssetReference) have 3 strings (12 bytes if empty)?
# IF Field[4] (ContextMenuData) is "f45d19f7..." (rem+0x000..0x02c), AND THEN rem+0x02c..0x038 (12 bytes) is AN EMPTY AssetReference (3 empty strings = 12 bytes!),
# THEN "399c0aa9357f67847b91ba2fe4756083" at rem+0x038..0x064 IS THE THIRD AssetReference (Field[6] RowElementAsset? No, why would FactoryAsset be at rem+0x038 if Field[4] is at rem+0x000?!)
# WAIT A MINUTE!
# Let's check how many bytes an AssetReference takes in VisualTreeAsset!
# Look at StreamedListView.UxmlSerializedData (Type[5787]):
# Field[0]: TruncateLabelTemplate (type_idx=5814)
# Field[1]: PaginationTemplate (type_idx=5814)
# Let's check the beginning of StreamedTable/UxmlSerializedData in Obj 229 (+0x000..+0x210)!
from parse_st_data_exact import get_ref_bytes
name, rid, dbytes = get_ref_bytes(229)
print(f"Obj 229 total len = {len(dbytes)} (0x{len(dbytes):x})")
