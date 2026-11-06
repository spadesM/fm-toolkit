import struct, sys
sys.stdout.reconfigure(encoding="utf-8")
from parse_st_data_exact import get_ref_bytes

# Let's trace from ContextMenuData (Field[4]) to the end of dbytes for Obj 229, 263, 111, 297, 360!
# Wait: let's see what is between Field[4] (ContextMenuData) and the end of dbytes:
# Field[4] ContextMenuData: AssetReference (m_AssetGUID: string, m_SubObjectName: string, m_SubObjectType: string)
#Wait: why were there 20 bytes of zeros between m_AssetGUID ("f45d...") and FactoryAsset ("399c...")?
# Wait: m_SubObjectName (4 bytes: 0), m_SubObjectType (4 bytes: 0) = 8 bytes!
# Why were there 12 MORE bytes of zeros before FactoryAsset?!
# Wait: is ContextMenuData 3 strings, or does AssetReference have more fields, OR is ContextMenuData Field[3]/Field[4]?
# Let's check what GUID "f45d19f7c2614ae4782f06ccd001fbb1" is!
# In Obj 229:
#   +0x210: "f93b92def36a8474fa5798233a6a3fb8" -> that's Field[0] InitFunction!
# Wait: what is between +0x210 (Field[0] InitFunction) and +0x33c ("f45d19f7...")?!
# In Obj 229 (+0x210..+0x33c):
#   +0x210: "f93b92def36a8474fa5798233a6a3fb8" (InitFunction of Base Class StreamedListView.UxmlSerializedData?! Or StreamedTable?!)
# WAIT A SECOND!
# Does StreamedListView.UxmlSerializedData ALSO have InitFunction?!
from check_deep_sorting import meta, fields_off, types_off, get_mstr

for ti in (5787, 5957):
    tu = struct.unpack_from("<22i", meta, types_off + ti * 88)
    f_start = tu[8]
    f_cnt = tu[17] & 0xFFFF
    print(f"\n=== Type[{ti}] {get_mstr(tu[0])} (fields={f_cnt}) ===")
    for i in range(f_cnt):
        fu = struct.unpack_from("<3i", meta, fields_off + (f_start + i) * 12)
        print(f"  Field[{i:2d}]: {get_mstr(fu[0])} (type_idx={fu[1]})")
